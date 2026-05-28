from app.target.http import HttpTargetClient
from app.target.mock import MockTargetClient
from app.target.types import TargetClient

_override: TargetClient | None = None


def get_target_client() -> TargetClient:
    if _override is not None:
        return _override
    return HttpTargetClient()


def set_target_client(client: TargetClient) -> None:
    global _override
    _override = client


def clear_target_client() -> None:
    global _override
    _override = None
