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

#Mailserver
sed -i '17s/.*/    fqdn = "'"$DOMAIN"'";/' mailserver.nix
sed -i '18s/.*/    domains = [ "'"$DOMAIN"'" ];/' mailserver.nix
sed -i '23s/.*/\t"'"$USER"'@'"$DOMAIN"'" = {/' mailserver.nix
sed -i "24s,.*,\t\    hashedPassword = \"$PASSWORD\";," mailserver.nix
sed -i '33s/.*/\t\t"'"$DOMAIN"'"/' mailserver.nix
sed -i '50s/.*/\t "admin@'"$DOMAIN"'" = "'"$USER"'@'"$DOMAIN"'";/' mailserver.nix
sed -i '72s/.*/    email = "'"$USER"'@'"$DOMAIN"'";/' mailserver.nix

# System Configuration
sed -i "16s,.*,\t\"$sshKey\"," configuration.nix

# OpenConnect

sed -i '25s/.*/server-cert = /etc/letsencrypt/live/$DOMAIN/cert.pem/' ocserv.nix
sed -i '26s/.*/server-key = /etc/letsencrypt/live/$DOMAIN/privkey.pem/' ocserv.nix
sed -i '28s/.*/default-domain = $DOMAIN/' ocserv.nix
sed -i '137s/.*/[vhost:$DOMAIN]/' ocserv.nix
sed -i '140s/.*/server-cert = /etc/letsencrypt/live/$DOMAIN/cert.pem/' ocserv.nix
sed -i '141s/.*/server-key = /etc/letsencrypt/live/$DOMAIN/privkey.pem/' ocserv.nix
sed -i '146s/.*/route = $machineip/255.255.255.255/' ocserv.nix

# ACME
sed -i '8s/.*/    email = "'"$USER"'@'"$DOMAIN"'";/' acme.nix
sed -i '9s/.*/    certs."'"$DOMAIN"'" = {/' acme.nix


#FIXME: Give access to system environment
#cp configuration.nix /etc/nixos/configuration.nix
#cp mailserver.nix /etc/nixos/mailserver/mailserver.nix
#cp restic.nix /etc/nixos/backup/restic.nix

/run/wrappers/bin/sudo ${config.system.build.nixos-rebuild}/bin/nixos-rebuild switch
    '';

    getDKIMScript = pkgs.writeScriptBin "getDKIMScript" ''
#!${pkgs.stdenv.shell}
    '';
    createUserScript = pkgs.writeScriptBin "createUserScript" ''
#!${pkgs.stdenv.shell}

${pkgs.shadow}/bin/useradd -m $1
    '';
    
    createBackupScript = pkgs.writeScriptBin "createBackupScript" ''
#!${pkgs.stdenv.shell}

${pkgs.restic}/bin/restic -r /srv/restic-repo backup ~/work
    '';

    restoreBackupScript = pkgs.writeScriptBin "restoreBackupScript" ''
#!${pkgs.stdenv.shell}

${pkgs.restic}/bin/restic -r $1 restore $2 --target $3
    '';

    webhook-server = self.callPackage ../packages/webhook-server.nix {};
  })];
  environment.etc."webhook_server.yml".text = ''
domain: "ilchub.net"
port: 8080
workers: 4
webhooks:
  -
    name: 'ls'
    command: '${pkgs.applyConfigScript}/bin/applyConfigScript'
    cwd: '/tmp'
  '';
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
          "value": "eemioqu5ohgu9eif6ahzo0shaiqu0caezaj0feel0quahp5u",
          "parameter":
	  {
            "source": "header",
	    "name": "X-Signature"
	  }
	}
      ]
    }
  },

  {
    "id": "getDKIM",
    "execute-command": "${pkgs.getDKIMScript}/bin/getDKIMScript",
    "command-working-directory": "/var/dkim",
    "pass-arguments-to-command":
    [
      {
        "source": "header",
	"name": "X-Domain"
      }
    ],
    "response-message": "Getting DKIM key",
    "response-headers":
    [
      {
        "name": "X-DKIM",
	"value": "${config.environment.variables.dkim}"
      }
    ]
  },

  {
    "id": "createUser",
    "execute-command": "${pkgs.createUserScript}/bin/createUserScript",
    "command-working-directory": "/tmp",
    "pass-arguments-to-command":
    [
      {
        "source": "header",
        "name": "X-User"
      }
    ]
  },

  {
    "id": "restoreBackup",
    "execute-command": "${pkgs.restoreBackupScript}/bin/restoreBackupScript",
    "command-working-directory": "/tmp"
  }
]
'';

  users.users.webhook = {
    isNormalUser = false;
    extraGroups = [ "wheel" ];
  };
  users.users.rswebhook = {
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
      restic
      shadow
    ];
    enable = true;
    serviceConfig = {
      User = "webhook";
      ExecStart = "${pkgs.webhook}/bin/webhook -hooks /etc/webhook.conf -verbose";
    };
  };

  systemd.services.webhook-server = {
    path = with pkgs; [
      man
      config.nix.package.out
      sudo
    ];
    enable = true;
    serviceConfig = {
      User = "rswebhook";
      ExecStart = "${pkgs.webhook-server}/bin/webhookserver";
    };
  };
}
