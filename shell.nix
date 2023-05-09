{ pkgs ? import <nixos-22.11> { } }:
let
  sp-python = pkgs.python310.withPackages (p: with p; [
    setuptools
    portalocker
    pytz
    pytest
    pytest-mock
    pytest-datadir
    huey
    gevent
    mnemonic
    coverage
    pylint
    pydantic
    typing-extensions
    psutil
    black
    fastapi
    uvicorn
    redis
    strawberry-graphql
  ]);
in
pkgs.mkShell {
  buildInputs = [
    sp-python
    pkgs.black
    pkgs.redis
    pkgs.restic
  ];
  shellHook = ''
    PYTHONPATH=${sp-python}/${sp-python.sitePackages}
    # envs set with export and as attributes are treated differently.
    # for example. printenv <Name> will not fetch the value of an attribute.
    export USE_REDIS_PORT=6379
    pkill redis-server
    redis-server --bind 127.0.0.1 --port $USE_REDIS_PORT >/dev/null &
    # maybe set more env-vars
  '';
}
