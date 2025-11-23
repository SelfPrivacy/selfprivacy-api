# SelfPrivacy GraphQL API which allows app to control your server

![CI status](https://ci.selfprivacy.org/api/badges/SelfPrivacy/selfprivacy-rest-api/status.svg)

## Build

```console
$ nix build
```

In case of successful build, you should get the `./result` symlink to a folder (in `/nix/store`) with build contents.

## Develop

```console
$ nix develop
[SP devshell:/dir/selfprivacy-rest-api]$ python
Python 3.10.13 (main, Aug 24 2023, 12:59:26) [GCC 12.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(ins)>>>
```

If you don't have experimental flakes enabled, you can use the following command:

```console
$ nix --extra-experimental-features nix-command --extra-experimental-features flakes develop
```

## Testing

Run the test suite by running coverage with pytest inside an ephemeral NixOS VM with redis service enabled:
```console
$ nix flake check -L
```

Run the same test suite, but additionally create `./result/coverage.xml` in the current directory:
```console
$ nix build .#checks.x86_64-linux.default -L
```

Alternatively, just print the path to `/nix/store/...coverage.xml` without creating any files in the current directory:
```console
$ nix build .#checks.x86_64-linux.default -L --print-out-paths --no-link
```

Run the same test suite with arbitrary pytest options:
```console
$ pytest-vm.sh # specify pytest options here, e.g. `--last-failed`
```
When running using the script, pytest cache is preserved between runs in `.pytest_cache` folder.
NixOS VM state temporary resides in `${TMPDIR:=/tmp}/nixos-vm-tmp-dir/vm-state-machine` during the test.
Git workdir directory is shared read-write with VM via `.nixos-vm-tmp-dir/shared-xchg` symlink. VM accesses workdir contents via `/tmp/shared` mount point and `/root/source` symlink.

Launch VM and execute commands manually either in Linux console (user `root`) or using python NixOS tests driver API (refer to [NixOS documentation](https://nixos.org/manual/nixos/stable/#ssec-machine-objects)):
```console
$ nix run .#checks.x86_64-linux.default.driverInteractive
```

You can add `--keep-vm-state` in order to keep VM state between runs:
```console
$ TMPDIR=".nixos-vm-tmp-dir" nix run .#checks.x86_64-linux.default.driverInteractive --keep-vm-state
```

Option `-L`/`--print-build-logs` is optional for all nix commands. It tells nix to print each log line one after another instead of overwriting a single one.

## Dependencies and Dependant Modules

This flake depends on a single Nix flake input - nixpkgs repository. nixpkgs repository is used for all software packages used to build, run API service, tests, etc.

In order to synchronize nixpkgs input with the same from selfprivacy-nixos-config repository, use this command:

```console
$ nix flake lock --override-input nixpkgs nixpkgs --inputs-from git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=BRANCH
```

Replace BRANCH with the branch name of selfprivacy-nixos-config repository you want to sync with. During development nixpkgs input update might be required in both selfprivacy-rest-api and selfprivacy-nixos-config repositories simultaneously. So, a new feature branch might be temporarily used until selfprivacy-nixos-config gets the feature branch merged.

Show current flake inputs (e.g. nixpkgs):
```console
$ nix flake metadata
```

Show selfprivacy-nixos-config Nix flake inputs (including nixpkgs):
```console
$ nix flake metadata git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=BRANCH
```

Nix code for NixOS service module for API is located in NixOS configuration repository.

## Troubleshooting

Sometimes commands inside `nix develop` refuse to work properly if the calling shell lacks `LANG` environment variable. Try to set it before entering `nix develop`.

## How to add translations

## Mark strings for translation

```
import gettext

_ = gettext.gettext

text = _("Service not found")

```

## Translate at runtime

```
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

print(t.translate(text=text, locale="au"))
```

## Extract strings into a .pot file

1. Add your files to gettext_extract.sh

2. Run gettext_extract.sh

## Create or update a language (.po .mo)

Create .po
```
msginit \
  --locale=ru_RU \
  --input=selfprivacy_api/locale/messages.pot \
  --output-file=selfprivacy_api/locale/ru/LC_MESSAGES/messages.po
```

Ensure UTF-8 encoding for the .po
```
iconv -f ISO-8859-5 -t UTF-8 \
  selfprivacy_api/locale/ru/LC_MESSAGES/messages.po \
  -o selfprivacy_api/locale/ru/LC_MESSAGES/messages.utf8.po && \
mv selfprivacy_api/locale/ru/LC_MESSAGES/messages.utf8.po selfprivacy_api/locale/ru/LC_MESSAGES/messages.po
```

Compile .mo
```
msgfmt -o selfprivacy_api/locale/ru/LC_MESSAGES/messages.mo selfprivacy_api/locale/ru/LC_MESSAGES/messages.po
```
