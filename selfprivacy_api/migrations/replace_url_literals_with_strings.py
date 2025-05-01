from selfprivacy_api.migrations.migration import Migration

FLAKE_PATH = "/etc/nixos/flake.nix"


class ReplaceUrlLiteralsWithStrings(Migration):
    """Wrap path:./ and git+https:// literals in /etc/nixos to strings"""

    def get_migration_name(self) -> str:
        return "replace_url_literals_with_strings"

    def get_migration_description(self) -> str:
        return "Wraps path:./ and git+https:// literals in /etc/nixos to strings"

    def is_migration_needed(self) -> bool:
        # This code matches following in the flake.nix file:
        #
        # ...
        #  inputs.selfprivacy-nixos-config.url =
        #    -> |git+https|://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git;
        #
        #  -> inputs.sp-modules.url = |path:./sp-modules;|
        # ...
        with open(FLAKE_PATH) as flake:
            for line in file:
                if line.strip().startswith("git+https"):
                    return true
                if line.strip().endswith("path:./sp-modules;"):
                    return true
        return false

    def migrate(self) -> None:
        content = ""
        with open(FLAKE_PATH) as flake:
            for line in file:
                if line.strip().startswith("git+https"):
                    # git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git; ->
                    # ...."git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git";
                    url = line.strip()[:-1]  # Remove ;
                    content += f'    "{url}";\n'
                elif line.strip().endswith("path:./sp-modules;"):
                    content += '  inputs.sp-modules.url = "path:./sp-modules";\n'
                else:
                    content += line
                    content += "\n"

        # FlakeServiceManager will wrap all URLs with "" when called.

        with FlakeServiceManager() as _:
            pass
