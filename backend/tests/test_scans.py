import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db import Base
from app.domain.review_run_status import ReviewRunStatus
from app.models.review_run import ReviewRun


def test_create_review_run_returns_id(client: TestClient):
    response = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert isinstance(body["id"], str)
    assert len(body["id"]) > 0


def test_create_review_run_without_target_uses_configured_application(
    client: TestClient,
):
    response = client.post("/api/scans")

    assert response.status_code == 201
    assert "id" in response.json()


def test_create_review_run_with_empty_body_uses_configured_application(
    client: TestClient,
):
    response = client.post("/api/scans", json={})

    assert response.status_code == 201


def test_create_review_run_rejects_non_configured_target(client: TestClient):
    response = client.post(
        "/api/scans",
        json={"target": "http://evil.example.com"},
    )

    assert response.status_code == 400
    assert "Target Application" in response.json()["detail"]


def test_create_review_run_normalizes_target_before_match(client: TestClient):
    response = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000/"},
    )

    assert response.status_code == 201


def test_second_active_review_run_returns_conflict(client: TestClient):
    first = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000"},
    )
    assert first.status_code == 201
    active_id = first.json()["id"]

    second = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000"},
    )

    assert second.status_code == 409
    body = second.json()["detail"]
    assert body["active_run_id"] == active_id


def test_list_review_runs_includes_summary_fields(client: TestClient):
    created = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000"},
    ).json()

    response = client.get("/api/scans")
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1

    run = runs[0]
    assert run["id"] == created["id"]
    assert run["status"] == "Queued"
    assert run["current_step"] == "Queued"
    assert run["started_at"] is not None
    assert run["completed_at"] is None
    assert run["finding_counts"] == {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "informational": 0,
    }


def test_database_rejects_two_active_review_runs():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

    first = ReviewRun(
        target_url="http://juice-shop:3000",
        status=ReviewRunStatus.QUEUED,
        current_step="Queued",
        is_active=True,
    )
    second = ReviewRun(
        target_url="http://juice-shop:3000",
        status=ReviewRunStatus.QUEUED,
        current_step="Queued",
        is_active=True,
    )
    session.add(first)
    session.commit()
    session.add(second)

    with pytest.raises(IntegrityError):
        session.commit()

    session.close()


def test_get_review_run_returns_empty_collections(client: TestClient):
    created = client.post(
        "/api/scans",
        json={"target": "http://juice-shop:3000"},
    ).json()

    response = client.get(f"/api/scans/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["status"] == "Queued"
    assert body["current_step"] == "Queued"
    assert body["findings"] == []
    assert body["hypotheses"] == []
    assert body["skill_runs"] == []
