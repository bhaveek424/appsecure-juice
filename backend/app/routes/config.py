from fastapi import APIRouter

from app.config import get_settings
from app.reasoning.factory import resolved_llm_provider

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def read_config():
    settings = get_settings()
    nvidia_key = settings.nvidia_api_key
    llm_configured = (
        nvidia_key is not None and bool(nvidia_key.get_secret_value())
    )
    return {
        "target_application_url": settings.target_application_url,
        "llm_provider": resolved_llm_provider(settings),
        "llm_configured": llm_configured,
    }
