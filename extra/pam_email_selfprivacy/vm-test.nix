{
  pkgs,
  self,
}:

let
  mockApi =
    pkgs.writers.writePython3 "mock-check-email-password"
      {
        libraries = [ pkgs.python3Packages.flask ];
      }
      ''
        from flask import Flask, request, jsonify

        app = Flask(__name__)


        @app.post("/internal/check-email-password")
        def check_email_password():
            data = request.get_json(force=True)
            return jsonify({
                "isValid": (
                    data.get("username") == "deer@selfprivacy.org"
                    and data.get("password") == "ilikeacorns"
                )
            })


        app.run(host="127.0.0.1", port=8000)
      '';
in
pkgs.testers.runNixOSTest {
  name = "pam-email-selfprivacy";

  nodes.machine =
    { pkgs, ... }:
    {
      documentation.enable = false;

      environment.systemPackages = [
        pkgs.pamtester
      ];

      systemd.services.mock-selfprivacy-api = {
        wantedBy = [ "multi-user.target" ];
        after = [ "network.target" ];
        serviceConfig = {
          ExecStart = "${mockApi}";
        };
      };

      security.pam.services.selfprivacymail.text = ''
        auth required ${self}/lib/libpam_email_selfprivacy.so port=8000
        account required pam_permit.so
      '';
    };

  testScript = ''
    start_all()

    machine.wait_for_unit("mock-selfprivacy-api.service")
    machine.wait_until_succeeds("curl -s http://127.0.0.1:8000")

    machine.succeed(
        "printf 'ilikeacorns\\n' | pamtester selfprivacymail deer@selfprivacy.org authenticate"
    )

    output = machine.fail(
        "printf 'ilikefish\\n' | pamtester selfprivacymail deer@selfprivacy.org authenticate 2>&1"
    )

    assert "Authentication failure" in output # Password: pamtester: Authentication failure

    output = machine.fail(
        "printf '1234\\n' | pamtester selfprivacymail unknown@selfprivacy.org authenticate 2>&1"
    )

    assert "Authentication failure" in output # Password: pamtester: Authentication failure

    machine.succeed("systemctl stop mock-selfprivacy-api.service")
    machine.wait_until_fails("systemctl is-active --quiet mock-selfprivacy-api.service")

    output = machine.fail(
        "printf 'ilikeacorns\\n' | pamtester selfprivacymail deer@selfprivacy.org authenticate 2>&1"
    )

    assert "Authentication service cannot retrieve authentication info" in output # Password: pamtester: Authentication service cannot retrieve authentication info
  '';
}
