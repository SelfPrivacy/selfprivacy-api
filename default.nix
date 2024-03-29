{ pythonPackages, rev ? "local" }:

pythonPackages.buildPythonPackage rec {
  pname = "selfprivacy-graphql-api";
  version = rev;
  src = builtins.filterSource (p: t: p != ".git" && t != "symlink") ./.;
  propagatedBuildInputs = with pythonPackages; [
    fastapi
    gevent
    huey
    mnemonic
    portalocker
    psutil
    pydantic
    pytz
    redis
    setuptools
    strawberry-graphql
    typing-extensions
    uvicorn
  ];
  pythonImportsCheck = [ "selfprivacy_api" ];
  doCheck = false;
  meta = {
    description = ''
      SelfPrivacy Server Management API
    '';
  };
}
