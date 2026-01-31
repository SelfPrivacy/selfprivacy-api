{
  description = "SelfPrivacy API flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

  outputs =
    { self, nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      vmtest-src-dir = "/root/source";

      mkPythonEnv =
        system:
        self.packages.${system}.default.pythonModule.withPackages (
          ps:
          self.packages.${system}.default.propagatedBuildInputs
          ++ (
            with ps;
            [
              coverage
              pytest
              pytest-datadir
              pytest-mock
              pytest-subprocess
              pytest-asyncio
              black
              mypy
              pylsp-mypy
              python-lsp-black
              python-lsp-server
              pyflakes
              typer # for strawberry
              types-redis # for mypy
              aiofiles
            ]
            ++ strawberry-graphql.optional-dependencies.cli
          )
        );

      shellMOTD = ''
        Welcome to SP API development shell!

        [formatters]

          black
          nixpkgs-fmt

        [linters]

          bandit
            CI uses the following command:
            bandit -ll -r selfprivacy_api
          mypy
          pyflakes

        [testing in NixOS VM]

          nixos-test-driver - run an interactive NixOS VM with all dependencies included and 2 disk volumes
          pytest-vm         - run pytest in an ephemeral NixOS VM with Redis, accepting pytest arguments
      '';
    in
    {
      nixosModules.default = import ./nixos/module.nix self.packages;
      # see https://github.com/NixOS/nixpkgs/blob/66a9817cec77098cfdcbb9ad82dbb92651987a84/nixos/lib/test-driver/test_driver/machine.py#L359
      packages = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.callPackage ./default.nix {
            pythonPackages = pkgs.python312Packages;
            rev = self.shortRev or self.dirtyShortRev or "dirty";
          };
          pytest-vm = pkgs.writeShellScriptBin "pytest-vm" ''
            set -o errexit
            set -o nounset
            set -o xtrace

            # see https://github.com/NixOS/nixpkgs/blob/66a9817cec77098cfdcbb9ad82dbb92651987a84/nixos/lib/test-driver/test_driver/machine.py#L359
            export TMPDIR=''${TMPDIR:=/tmp}/nixos-vm-tmp-dir
            readonly NIXOS_VM_SHARED_DIR_HOST="$TMPDIR/shared-xchg"
            readonly NIXOS_VM_SHARED_DIR_GUEST="/tmp/shared"

            mkdir -p "$TMPDIR"
            ln -sfv "$PWD" -T "$NIXOS_VM_SHARED_DIR_HOST"

            SCRIPT=$(cat <<EOF
            start_all()
            machine.succeed("ln -sf $NIXOS_VM_SHARED_DIR_GUEST -T ${vmtest-src-dir} >&2")
            machine.succeed("cd ${vmtest-src-dir} && coverage run -m pytest $@ >&2")
            machine.succeed("cd ${vmtest-src-dir} && coverage report >&2")
            EOF
            )

            if [ -f "/etc/arch-release" ]; then
                ${
                  self.checks.${system}.default.driverInteractive
                }/bin/nixos-test-driver --no-interactive <(printf "%s" "$SCRIPT")
            else
                ${self.checks.${system}.default.driver}/bin/nixos-test-driver -- <(printf "%s" "$SCRIPT")
            fi
          '';
          dependencies-json = pkgs.writeTextFile {
            name = "dependencies-versions.json";
            text =
              let
                pkg = self.packages.${system}.default;
                # Extract package information from propagatedBuildInputs
                packageInfo = builtins.map (dep: {
                  name = dep.pname or (builtins.parseDrvName dep.name).name;
                  version = dep.version or (builtins.parseDrvName dep.name).version;
                  changelog = dep.meta.changelog or null;
                  homepage = dep.meta.homepage or null;
                }) pkg.propagatedBuildInputs;
              in
              builtins.toJSON {
                dependencies = packageInfo;
              };
          };
        }
      );
      devShells = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShellNoCC {
            name = "SP API dev shell";
            packages = with pkgs; [
              nixpkgs-fmt
              rclone
              valkey
              restic
              bandit
              self.packages.${system}.pytest-vm
              # FIXME consider loading this explicitly only after ArchLinux issue is solved
              self.checks.${system}.default.driverInteractive
              # the target API application python environment
              (mkPythonEnv system)
            ];
            shellHook = ''
              # envs set with export and as attributes are treated differently.
              # for example. printenv <Name> will not fetch the value of an attribute.
              export TEST_MODE="true"

              # more tips for bash-completion to work on non-NixOS:
              # https://discourse.nixos.org/t/whats-the-nix-way-of-bash-completion-for-packages/20209/16?u=alexoundos
              # Load installed profiles
              for file in "/etc/profile.d/"*.sh; do
                # If that folder doesn't exist, bash loves to return the whole glob
                [[ -f "$file" ]] && source "$file"
              done

              printf "%s" "${shellMOTD}"
            '';
          };
          ci-bandit = pkgs.mkShellNoCC {
            name = "SP API dev shell";
            packages = with pkgs; [
              bandit
              (mkPythonEnv system)
            ];
            shellHook = ''
              export TEST_MODE="true"
            '';
          };
          ci-black = pkgs.mkShellNoCC {
            name = "SP API dev shell";
            packages = with pkgs; [
              black
              (mkPythonEnv system)
            ];
            shellHook = ''
              export TEST_MODE="true"
            '';
          };
          ci-sonar = pkgs.mkShellNoCC {
            name = "SP API sonar shell";
            packages = with pkgs; [
              sonar-scanner-cli
            ];
          };
        }
      );

      checks = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          fmt-check = pkgs.runCommandLocal "sp-api-fmt-check"
            {
              nativeBuildInputs = [ pkgs.black ];
            } "black --check ${self.outPath} > $out";
          default = pkgs.testers.runNixOSTest {
            name = "default";
            nodes.machine =
              { lib, pkgs, ... }:
              {
                # 2 additional disks (1024 MiB and 200 MiB) with empty ext4 FS
                virtualisation.emptyDiskImages = [
                  1024
                  200
                ];
                virtualisation.fileSystems."/volumes/vdb" = {
                  autoFormat = true;
                  device = "/dev/vdb"; # this name is chosen by QEMU, not here
                  fsType = "ext4";
                  noCheck = true;
                };
                virtualisation.fileSystems."/volumes/vdc" = {
                  autoFormat = true;
                  device = "/dev/vdc"; # this name is chosen by QEMU, not here
                  fsType = "ext4";
                  noCheck = true;
                };
                boot.consoleLogLevel = lib.mkForce 3;
                documentation.enable = false;
                services.journald.extraConfig = lib.mkForce "";
                services.redis.package = pkgs.valkey;
                services.redis.servers.sp-api = {
                  enable = true;
                  save = [ ];
                  settings.notify-keyspace-events = "KEA";
                };
                environment.systemPackages = with pkgs; [
                  (mkPythonEnv system)
                  # TODO: these can be passed via wrapper script around app
                  rclone
                  restic
                ];
                environment.variables.TEST_MODE = "true";
                systemd.tmpfiles.settings.src.${vmtest-src-dir}.L.argument = self.outPath;
              };
            testScript = ''
              start_all()
              machine.succeed("cd ${vmtest-src-dir} && coverage run --data-file=/tmp/.coverage -m pytest -p no:cacheprovider -v >&2")
              machine.succeed("cd ${vmtest-src-dir} && coverage xml --rcfile=${vmtest-src-dir}/.coveragerc --data-file=/tmp/.coverage -o /tmp/coverage.xml >&2")
              machine.copy_from_vm("/tmp/coverage.xml", "coverage.xml")
              machine.succeed("cd ${vmtest-src-dir} && coverage report --data-file=/tmp/.coverage >&2")
            '';
          };
        }
      );
    };
  nixConfig.bash-prompt = ''\n\[\e[1;32m\][\[\e[0m\]\[\e[1;34m\]SP devshell\[\e[0m\]\[\e[1;32m\]:\w]\$\[\[\e[0m\] '';
}
