{ pkgs ? import <nixpkgs> {} }:
let
  sp-python = pkgs.python39.withPackages (p: with p; [
    flask
    flask-restful
    setuptools
    portalocker
    flask-swagger
    flask-swagger-ui
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
    flask-cors
    psutil
    black
    (buildPythonPackage rec {
      pname = "strawberry-graphql";
      version = "0.114.5";
      format = "pyproject";
      patches = [
        ./strawberry-graphql.patch
      ];
      propagatedBuildInputs = [
        typing-extensions
        graphql-core
        python-multipart
        python-dateutil
        flask
        pydantic
        pygments
        poetry
        flask-cors
      ];
      src = fetchPypi {
        inherit pname version;
        sha256 = "b6e007281cf29a66eeba66a512744853d8aa53b4ca2525befb6f350bb7b24df6";
      };
    })
  ]);
in
pkgs.mkShell {
  buildInputs = [
    sp-python
    pkgs.black
  ];
  shellHook = ''
    PYTHONPATH=${sp-python}/${sp-python.sitePackages}
    # maybe set more env-vars
  '';
}
