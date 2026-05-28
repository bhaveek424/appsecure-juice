import os

from fastapi.testclient import TestClient

from app.main import app

PUBLIC_CONFIG_KEYS = {
    "target_application_url",
    "llm_provider",
    "llm_configured",
}

FORBIDDEN_PUBLIC_KEYS = {
    "zap_api_url",
    "database_url",
    "zap_api_key",
    "nvidia_api_key",
    "llm_api_key",
    "api_key",
    "secret",
    "password",
    "token",
}


def test_config_exposes_target_application(monkeypatch):
    monkeypatch.setenv(
        "TARGET_APPLICATION_URL", "http://juice-shop:3000/#/"
    )
    monkeypatch.setenv("ZAP_API_KEY", "super-secret-zap-key")
    monkeypatch.setenv("NVIDIA_API_KEY", "super-secret-nvidia-key")
    from app.config import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    response = client.get("/api/config")

    assert response.status_code == 200
    data = response.json()
    assert data["target_application_url"] == "http://juice-shop:3000/#/"
    assert data["llm_provider"] == os.getenv("LLM_PROVIDER", "mock")
    assert set(data.keys()) == PUBLIC_CONFIG_KEYS

    for key in FORBIDDEN_PUBLIC_KEYS:
        assert key not in data

    assert "super-secret" not in str(data)


def test_config_reports_llm_configured_without_exposing_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "super-secret-nvidia-key")
    from app.config import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    data = client.get("/api/config").json()

    assert data["llm_configured"] is True
    assert "super-secret-nvidia-key" not in str(data)


def test_config_uses_mock_provider_when_nvidia_key_missing(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    from app.config import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    data = client.get("/api/config").json()

    assert data["llm_provider"] == "mock"
    assert data["llm_configured"] is False
