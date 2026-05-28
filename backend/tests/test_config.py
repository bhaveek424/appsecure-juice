import os

from fastapi.testclient import TestClient

from app.main import app

SECRET_KEYS = {
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

    for key in data:
        assert key.lower() not in SECRET_KEYS
        assert "secret" not in key.lower()
        assert "super-secret" not in str(data[key])


def test_config_reports_llm_configured_without_exposing_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "super-secret-nvidia-key")
    from app.config import get_settings

    get_settings.cache_clear()

    client = TestClient(app)
    data = client.get("/api/config").json()

    assert data["llm_configured"] is True
    assert "super-secret-nvidia-key" not in str(data)
