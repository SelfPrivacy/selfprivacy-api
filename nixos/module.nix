selfprivacy-graphql-api:
{ config
, lib
, pkgs
, ...
}:

let
  cfg = config.services.selfprivacy-api;
  config-id = "default";
  nixos-rebuild = "${config.system.build.nixos-rebuild}/bin/nixos-rebuild";
  nix = "${config.nix.package.out}/bin/nix";
  sp-fetch-remote-module = pkgs.writeShellApplication {
    name = "sp-fetch-remote-module";
    runtimeInputs = [ config.nix.package.out ];
    text = ''
      if [ "$#" -ne 1 ]; then
        echo "Usage: $0 <URL>"
        exit 1
      fi

      URL="$1"
      nix eval --file /etc/sp-fetch-remote-module.nix --raw --apply "f: f { flakeURL = \"$URL\"; }"
    '';
  };

  sp = config.selfprivacy;
  domain = sp.domain;
  unix-user = "selfprivacy-api";
  port = "5050";

  oauth-client-id = "selfprivacy-api";
  oauth-redirect-uri = "https://api.${domain}/login/callback";

  dovecot-auth-script = pkgs.writeShellApplication {
    name = "dovecot-auth-script.sh";
    runtimeInputs = with pkgs; [
      coreutils-full
      gnugrep
      curl
      jq
    ];
    text = ''
      CHECKPASSWORD_REPLY_BINARY="$1"

      IFS= read -r -d ''' username <&3
      IFS= read -r -d ''' password <&3

      if ! response=$(curl -s -X POST http://127.0.0.1:${port}/internal/check-email-password \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$username\", \"password\": \"$password\"}"); then
        exit 111
      fi

      isValid=$(echo "$response" | jq -r '.isValid')

      if [ "$isValid" = "true" ]; then
        exec "$CHECKPASSWORD_REPLY_BINARY"
      else
        exit 1
      fi
    '';
  };

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
    opentelemetry = {
      enable = lib.mkOption {
        default = false;
        type = lib.types.bool;
        description = ''
          Enable OpenTelemetry instrumentation for SelfPrivacy services
        '';
      };
      endpoint = lib.mkOption {
        type = lib.types.str;
        default = "http://localhost:4317";
        description = ''
          OTLP gRPC endpoint URL
        '';
      };
      serviceName = lib.mkOption {
        type = lib.types.str;
        default = "selfprivacy-api";
        description = ''
          Service name for telemetry traces
        '';
      };
      serviceVersion = lib.mkOption {
        type = lib.types.str;
        default = "3.6.2";
        description = ''
          Service version for telemetry traces
        '';
      };
      headers = lib.mkOption {
        type = lib.types.str;
        default = "";
        example = "key1=value1,key2=value2";
        description = ''
          Additional headers to send with OTLP requests
        '';
      };
      sampleRate = lib.mkOption {
        type = lib.types.float;
        default = 1.0;
        description = ''
          Sampling rate for traces (0.0 to 1.0)
        '';
      };
    };
  };
  config = lib.mkIf cfg.enable {
    users = {
      users."selfprivacy-api" = {
        isNormalUser = false;
        isSystemUser = true;
        extraGroups = [ "opendkim" ];
        group = "selfprivacy-api";
      };
      groups = {
        "selfprivacy-api".members = [ unix-user ];
        keys.members = [ unix-user ];
        redis-sp-api.members = [ unix-user ];
      };
    };

    systemd = {
      services = {
        selfprivacy-api = {
          description = "API Server used to control system from the mobile application";
          environment =
            config.nix.envVars
            // {
              HOME = "/root";
              PYTHONUNBUFFERED = "1";
              KANIDM_ADMIN_TOKEN_FILE =
                sp.passthru.auth.mkServiceAccountTokenFP unix-user;
            }
            // config.networking.proxy.envVars
            // (lib.optionalAttrs cfg.opentelemetry.enable
              {
                OTEL_EXPORTER_OTLP_ENDPOINT = cfg.opentelemetry.endpoint;
                OTEL_EXPORTER_OTLP_PROTOCOL = "grpc";
                OTEL_EXPORTER_OTLP_HEADERS = cfg.opentelemetry.headers;
                OTEL_SERVICE_NAME = cfg.opentelemetry.serviceName;
                OTEL_SERVICE_VERSION = cfg.opentelemetry.serviceVersion;
                OTEL_TRACES_SAMPLER = "traceidratio";
                OTEL_TRACES_SAMPLER_ARG = toString cfg.opentelemetry.sampleRate;
                OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED = "true";
                OTEL_PYTHON_LOG_CORRELATION = "true";
              }
            );
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
            pkgs.rclone
            pkgs.mkpasswd
            pkgs.util-linux
            pkgs.e2fsprogs
            pkgs.iproute2
            pkgs.postgresql_16.out
            sp-fetch-remote-module
            config.services.kanidm.package
          ];
          after = [ "network-online.target" ];
          wants = [ "network-online.target" ];
          wantedBy = [ "multi-user.target" ];
          serviceConfig = {
            # Do not forget to edit Postgres identMap if you change the user!
            User = "root";
            ExecStart = "${selfprivacy-graphql-api}/bin/app.py";
            Restart = "always";
            RestartSec = "5";
            Slice = "selfprivacy_api.slice";
          };
        };
        selfprivacy-api-worker = {
          description = "Task worker for SelfPrivacy API";
          environment =
            config.nix.envVars
            // {
              HOME = "/root";
              PYTHONUNBUFFERED = "1";
              PYTHONPATH = pkgs.python312Packages.makePythonPath [ selfprivacy-graphql-api ];
            }
            // config.networking.proxy.envVars
            // (lib.optionalAttrs cfg.opentelemetry.enable
              {
                OTEL_EXPORTER_OTLP_ENDPOINT = cfg.opentelemetry.endpoint;
                OTEL_EXPORTER_OTLP_PROTOCOL = "grpc";
                OTEL_EXPORTER_OTLP_HEADERS = cfg.opentelemetry.headers;
                OTEL_SERVICE_NAME = "${cfg.opentelemetry.serviceName}-worker";
                OTEL_SERVICE_VERSION = cfg.opentelemetry.serviceVersion;
                OTEL_TRACES_SAMPLER = "traceidratio";
                OTEL_TRACES_SAMPLER_ARG = toString cfg.opentelemetry.sampleRate;
                OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED = "true";
                OTEL_PYTHON_LOG_CORRELATION = "true";
              }
            );
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
            pkgs.rclone
            pkgs.mkpasswd
            pkgs.util-linux
            pkgs.e2fsprogs
            pkgs.iproute2
            pkgs.postgresql_16.out
            sp-fetch-remote-module
            config.services.kanidm.package
          ];
          after = [ "network-online.target" ];
          wants = [ "network-online.target" ];
          wantedBy = [ "multi-user.target" ];
          serviceConfig = {
            # Do not forget to edit Postgres identMap if you change the user!
            User = "root";
            ExecStart = "${pkgs.python312Packages.huey}/bin/huey_consumer.py selfprivacy_api.task_registry.huey";
            Restart = "always";
            RestartSec = "5";
            Slice = "selfprivacy_api.slice";
          };
        };
        sp-nixos-rebuild = {
          description = "nixos-rebuild switch";
          environment =
            config.nix.envVars
            // {
              HOME = "/root";
            }
            // config.networking.proxy.envVars;
          # TODO figure out how to get dependencies list reliably
          path = [
            pkgs.coreutils
            pkgs.gnutar
            pkgs.xz.bin
            pkgs.gzip
            pkgs.gitMinimal
            config.nix.package.out
          ];
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
            KillMode = "mixed";
            SendSIGKILL = "no";
            StandardOutput = "journal";
            StandardError = "journal";
          };
          restartIfChanged = false;
          unitConfig.X-StopOnRemoval = false;
        };
        sp-nixos-upgrade = {
          # protection against simultaneous runs
          after = [ "sp-nixos-rebuild.service" ];
          description = "Upgrade NixOS and SP modules to latest versions";
          environment =
            config.nix.envVars
            // {
              HOME = "/root";
            }
            // config.networking.proxy.envVars;
          # TODO figure out how to get dependencies list reliably
          path = [
            pkgs.coreutils
            pkgs.gnutar
            pkgs.xz.bin
            pkgs.gzip
            pkgs.gitMinimal
            config.nix.package.out
          ];
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
            KillMode = "mixed";
            SendSIGKILL = "no";
            StandardOutput = "journal";
            StandardError = "journal";
          };
          restartIfChanged = false;
          unitConfig.X-StopOnRemoval = false;
        };
        sp-nixos-rollback = {
          # protection against simultaneous runs
          after = [
            "sp-nixos-rebuild.service"
            "sp-nixos-upgrade.service"
          ];
          description = "Rollback NixOS using nixos-rebuild";
          environment =
            config.nix.envVars
            // {
              HOME = "/root";
            }
            // config.networking.proxy.envVars;
          # TODO figure out how to get dependencies list reliably
          path = [
            pkgs.coreutils
            pkgs.gnutar
            pkgs.xz.bin
            pkgs.gzip
            pkgs.gitMinimal
            config.nix.package.out
          ];
          serviceConfig = {
            User = "root";
            WorkingDirectory = "/etc/nixos";
            ExecStart = ''
              ${nixos-rebuild} switch --rollback --flake .#${config-id}
            '';
            KillMode = "mixed";
            SendSIGKILL = "no";
            StandardOutput = "journal";
            StandardError = "journal";
          };
          restartIfChanged = false;
          unitConfig.X-StopOnRemoval = false;
        };
      };
      slices = {
        "selfprivacy_api" = {
          name = "selfprivacy_api.slice";
          description = "Slice for SelfPrivacy API services";
        };
      };
    };

    services.dovecot2.extraConfig = lib.mkAfter ''
      passdb {
        driver = checkpassword
        mechanisms = plain login
        args = ${dovecot-auth-script}/bin/dovecot-auth-script.sh
      }
    '';

    selfprivacy.auth.clients."${oauth-client-id}" = {
      displayName = "SelfPrivacy Self-Service Portal";
      subdomain = cfg.subdomain;
      isTokenNeeded = true;
      originLanding = "https://api.${domain}/";
      originUrl = oauth-redirect-uri;
      clientSystemdUnits = [ "${oauth-client-id}.service" ];
      enablePkce = true;
      linuxUserOfClient = unix-user;
      linuxGroupOfClient = unix-user;
      scopeMaps."idm_all_persons" = [
        "email"
        "groups"
        "openid"
        "profile"
      ];
    };

  };
}
