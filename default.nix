{ pythonPackages, rev ? "local" }:

pythonPackages.buildPythonPackage rec {
  pname = "selfprivacy-graphql-api";
  version = rev;
  src = builtins.filterSource (p: t: p != ".git" && t != "symlink") ./.;
  nativeCheckInputs = [ pythonPackages.pytestCheckHook ];
  propagatedBuildInputs = with pythonPackages; [
    fastapi
    gevent
    huey
    mnemonic
    portalocker
    psutil
    pydantic
    pytest
    pytest-datadir
    pytest-mock
    pytz
    redis
    setuptools
    strawberry-graphql
    typing-extensions
    uvicorn
  ];
  pythonImportsCheck = [ "selfprivacy_api" ];
  doCheck = true;
  meta = {
    description = ''
      SelfPrivacy Server Management API
    '';
  };
}
