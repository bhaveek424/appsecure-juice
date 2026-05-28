from urllib.parse import urlparse, urlunparse


def normalize_target(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.hostname:
        msg = "Target must be an absolute URL with scheme and host"
        raise ValueError(msg)

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    port = parsed.port
    if port and (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        port = None

    netloc = f"{host}:{port}" if port else host
    path = parsed.path.rstrip("/")

    return urlunparse((scheme, netloc, path, "", parsed.query, ""))
