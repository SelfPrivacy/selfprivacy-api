use std::ffi::CStr;

use thiserror::Error;

pub const DEFAULT_API_PORT: u16 = 5050;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ConfigError {
    #[error("PAM argument is not valid UTF-8")]
    InvalidUtf8,
    #[error("invalid port")]
    InvalidPort,
}

pub fn parse_api_port(args: &[&CStr]) -> Result<u16, ConfigError> {
    for arg in args {
        let arg = arg.to_str().map_err(|_| ConfigError::InvalidUtf8)?;
        if let Some(value) = arg.strip_prefix("port=") {
            return value.parse().map_err(|_| ConfigError::InvalidPort);
        }
    }

    Ok(DEFAULT_API_PORT)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::CString;

    fn args(args: &[&str]) -> Vec<CString> {
        args.iter().map(|arg| CString::new(*arg).unwrap()).collect()
    }

    fn refs(args: &[CString]) -> Vec<&CStr> {
        args.iter().map(|arg| arg.as_c_str()).collect()
    }

    #[test]
    fn returns_default_api_port_without_args() {
        assert_eq!(parse_api_port(&[]).unwrap(), DEFAULT_API_PORT);
    }

    #[test]
    fn parses_api_port_from_port_arg() {
        let args = args(&["port=1234"]);
        assert_eq!(parse_api_port(&refs(&args)).unwrap(), 1234);
    }

    #[test]
    fn ignores_unrelated_args() {
        let args = args(&["debug", "foo=bar"]);
        assert_eq!(parse_api_port(&refs(&args)).unwrap(), DEFAULT_API_PORT);
    }

    #[test]
    fn first_api_port_wins() {
        let args = args(&["port=1234", "port=5678"]);
        assert_eq!(parse_api_port(&refs(&args)).unwrap(), 1234);
    }

    #[test]
    fn rejects_non_numeric_api_port() {
        let args = args(&["port=nan"]);
        assert_eq!(parse_api_port(&refs(&args)), Err(ConfigError::InvalidPort));
    }

    #[test]
    fn rejects_out_of_range_api_port() {
        let args = args(&["port=65536"]);
        assert_eq!(parse_api_port(&refs(&args)), Err(ConfigError::InvalidPort));
    }
}
