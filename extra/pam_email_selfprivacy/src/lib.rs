mod api;
mod config;

use nonstick::{ErrorCode, ModuleClient, PamModule, pam_export};

use crate::{api::check_email_password, config::parse_api_port};

struct SelfPrivacyEmailPam;
pam_export!(SelfPrivacyEmailPam);

impl<M: ModuleClient> PamModule<M> for SelfPrivacyEmailPam {
    fn authenticate(
        handle: &mut M,
        args: Vec<&std::ffi::CStr>,
        _flags: nonstick::AuthnFlags,
    ) -> nonstick::Result<()> {
        let username = handle
            .username(None)?
            .into_string()
            .map_err(|_| ErrorCode::UserUnknown)?;
        let password = handle
            .authtok(None)?
            .into_string()
            .map_err(|_| ErrorCode::AuthTokError)?;

        let api_port = parse_api_port(&args).map_err(|_| ErrorCode::ServiceError)?;

        let is_valid = check_email_password(
            api::CheckEmailPasswordRequest { username, password },
            api_port,
        )
        .map_err(|err| match err {
            api::CheckEmailPasswordError::RequestEncoding(_) => ErrorCode::AuthenticationError,
            api::CheckEmailPasswordError::Request(_) => ErrorCode::AuthInfoUnavailable,
            api::CheckEmailPasswordError::ResponseDecoding(_) => ErrorCode::AuthInfoUnavailable,
        })?;

        if is_valid {
            Ok(())
        } else {
            Err(ErrorCode::AuthenticationError)
        }
    }
}
