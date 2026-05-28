from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


@patch("app.dependencies.check_zap", return_value=True)
@patch("app.dependencies.check_target_application", return_value=True)
def test_health_ok_when_dependencies_reachable(_mock_target, _mock_zap):
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {
            "target_application": {"reachable": True},
            "zap": {"reachable": True},
        },
    }


@patch("app.dependencies.check_zap", return_value=True)
@patch("app.dependencies.check_target_application", return_value=False)
def test_health_degraded_when_target_unreachable(_mock_target, _mock_zap):
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["target_application"]["reachable"] is False
    assert data["dependencies"]["zap"]["reachable"] is True


@patch("app.dependencies.check_zap", return_value=False)
@patch("app.dependencies.check_target_application", return_value=True)
def test_health_degraded_when_zap_unreachable(_mock_target, _mock_zap):
    client = TestClient(app)
    data = client.get("/health").json()

    assert data["status"] == "degraded"
    assert data["dependencies"]["zap"]["reachable"] is False
