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