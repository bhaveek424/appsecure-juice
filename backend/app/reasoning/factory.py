from app.config import Settings, get_settings
from app.reasoning.nvidia import HttpNvidiaNimReasoningClient
from app.reasoning.mock import MockReasoningClient
from app.reasoning.types import ReasoningClient

_override: ReasoningClient | None = None


def resolved_llm_provider(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    nvidia_key = settings.nvidia_api_key
    if (
        settings.llm_provider == "nvidia"
        and nvidia_key is not None
        and bool(nvidia_key.get_secret_value())
    ):
        return "nvidia"
    return "mock"


def get_reasoning_client() -> ReasoningClient:
    if _override is not None:
        return _override

    settings = get_settings()
    if resolved_llm_provider(settings) == "nvidia":
        return HttpNvidiaNimReasoningClient()
    return MockReasoningClient()


def set_reasoning_client(client: ReasoningClient) -> None:
    global _override
    _override = client


def clear_reasoning_client() -> None:
    global _override
    _override = None
