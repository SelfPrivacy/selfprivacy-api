{ rustPlatform, pam }:
rustPlatform.buildRustPackage {
  pname = "pam_email_selfprivacy";
  version = "1.0.0";

  src = ./.;

  buildInputs = [pam];

  cargoHash = "sha256-VZ72baev2y0ZedQC3kJ8dM7XWFMGdkUXdQf/mGxWLpE=";
}
