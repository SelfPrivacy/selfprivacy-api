import base64
import pytest
from urllib.parse import urlencode

from selfprivacy_api.utils.self_service_portal_utils import generate_qr_code


def test_qr_code_creation():
    """Test that QR code creation succeeds for deltachat functionality."""
    # Test data
    password = "test_password_123"
    server_domain = "example.com"
    login = "testuser@example.com"

    # Create deltachat parameters (same as in the actual function)
    deltachat_params = {
        "p": password,
        "v": 1,
        "ih": server_domain,
        "ip": 993,
        "sh": server_domain,
        "sp": 465,
    }

    # Create the deltachat URI
    deltachat_uri = f"dclogin://{login}?{urlencode(deltachat_params)}"

    # Test QR code creation using the extracted function
    deltachat_qr_base64 = generate_qr_code(deltachat_uri)

    # Verify base64 encoding succeeds
    assert deltachat_qr_base64 is not None
    assert isinstance(deltachat_qr_base64, str)
    assert len(deltachat_qr_base64) > 0

    # Verify the base64 string is valid by trying to decode it
    try:
        decoded_data = base64.b64decode(deltachat_qr_base64)
        assert len(decoded_data) > 0
    except Exception as e:
        pytest.fail(f"Failed to decode base64 QR code data: {e}")


def test_qr_code_with_different_parameters():
    """Test QR code creation with different parameter combinations."""
    test_cases = [
        {"password": "simple_pass", "domain": "test.com", "user": "user1"},
        {
            "password": "complex_p@ssw0rd!",
            "domain": "long-domain-name.example.org",
            "user": "complex.user+test",
        },
        {"password": "123456", "domain": "short.io", "user": "a"},
    ]

    for case in test_cases:
        password = case["password"]
        server_domain = case["domain"]
        login = f"{case['user']}@{server_domain}"

        deltachat_params = {
            "p": password,
            "v": 1,
            "ih": server_domain,
            "ip": 993,
            "sh": server_domain,
            "sp": 465,
        }

        deltachat_uri = f"dclogin://{login}?{urlencode(deltachat_params)}"

        # Should not raise any exceptions
        deltachat_qr_base64 = generate_qr_code(deltachat_uri)
        assert deltachat_qr_base64 is not None
        assert len(deltachat_qr_base64) > 0


def test_qr_code_uri_format():
    """Test that the generated deltachat URI has the correct format."""
    password = "test_password"
    server_domain = "example.com"
    login = "testuser@example.com"

    deltachat_params = {
        "p": password,
        "v": 1,
        "ih": server_domain,
        "ip": 993,
        "sh": server_domain,
        "sp": 465,
    }

    deltachat_uri = f"dclogin://{login}?{urlencode(deltachat_params)}"

    # Verify URI format
    assert deltachat_uri.startswith("dclogin://")
    assert login in deltachat_uri
    assert "p=test_password" in deltachat_uri
    assert "v=1" in deltachat_uri
    assert "ih=example.com" in deltachat_uri
    assert "ip=993" in deltachat_uri
    assert "sh=example.com" in deltachat_uri
    assert "sp=465" in deltachat_uri

    # Test that QR code generation works with this URI
    qr_base64 = generate_qr_code(deltachat_uri)
    assert qr_base64 is not None
    assert len(qr_base64) > 0


def test_qr_code_with_special_characters():
    """Test QR code creation with special characters in password."""
    # Test with various special characters that might be in passwords
    special_passwords = [
        "pass@word",
        "p@ssw0rd!",
        "test#123$",
        "user&pass%",
        "complex+password=test",
    ]

    server_domain = "example.com"
    login = "testuser@example.com"

    for password in special_passwords:
        deltachat_params = {
            "p": password,
            "v": 1,
            "ih": server_domain,
            "ip": 993,
            "sh": server_domain,
            "sp": 465,
        }

        deltachat_uri = f"dclogin://{login}?{urlencode(deltachat_params)}"

        # Should handle URL encoding properly and not fail
        deltachat_qr_base64 = generate_qr_code(deltachat_uri)
        assert deltachat_qr_base64 is not None
        assert len(deltachat_qr_base64) > 0

        # Verify it's valid base64
        try:
            base64.b64decode(deltachat_qr_base64)
        except Exception as e:
            pytest.fail(f"Invalid base64 for password '{password}': {e}")


def test_qr_code_error_handling():
    """Test error handling with invalid inputs."""
    # Test with empty URI - this should still work as qrcode handles empty strings
    empty_qr = generate_qr_code("")
    assert empty_qr is not None
    assert len(empty_qr) > 0


def test_qr_code_function_directly():
    """Test the generate_qr_code function directly with various inputs."""
    test_inputs = [
        "simple text",
        "https://example.com",
        "dclogin://user@domain.com?p=password&v=1",
        "unicode: 你好世界",
        "numbers: 1234567890",
        "symbols: !@#$%^&*()_+-=[]{}|;:,.<>?",
    ]

    for test_input in test_inputs:
        qr_base64 = generate_qr_code(test_input)
        assert qr_base64 is not None
        assert isinstance(qr_base64, str)
        assert len(qr_base64) > 0

        # Verify it's valid base64
        try:
            decoded = base64.b64decode(qr_base64)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Invalid base64 for input '{test_input}': {e}")
