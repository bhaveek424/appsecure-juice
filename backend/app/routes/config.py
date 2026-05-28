from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def read_config():
    settings = get_settings()
    return {
        "target_application_url": settings.target_application_url,
        "zap_api_url": settings.zap_api_url,
        "database_url": settings.database_url,
        "llm_provider": settings.llm_provider,
        "llm_configured": settings.nvidia_api_key is not None
        and bool(settings.nvidia_api_key.get_secret_value()),
    }
