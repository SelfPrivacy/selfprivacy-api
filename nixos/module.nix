selfprivacy-graphql-api: { config, lib, pkgs, ... }:

let
  cfg = config.services.selfprivacy-api;
  config-id = "default";
  nixos-rebuild = "${config.system.build.nixos-rebuild}/bin/nixos-rebuild";
  nix = "${config.nix.package.out}/bin/nix";
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
        pkgs.restic
        pkgs.mkpasswd
        pkgs.util-linux
        pkgs.e2fsprogs
        pkgs.iproute2
        pkgs.memray
      ];
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      serviceConfig = {
        User = "root";
        ExecStart = "${pkgs.memray}/bin/memray run --trace-python-allocators --follow-fork ${selfprivacy-graphql-api}/bin/.app.py-wrapped";
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
          pkgs.python311Packages.makePythonPath [ selfprivacy-graphql-api ];
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
        ExecStart = "${pkgs.python311Packages.huey}/bin/huey_consumer.py selfprivacy_api.task_registry.huey";
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
      # TODO figure out how to get dependencies list reliably
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out ];
      # TODO set proper timeout for reboot instead of service restart
      serviceConfig = {
        User = "root";
        WorkingDirectory = "/etc/nixos";
        # sync top-level flake with sp-modules sub-flake
        # (https://github.com/NixOS/nix/issues/9339)
        ExecStartPre = ''
          ${nix} flake lock --override-input sp-modules path:./sp-modules
        '';
        ExecStart = ''
          ${nixos-rebuild} switch --flake .#${config-id}
        '';
        KillMode = "none";
        SendSIGKILL = "no";
      };
      restartIfChanged = false;
      unitConfig.X-StopOnRemoval = false;
    };
    # One shot systemd service to upgrade NixOS using nixos-rebuild
    systemd.services.sp-nixos-upgrade = {
      # protection against simultaneous runs
      after = [ "sp-nixos-rebuild.service" ];
      description = "Upgrade NixOS and SP modules to latest versions";
      environment = config.nix.envVars // {
        HOME = "/root";
      } // config.networking.proxy.envVars;
      # TODO figure out how to get dependencies list reliably
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out ];
      serviceConfig = {
        User = "root";
        WorkingDirectory = "/etc/nixos";
        # TODO get URL from systemd template parameter?
        ExecStartPre = ''
          ${nix} flake update \
          --override-input selfprivacy-nixos-config git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes
        '';
        ExecStart = ''
          ${nixos-rebuild} switch --flake .#${config-id}
        '';
        KillMode = "none";
        SendSIGKILL = "no";
      };
      restartIfChanged = false;
      unitConfig.X-StopOnRemoval = false;
    };
    # One shot systemd service to rollback NixOS using nixos-rebuild
    systemd.services.sp-nixos-rollback = {
      # protection against simultaneous runs
      after = [ "sp-nixos-rebuild.service" "sp-nixos-upgrade.service" ];
      description = "Rollback NixOS using nixos-rebuild";
      environment = config.nix.envVars // {
        HOME = "/root";
      } // config.networking.proxy.envVars;
      # TODO figure out how to get dependencies list reliably
      path = [ pkgs.coreutils pkgs.gnutar pkgs.xz.bin pkgs.gzip pkgs.gitMinimal config.nix.package.out ];
      serviceConfig = {
        User = "root";
        WorkingDirectory = "/etc/nixos";
        ExecStart = ''
          ${nixos-rebuild} switch --rollback --flake .#${config-id}
        '';
        KillMode = "none";
        SendSIGKILL = "no";
      };
      restartIfChanged = false;
      unitConfig.X-StopOnRemoval = false;
    };
  };
}
