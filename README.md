# SelfPrivacy GraphQL API which allows app to control your server

## build

```console
$ nix build
```

As a result, you should get the `./result` symlink to a folder (in `/nix/store`) with build contents.

## develop & test

```console
$ nix develop
$ [SP devshell] pytest .
=================================== test session starts =====================================
platform linux -- Python 3.10.11, pytest-7.1.3, pluggy-1.0.0
rootdir: /data/selfprivacy/selfprivacy-rest-api
plugins: anyio-3.5.0, datadir-1.4.1, mock-3.8.2
collected 692 items

tests/test_block_device_utils.py .................                                    [  2%]
tests/test_common.py .....                                                            [  3%]
tests/test_jobs.py ........                                                           [  4%]
tests/test_model_storage.py ..                                                        [  4%]
tests/test_models.py ..                                                               [  4%]
tests/test_network_utils.py ......                                                    [  5%]
tests/test_services.py ......                                                         [  6%]
tests/test_graphql/test_api.py .                                                      [  6%]
tests/test_graphql/test_api_backup.py ...............                                 [  8%]
tests/test_graphql/test_api_devices.py .................                              [ 11%]
tests/test_graphql/test_api_recovery.py .........                                     [ 12%]
tests/test_graphql/test_api_version.py ..                                             [ 13%]
tests/test_graphql/test_backup.py ...............................                     [ 21%]
tests/test_graphql/test_localsecret.py ...                                            [ 22%]
tests/test_graphql/test_ssh.py ............                                           [ 23%]
tests/test_graphql/test_system.py .............................                       [ 28%]
tests/test_graphql/test_system_nixos_tasks.py ........                                [ 29%]
tests/test_graphql/test_users.py ..................................                   [ 42%]
tests/test_graphql/test_repository/test_json_tokens_repository.py                     [ 44%]
tests/test_graphql/test_repository/test_tokens_repository.py ....                     [ 53%]
tests/test_rest_endpoints/test_auth.py ..........................                     [ 58%]
tests/test_rest_endpoints/test_system.py ........................                     [ 63%]
tests/test_rest_endpoints/test_users.py ................................              [ 76%]
tests/test_rest_endpoints/services/test_bitwarden.py ............                     [ 78%]
tests/test_rest_endpoints/services/test_gitea.py ..............                       [ 80%]
tests/test_rest_endpoints/services/test_mailserver.py .....                           [ 81%]
tests/test_rest_endpoints/services/test_nextcloud.py ............                     [ 83%]
tests/test_rest_endpoints/services/test_ocserv.py ..............                      [ 85%]
tests/test_rest_endpoints/services/test_pleroma.py ..............                     [ 87%]
tests/test_rest_endpoints/services/test_services.py ....                              [ 88%]
tests/test_rest_endpoints/services/test_ssh.py .....................                  [100%]

============================== 692 passed in 352.76s (0:05:52) ===============================
```

## dependencies and dependant modules

Current flake inherits nixpkgs from NixOS configuration flake. So there is no need to refer to extra nixpkgs dependency if you want to be aligned with exact NixOS configuration.

![diagram](http://www.plantuml.com/plantuml/proxy?src=https://git.selfprivacy.org/SelfPrivacy/selfprivacy-rest-api/raw/branch/flake/nix-dependencies-diagram.puml)

Nix code for NixOS service module for API is located in NixOS configuration repository.

## current issues

- It's not clear how to store in this repository information about several compatible NixOS configuration commits, where API application tests pass. Currently, here is only a single `flake.lock`.
