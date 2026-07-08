{
  description = "SelfPrivacy API flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs =
    { self, nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      vmtest-src-dir = "/root/source";

      apiVersion = builtins.head (
        builtins.match ''.*version="([^"]+)".*'' (builtins.readFile ./setup.py)
      );

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
          src-with-mo = pkgs.runCommand "sp-api-src-with-mo" { nativeBuildInputs = [ pkgs.gettext ]; } ''
            cp -r ${self} $out
            chmod -R +w $out
            shopt -s nullglob
            for po in $out/selfprivacy_api/locale/*/LC_MESSAGES/messages.po; do
              msgfmt -o "''${po%.po}.mo" "$po"
            done
          '';
          pam-email-selfprivacy = pkgs.callPackage ./extra/pam_email_selfprivacy { };
          pytest-vm =
            let
              check = self.checks.${system}.default.extend {
                modules = [
                  ({ config, lib, ... }: {
                    nodes.machine = {
                      virtualisation.sharedDirectories.src = {
                        source = "$API_SOURCES";
                        target = vmtest-src-dir;
                      };
                      virtualisation.fileSystems.${vmtest-src-dir} = lib.mkForce {
                        neededForBoot = true;
                        device = "src";
                        fsType = "9p";
                        options = [
                          "trans=virtio"
                          "version=9p2000.L"
                          "msize=${toString config.nodes.machine.virtualisation.msize}"
                          "x-systemd.requires=modprobe@9pnet_virtio.service"
                        ];
                      };
                    };
                  })
                ];
              };
            in
            pkgs.writeShellScriptBin "pytest-vm" ''
              set -o errexit
              set -o nounset
              set -o xtrace

              shopt -s nullglob
              for po in selfprivacy_api/locale/*/LC_MESSAGES/messages.po; do
                ${pkgs.gettext}/bin/msgfmt -o "''${po%.po}.mo" "$po"
              done

              # see https://github.com/NixOS/nixpkgs/blob/66a9817cec77098cfdcbb9ad82dbb92651987a84/nixos/lib/test-driver/test_driver/machine.py#L359
              export TMPDIR=''${TMPDIR:=/tmp}/nixos-vm-tmp-dir
              export API_SOURCES=$PWD

              SCRIPT=$(cat <<EOF
              start_all()
              machine.succeed("cd ${vmtest-src-dir} && coverage run -m pytest $@ >&2")
              machine.succeed("cd ${vmtest-src-dir} && coverage report >&2")
              EOF
              )

              if [ -f "/etc/arch-release" ]; then
                  ${check.driverInteractive}/bin/nixos-test-driver --no-interactive <(printf "%s" "$SCRIPT")
              else
                  ${check.driver}/bin/nixos-test-driver -- <(printf "%s" "$SCRIPT")
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
          gettext-extract = pkgs.writeShellApplication {
            name = "gettext-extract";
            runtimeInputs = with pkgs; [
              gettext
              findutils
              coreutils
              gnused
            ];
            text = ''
              POT_FILE="selfprivacy_api/locale/messages.pot"

              if [[ ! -d selfprivacy_api ]]; then
                echo "gettext-extract: run this from the repo root" >&2
                exit 1
              fi

              files_list="$(mktemp)"
              trap 'rm -f "$files_list"' EXIT

              find selfprivacy_api -type f -name '*.py' | LC_ALL=C sort > "$files_list"

              xgettext \
                --from-code=UTF-8 \
                --language=Python \
                -k_ \
                -kngettext:1,2 \
                --package-name="SelfPrivacy API" \
                --package-version="${apiVersion}" \
                --copyright-holder="SelfPrivacy" \
                --msgid-bugs-address="https://git.selfprivacy.org/SelfPrivacy/selfprivacy-rest-api/issues" \
                --foreign-user \
                --sort-by-file \
                --no-wrap \
                --files-from="$files_list" \
                -o "$POT_FILE"

              # Normalize POT-Creation-Date so re-runs are byte-identical
              # (load-bearing for the diff-based CI check).
              sed -i -e 's|^"POT-Creation-Date:[^"]*|"POT-Creation-Date: 1970-01-01 00:00+0000\\n|' "$POT_FILE"

              shopt -s nullglob
              for po in selfprivacy_api/locale/*/LC_MESSAGES/messages.po; do
                msgmerge --update --backup=none --no-wrap "$po" "$POT_FILE"
                msgfmt -c --check-format -o /dev/null "$po"
              done
            '';
          };
        }
      );

      apps = nixpkgs.lib.genAttrs systems (system: {
        gettext-extract = {
          type = "app";
          program = "${self.packages.${system}.gettext-extract}/bin/gettext-extract";
        };
      });
      devShells = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            name = "SP API dev shell";
            LLVM_COV = "${pkgs.llvmPackages.llvm}/bin/llvm-cov";
            LLVM_PROFDATA = "${pkgs.llvmPackages.llvm}/bin/llvm-profdata";
            packages = with pkgs; [
              rustc
              rustfmt
              cargo
              clippy
              cargo-llvm-cov
              llvmPackages.llvm
              pam
              gettext # msginit, msgfmt
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
          ci-rust = pkgs.mkShell {
            name = "SP API Rust CI shell";
            LLVM_COV = "${pkgs.llvmPackages.llvm}/bin/llvm-cov";
            LLVM_PROFDATA = "${pkgs.llvmPackages.llvm}/bin/llvm-profdata";
            packages = with pkgs; [
              rustc
              cargo
              clippy
              cargo-llvm-cov
              llvmPackages.llvm
              pam
            ];
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
          fmt-check = pkgs.runCommandLocal "sp-api-fmt-check" {
            nativeBuildInputs = [ pkgs.black ];
          } "black --check ${self.outPath} > $out";
          i18n-integrity =
            pkgs.runCommand "sp-api-i18n-integrity"
              {
                nativeBuildInputs = [
                  self.packages.${system}.gettext-extract
                  pkgs.diffutils
                  pkgs.coreutils
                ];
              }
              ''
                set -euo pipefail

                src=${self}
                cp -r "$src" work
                chmod -R +w work
                cd work
                gettext-extract

                fail=0

                if ! diff -u "$src/selfprivacy_api/locale/messages.pot" selfprivacy_api/locale/messages.pot; then
                  fail=1
                fi

                shopt -s nullglob
                for po in "$src"/selfprivacy_api/locale/*/LC_MESSAGES/messages.po; do
                  rel="''${po#$src/}"
                  if ! diff -u "$po" "$rel"; then
                    fail=1
                  fi
                done

                if [ $fail -ne 0 ]; then
                  echo "" >&2
                  echo "ERROR: i18n files are stale." >&2
                  echo "Run 'nix run .#gettext-extract' and commit the result." >&2
                  exit 1
                fi

                touch $out
              '';
          pam-email-selfprivacy-vm-integration =
            self.packages.${system}.pam-email-selfprivacy.tests.vm-integration;
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
                virtualisation.fileSystems.${vmtest-src-dir} = {
                  neededForBoot = true;
                  device = "${self.packages.${system}.src-with-mo}";
                  options = [
                    "bind"
                  ];
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
