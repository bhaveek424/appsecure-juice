from typing import Any

_SENSITIVE_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-access-token",
        "x-auth-token",
    }
)


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in _SENSITIVE_HEADER_NAMES:
            sanitized[name] = "[REDACTED]"
        else:
            sanitized[name] = value
    return sanitized


def sanitize_probe_capture(capture: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(capture)
    if "request_headers" in sanitized:
        sanitized["request_headers"] = sanitize_headers(
            dict(sanitized["request_headers"])
        )
    if "response_headers" in sanitized:
        sanitized["response_headers"] = sanitize_headers(
            dict(sanitized["response_headers"])
        )
    return sanitized
