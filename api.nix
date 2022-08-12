{ lib, python39Packages }:
with python39Packages;
buildPythonApplication {
  pname = "selfprivacy-api";
  version = "2.0.0";

  propagatedBuildInputs = [
    setuptools
        portalocker
        pytz
        pytest
        pytest-mock
        pytest-datadir
        huey
        gevent
        mnemonic
        pydantic
        typing-extensions
        psutil
        fastapi
        uvicorn
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
      ];

  src = ./.;
}
