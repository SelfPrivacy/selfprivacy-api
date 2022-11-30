{ pkgs ? import <nixpkgs> { } }:
let
  sp-python = pkgs.python39.withPackages (p: with p; [
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
    (buildPythonPackage rec {
      pname = "strawberry-graphql";
      version = "0.123.0";
      format = "pyproject";
      patches = [
        ./strawberry-graphql.patch
      ];
      propagatedBuildInputs = [
        typing-extensions
        python-multipart
        python-dateutil
        # flask
        pydantic
        pygments
        poetry
        # flask-cors
        (buildPythonPackage rec {
          pname = "graphql-core";
          version = "3.2.0";
          format = "setuptools";
          src = fetchPypi {
            inherit pname version;
            sha256 = "sha256-huKgvgCL/eGe94OI3opyWh2UKpGQykMcJKYIN5c4A84=";
          };
          checkInputs = [
            pytest-asyncio
            pytest-benchmark
            pytestCheckHook
          ];
          pythonImportsCheck = [
            "graphql"
          ];
        })
      ];
      src = fetchPypi {
        inherit pname version;
        sha256 = "KsmZ5Xv8tUg6yBxieAEtvoKoRG60VS+iVGV0X6oCExo=";
      };
    })
  ]);
in
pkgs.mkShell {
  buildInputs = [
    sp-python
    pkgs.black
    pkgs.redis
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
