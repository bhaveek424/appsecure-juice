from app.zap.client import HttpZapClient, ZapClient

_override: ZapClient | None = None


def get_zap_client() -> ZapClient:
    if _override is not None:
        return _override
    return HttpZapClient()


def set_zap_client(client: ZapClient) -> None:
    global _override
    _override = client


def clear_zap_client() -> None:
    global _override
    _override = None
