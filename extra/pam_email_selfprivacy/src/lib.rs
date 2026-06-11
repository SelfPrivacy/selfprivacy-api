use nonstick::{ErrorCode, ModuleClient, PamModule, pam_export};
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct CheckEmailPasswordBody {
    username: String,
    password: String,
}

#[derive(Deserialize)]
pub struct CheckEmailPasswordResponse {
    #[serde(rename = "isValid")]
    is_valid: bool,
}

struct SelfPrivacyEmailPam;
pam_export!(SelfPrivacyEmailPam);

impl<M: ModuleClient> PamModule<M> for SelfPrivacyEmailPam {
    fn authenticate(
        handle: &mut M,
        _args: Vec<&std::ffi::CStr>,
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

        // TODO: get port at runtime or even better, use varlink/http over unix socket.
        let response = minreq::post("http://127.0.0.1:5050/internal/check-email-password")
            .with_header("Content-Type", "application/json")
            .with_timeout(3)
            .with_json(&CheckEmailPasswordBody { username, password })
            .map_err(|_| ErrorCode::AuthenticationError)?
            .send()
            .map_err(|_| ErrorCode::AuthInfoUnavailable)?
            .json::<CheckEmailPasswordResponse>()
            .map_err(|_| ErrorCode::AuthInfoUnavailable)?;

        if response.is_valid {
            Ok(())
        } else {
            Err(ErrorCode::AuthenticationError)
        }
    }
}
