{ pkgs, config, ... }:
{
  nixpkgs.overlays = [(self: super: {
    updateScript = pkgs.writeScriptBin "updateScript" ''
      #!${pkgs.stdenv.shell}

      /run/wrappers/bin/sudo ${config.system.build.nixos-rebuild}/bin/nixos-rebuild switch --upgrade
    '';

    rollbackScript = pkgs.writeScriptBin "rollbackScript" ''
      #!${pkgs.stdenv.shell}

      /run/wrappers/bin/sudo ${config.system.build.nixos-rebuild}/bin/nixos-rebuild switch --rollback
    '';

    applyConfigScript = pkgs.writeScriptBin "applyConfigScript" ''
      #!${pkgs.stdenv.shell}

      /run/wrappers/bin/sudo ${config.system.build.nixos-rebuild}/bin/nixos-rebuild switch
    '';

    setupConfigsScript = pkgs.writeScriptBin "setupConfigsScript" ''
      #!${pkgs.stdenv.shell}
      export DOMAIN=$1
      export USER=$2
      export PASSWORD=$3
      
      ${pkgs.wget}/bin/wget https://bitbucket.org/ilchub/serverdata/raw/b297b4026794c5420da97d7d06a393a5bf7e0819/configuration.nix
      ${pkgs.wget}/bin/wget https://bitbucket.org/ilchub/serverdata/raw/b297b4026794c5420da97d7d06a393a5bf7e0819/mailserver.nix
      ${pkgs.wget}/bin/wget https://bitbucket.org/ilchub/serverdata/raw/b297b4026794c5420da97d7d06a393a5bf7e0819/restic.nix

      sed -i '17s/.*/    fqdn = "'"$DOMAIN"'";/' mailserver.nix
      sed -i '18s/.*/    domains = [ "'"$DOMAIN"'" ];/' mailserver.nix
      sed -i '23s/.*/\t"'"$USER"'@'"$DOMAIN"'" = {/' mailserver.nix
      sed -i "24s,.*,\t\    hashedPassword = \"$PASSWORD\";," mailserver.nix
      sed -i '33s/.*/\t\t"'"$DOMAIN"'"/' mailserver.nix
      sed -i '50s/.*/\t "admin@'"$DOMAIN"'" = "'"$USER"'@'"$DOMAIN"'";/' mailserver.nix
      sed -i '72s/.*/    email = "'"$USER"'@'"$DOMAIN"'";/' mailserver.nix

      # System Configuration
      sed -i "16s,.*,\t\"$sshKey\"," configuration.nix

      # Restic
      #sed -i '14s/.*/\t\tEnvironment = [ "AWS_ACCESS_KEY_ID='"$AWS_TOKEN_ID"'" "AWS_SECRET_ACCESS_KEY='"$AWS_TOKEN"'" ];/' restic.nix
      #sed -i "17s,.*,\t restic -r s3:s3.amazonaws.com/$AWS_BUCKET_NAME backup /var/vmail /var/vmail ," restic.nix

      #FIXME: Give access to system environment
      #cp configuration.nix /etc/nixos/configuration.nix
      #cp mailserver.nix /etc/nixos/mailserver.nix
      #cp restic.nix /etc/nixos/restic.nix

      #rm configuration.nix
      #rm mailserver.nix
      #rm restic.nix

      /run/wrappers/bin/sudo ${config.system.build.nixos-rebuild}/bin/nixos-rebuild switch
    '';

   getDKIMScript = pkgs.writeScriptBin "getDKIMScript" ''
      #!${pkgs.stdenv.shell}

      export dkim=$( cat "$1".selector.txt )
    ''; 
  })];

  environment.etc."webhook.conf".text = ''
  [
    {
      "id": "update",
      "execute-command": "${pkgs.updateScript}/bin/updateScript",
      "command-working-directory": "/tmp",
      "response-message": "Updating system..."
    },

    {
      "id": "rollback",
      "execute-command": "${pkgs.rollbackScript}/bin/rollbackScript",
      "command-working-directory": "/tmp"
    },

    {
      "id": "apply",
      "execute-command": "${pkgs.applyConfigScript}/bin/applyConfigScript",
      "command-working-directory": "/tmp"
    },

    {
      "id": "setupConfigs",
      "execute-command": "${pkgs.setupConfigsScript}/bin/setupConfigsScript",
      "command-working-directory": "/tmp",
      "pass-arguments-to-command":
      [
        {
          "source": "header",
	  "name": "X-Domain"
        },
	{
          "source": "header",
	  "name": "X-User"
	},
	{
          "source": "header",
	  "name": "X-Password"
	}
      ],
      "trigger-rule":
      {
        "and":
	[
          "match":
	  {
            "type": "value",
	    "value": "blahblah",
	    "parameter":
	    {
              "source": "header",
	      "name": "X-Signature"
	    }
	  }
	]
      }
    }

    {
      "id": "getdkim",
      "execute-command": "${getDKIMScript}/bin/getDKIMScript",
      "command-working-directory": "/var/dkim",
      "pass-arguments-to-command":
      [
        {
          "source": "header",
	  "name": "X-Domain"
	}
      ],
      "response-headers":
      [
        {
          "name": "DKIM-Signature",
	  "value": "{{ getenv "dkim" }}"
	}
      ]
    }
  ]
  '';

  users.users.webhook = {
    isNormalUser = false;
    extraGroups = [ "wheel" ];
  };

  systemd.services.webhook = {
    path = with pkgs; [
      man
      config.nix.package.out
      sudo
      git
      wget
    ];
    enable = true;
    serviceConfig = {
      User = "webhook";
      ExecStart = "${pkgs.webhook}/bin/webhook -hooks /etc/webhook.conf -secure -cert /var/lib/acme/ilchub.net/fullchain.pem -key /var/lib/acme/ilchub.net/key.pem -verbose";
    };
  };
}
