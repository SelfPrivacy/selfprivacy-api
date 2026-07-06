use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct CheckEmailPasswordRequest {
    pub username: String,
    pub password: String,
}

#[derive(Deserialize)]
pub struct CheckEmailPasswordResponse {
    #[serde(rename = "isValid")]
    pub is_valid: bool,
}

#[derive(thiserror::Error, Debug)]
pub enum CheckEmailPasswordError {
    #[error("JSON request encoding error")]
    RequestEncoding(serde_json::Error),
    #[error("HTTP request error")]
    Request(minreq::Error),
    #[error("JSON response decoding error")]
    ResponseDecoding(minreq::Error),
}

pub fn check_email_password(
    request: CheckEmailPasswordRequest,
    api_port: u16,
) -> Result<bool, CheckEmailPasswordError> {
    let response = minreq::post(format!(
        "http://127.0.0.1:{}/internal/check-email-password",
        api_port
    ))
    .with_timeout(3)
    .with_json(&request)
    .map_err(|err| {
        CheckEmailPasswordError::RequestEncoding(match err {
            minreq::Error::SerdeJsonError(err) => err,
            _ => unreachable!(),
        })
    })?
    .send()
    .map_err(CheckEmailPasswordError::Request)?
    .json::<CheckEmailPasswordResponse>()
    .map_err(CheckEmailPasswordError::ResponseDecoding)?;

    Ok(response.is_valid)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        io::{Read, Write},
        net::TcpListener,
        sync::mpsc::{self, Receiver},
        thread,
    };

    fn mock_api(status: &'static str, body: &'static str) -> (u16, Receiver<String>) {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let port = listener.local_addr().unwrap().port();
        let (request_tx, request_rx) = mpsc::channel();

        thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();

            let mut request = [0; 4096];
            let bytes_read = stream.read(&mut request).unwrap();
            let _ = request_tx.send(String::from_utf8_lossy(&request[..bytes_read]).into_owned());

            let response = format!(
                "HTTP/1.1 {status}\r\n\
                 Content-Type: application/json\r\n\
                 Content-Length: {}\r\n\
                 Connection: close\r\n\
                 \r\n\
                 {body}",
                body.len()
            );

            stream.write_all(response.as_bytes()).unwrap();
        });

        (port, request_rx)
    }

    fn request() -> CheckEmailPasswordRequest {
        CheckEmailPasswordRequest {
            username: "deer@selfprivacy.org".to_string(),
            password: "ilikeacorns".to_string(),
        }
    }

    #[test]
    fn returns_true_when_api_accepts_credentials() {
        let (port, _) = mock_api("200 OK", r#"{"isValid":true}"#);

        let is_valid = check_email_password(request(), port).unwrap();

        assert!(is_valid);
    }

    #[test]
    fn returns_false_when_api_rejects_credentials() {
        let (port, _) = mock_api("200 OK", r#"{"isValid":false}"#);

        let is_valid = check_email_password(request(), port).unwrap();

        assert!(!is_valid);
    }

    #[test]
    fn posts_credentials_to_check_email_password_endpoint() {
        let (port, request_rx) = mock_api("200 OK", r#"{"isValid":true}"#);

        check_email_password(request(), port).unwrap();
        let request = request_rx.recv().unwrap();

        assert!(request.starts_with("POST /internal/check-email-password HTTP/1.1\r\n"));
        assert!(request.contains("Content-Type: application/json"));
        assert!(request.contains(r#""username":"deer@selfprivacy.org""#));
        assert!(request.contains(r#""password":"ilikeacorns""#));
    }

    #[test]
    fn invalid_json_is_response_decoding_error() {
        let (port, _) = mock_api("200 OK", "not json");

        let err = check_email_password(request(), port).unwrap_err();

        assert!(matches!(err, CheckEmailPasswordError::ResponseDecoding(_)));
    }

    #[test]
    fn unreachable_api_is_request_error() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let port = listener.local_addr().unwrap().port();
        drop(listener);

        let err = check_email_password(request(), port).unwrap_err();

        assert!(matches!(err, CheckEmailPasswordError::Request(_)));
    }
}
