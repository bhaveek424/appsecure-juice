from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    target_application_url: str = "http://juice-shop:3000"
    zap_api_url: str = "http://zap:8080"
    zap_api_key: SecretStr = SecretStr("changeme")
    database_url: str = "sqlite:///./data/review.db"
    llm_provider: str = "mock"
    nvidia_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
