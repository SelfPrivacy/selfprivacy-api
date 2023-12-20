selfprivacy-graphql-api: { config, lib, pkgs, ... }:

let
  cfg = config.services.selfprivacy-api;
in
{
  options.services.selfprivacy-api = {
    enable = lib.mkOption {
      default = true;
      type = lib.types.bool;
      description = ''
        Enable SelfPrivacy API service
      '';
    };
  };
  config = lib.mkIf cfg.enable {
    users.users."selfprivacy-api" = {
      isNormalUser = false;
      isSystemUser = true;
      extraGroups = [ "opendkim" ];
      group = "selfprivacy-api";
    };
    users.groups."selfprivacy-api".members = [ "selfprivacy-api" ];

    systemd.services.selfprivacy-api = {
      description = "API Server used to control system from the mobile application";
      environment = config.nix.envVars // {
        HOME = "/root";
        PYTHONUNBUFFERED = "1";
      } // config.networking.proxy.envVars;
      path = [
        "/var/"
        "/var/dkim/"
        pkgs.coreutils
        pkgs.gnutar
        pkgs.xz.bin
        pkgs.gzip
        pkgs.gitMinimal
        config.nix.package.out
        pkgs.nixos-rebuild
        pkgs.restic
        pkgs.mkpasswd
        pkgs.util-linux
        pkgs.e2fsprogs
        pkgs.iproute2
      ];
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      serviceConfig = {
        User = "root";
        ExecStart = "${selfprivacy-graphql-api}/bin/app.py";
        Restart = "always";
        RestartSec = "5";
      };
    };
    systemd.services.selfprivacy-api-worker = {
      description = "Task worker for SelfPrivacy API";
      environment = config.nix.envVars // {
        HOME = "/root";
        PYTHONUNBUFFERED = "1";
        PYTHONPATH =
          pkgs.python310Packages.makePythonPath [ selfprivacy-graphql-api ];
      } // config.networking.proxy.envVars;
      path = [
        "/var/"
        "/var/dkim/"
        pkgs.coreutils
        pkgs.gnutar
        pkgs.xz.bin
        pkgs.gzip
        pkgs.gitMinimal
        config.nix.package.out
        pkgs.nixos-rebuild
        pkgs.restic
        pkgs.mkpasswd
        pkgs.util-linux
        pkgs.e2fsprogs
        pkgs.iproute2
      ];
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      serviceConfig = {
        User = "root";
        ExecStart = "${pkgs.python310Packages.huey}/bin/huey_consumer.py selfprivacy_api.task_registry.huey";
        Restart = "always";
        RestartSec = "5";
      };
    };
    # One shot systemd service to rebuild NixOS using nixos-rebuild
    systemd.services.sp-nixos-rebuild = {
      description = "nixos-rebuild switch";
      environment = config.nix.envVars // {
        HOME = "/root";
      } // config.networking.proxy.envVars;
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out pkgs.nixos-rebuild ];
      # TODO set proper timeout for reboot instead of service restart
      serviceConfig = {
        Type = "oneshot";
        User = "root";
        KillMode = "none";
        SendSIGKILL = "no";
      };
      script = ''
        # relock sp-modules to absolute path (in terms of Nix) due to Nix bugs:
        # https://github.com/NixOS/nix/issues/9339
        ${config.nix.package}/bin/nix flake lock /etc/nixos --override-input sp-modules /etc/nixos/sp-modules

        ${pkgs.nixos-rebuild}/bin/nixos-rebuild switch --flake /etc/nixos#sp-nixos
      '';
    };
    # One shot systemd service to upgrade NixOS using nixos-rebuild
    systemd.services.sp-nixos-upgrade = {
      # protection against simultaneous runs
      after = [ "sp-nixos-rebuild.service" ];
      description = "Upgrade NixOS and SP modules to latest versions";
      environment = config.nix.envVars // {
        HOME = "/root";
      } // config.networking.proxy.envVars;
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out pkgs.nixos-rebuild ];
      serviceConfig = {
        Type = "oneshot";
        User = "root";
        KillMode = "none";
        SendSIGKILL = "no";
      };
      script = ''
        # FIXME get URL from systemd parameter
        ${config.nix.package}/bin/nix flake update /etc/nixos/sp-modules/
        ${config.nix.package}/bin/nix flake update /etc/nixos --override-input selfprivacy-nixos-config git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes
        ${pkgs.nixos-rebuild}/bin/nixos-rebuild switch --flake /etc/nixos#sp-nixos
      '';
    };
    # One shot systemd service to rollback NixOS using nixos-rebuild
    systemd.services.sp-nixos-rollback = {
      # protection against simultaneous runs
      after = [ "sp-nixos-rebuild.service" "sp-nixos-upgrade.service" ];
      description = "Rollback NixOS using nixos-rebuild";
      environment = config.nix.envVars // {
        HOME = "/root";
      } // config.networking.proxy.envVars;
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out pkgs.nixos-rebuild ];
      serviceConfig = {
        Type = "oneshot";
        User = "root";
        ExecStart = "${pkgs.nixos-rebuild}/bin/nixos-rebuild switch --rollback --flake /etc/nixos#sp-nixos";
        KillMode = "none";
        SendSIGKILL = "no";
      };
    };
  };
}
