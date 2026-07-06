{
  rustPlatform,
  pam,
  callPackage,
  lib,
}:
lib.fix (
  self:
  rustPlatform.buildRustPackage {
    pname = "pam_email_selfprivacy";
    version = "0.1.0";

    src = ./.;

    buildInputs = [ pam ];

    cargoHash = "sha256-vwBsPRzTQ2dDyPH3rRe4yADWou7k0qj5GsSqUOx9fig=";

    passthru.tests.vm-integration = callPackage ./vm-test.nix {
      inherit self;
    };
  }
)
