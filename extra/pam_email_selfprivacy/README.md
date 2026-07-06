# pam_email_selfprivacy

PAM module that uses SelfPrivacy API email password checking endpoint to authenticate users in Dovecot. (PAM service & Dovecot config glue is defined in nixos/module.nix)
Dovecot 2.4 dropped ability to run shell scripts to check password, and pam_exec doesn't provide way to reliably return error code to PAM.

## Development

(make sure cargo is running from `nix develop` environment)

- `cargo check` for checking syntax
- `cargo clippy` for linting
- `cargo test` for tests

## Internals

This PAM module uses `/internal/check-email-password` REST endpoint from API service.
API port can be configured through PAM argument, `port=number`.
