from app.evidence.sanitizer import sanitize_headers, sanitize_probe_capture


def test_sanitize_headers_redacts_authorization_and_cookies():
    headers = {
        "Authorization": "Bearer secret-token",
        "Cookie": "session=abc123",
        "Accept": "application/json",
    }

    sanitized = sanitize_headers(headers)

    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["Cookie"] == "[REDACTED]"
    assert sanitized["Accept"] == "application/json"
    assert "secret-token" not in str(sanitized)


def test_sanitize_probe_capture_redacts_sensitive_headers_in_packet():
    capture = {
        "request_method": "GET",
        "request_path": "/rest/basket/1",
        "request_headers": {"Authorization": "Bearer abc"},
        "response_status": 200,
        "response_headers": {"Set-Cookie": "token=xyz"},
        "response_body": '{"items":[]}',
    }

    sanitized = sanitize_probe_capture(capture)

    assert sanitized["request_headers"]["Authorization"] == "[REDACTED]"
    assert sanitized["response_headers"]["Set-Cookie"] == "[REDACTED]"
    assert "abc" not in str(sanitized)
    assert "xyz" not in str(sanitized)
