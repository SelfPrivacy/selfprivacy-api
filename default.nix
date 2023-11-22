{ pythonPackages }:

pythonPackages.buildPythonApplication rec {
  pname = "selfprivacy-graphql-api";
  version = "local";
  src = builtins.filterSource (p: t: p != ".git" && t != "symlink") ./.;
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
  meta = {
    description = ''
      SelfPrivacy Server Management API
    '';
  };
}
