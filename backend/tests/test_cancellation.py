import pytest
from fastapi.testclient import TestClient

from app.domain.review_run_status import ReviewRunStatus


def _ready_review_run(client: TestClient) -> str:
    created = client.post("/api/scans")
    assert created.status_code == 201
    return created.json()["id"]


def test_cancel_active_review_run_marks_cancelled(client: TestClient):
    run_id = _ready_review_run(client)

    response = client.post(f"/api/scans/{run_id}/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ReviewRunStatus.CANCELLED
    assert body["current_step"] == "Review Run cancelled"
    assert body["completed_at"] is not None

    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == ReviewRunStatus.CANCELLED

    summary = client.get("/api/scans").json()[0]
    assert summary["status"] == ReviewRunStatus.CANCELLED


def test_cancel_attempts_to_stop_active_zap_scans(client: TestClient):
    from app.zap import factory as zap_factory
    from app.zap.client import MockZapClient

    zap_client = zap_factory.get_zap_client()
    assert isinstance(zap_client, MockZapClient)
    run_id = _ready_review_run(client)

    client.post(f"/api/scans/{run_id}/cancel")

    assert zap_client.stop_calls == 1


def test_cancel_during_skill_execution_stops_without_finding(
    client: TestClient, monkeypatch
):
    from app.domain.review_skill import ReviewSkillId
    from app.target import factory as target_factory
    from app.target.mock import MockTargetClient

    run_id = _ready_review_run(client)
    probe_calls = {"count": 0}
    base_client = MockTargetClient(boundary_violation=False)
    original_probe = base_client.probe_apply_coupon

    def probe_apply_coupon(session, basket_id, coupon_code, *, scenario):
        probe_calls["count"] += 1
        if probe_calls["count"] == 2:
            client.post(f"/api/scans/{run_id}/cancel")
        return original_probe(
            session, basket_id, coupon_code, scenario=scenario
        )

    target_factory.set_target_client(base_client)
    monkeypatch.setattr(base_client, "probe_apply_coupon", probe_apply_coupon)
    try:
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.COUPON_AND_DISCOUNT}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["finding_id"] is None
        assert "cancel" in skill_run["summary"].lower()

        detail = client.get(f"/api/scans/{run_id}").json()
        assert detail["status"] == ReviewRunStatus.CANCELLED
        assert not any(
            finding["source"] == "Business Logic" for finding in detail["findings"]
        )
    finally:
        target_factory.clear_target_client()


def test_cancel_during_triage_does_not_restore_ready_for_skills(
    client: TestClient, monkeypatch
):
    from app.db import get_session_factory
    from app.domain.severity import Severity
    from app.models.finding import Finding
    from app.reasoning.mock import MockReasoningClient
    from app.services import agent_triage as triage_module
    from app.services.agent_triage import execute_agent_triage
    from app.services.exceptions import ReviewRunCancelledError
    from app.services.review_runs import create_review_run

    db = get_session_factory()()
    try:
        run = create_review_run(db)
        run_id = run.id
        db.add(
            Finding(
                review_run_id=run_id,
                source="Scanner",
                title="Cross Site Scripting",
                category="Injection",
                severity=Severity.HIGH,
                endpoint="http://juice-shop:3000/#/search",
                description="Reflected XSS",
                remediation="Encode output",
                confidence="Medium",
                evidence_excerpt="<script>",
            )
        )
        db.commit()

        def triage_with_cancel(observations):
            client.post(f"/api/scans/{run_id}/cancel")
            return (
                "Agent triage complete",
                MockReasoningClient().triage(observations),
            )

        monkeypatch.setattr(triage_module, "_run_triage", triage_with_cancel)

        with pytest.raises(ReviewRunCancelledError):
            execute_agent_triage(db, run_id)
    finally:
        db.close()

    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == ReviewRunStatus.CANCELLED
    assert detail["hypotheses"] == []


def test_cancel_during_account_boundary_probe_stops_without_finding(
    client: TestClient, monkeypatch
):
    from app.domain.review_skill import ReviewSkillId
    from app.target import factory as target_factory
    from app.target.mock import MockTargetClient

    run_id = _ready_review_run(client)
    base_client = MockTargetClient(boundary_violation=True)
    original_probe = base_client.probe_cross_actor_basket_access

    def probe_cross_actor_basket_access(actor_b, basket_id):
        client.post(f"/api/scans/{run_id}/cancel")
        return original_probe(actor_b, basket_id)

    target_factory.set_target_client(base_client)
    monkeypatch.setattr(
        base_client,
        "probe_cross_actor_basket_access",
        probe_cross_actor_basket_access,
    )
    try:
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.ACCOUNT_BOUNDARY}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["finding_id"] is None

        detail = client.get(f"/api/scans/{run_id}").json()
        assert detail["status"] == ReviewRunStatus.CANCELLED
        assert not any(
            finding["source"] == "Business Logic" for finding in detail["findings"]
        )
    finally:
        target_factory.clear_target_client()


def test_run_recommended_skills_skips_completed_skills(client: TestClient):
    from app.domain.review_skill import ReviewSkillId

    run_id = _ready_review_run(client)
    completed = client.post(
        f"/api/scans/{run_id}/skills/{ReviewSkillId.ACCOUNT_BOUNDARY}/run"
    )
    assert completed.status_code == 201

    response = client.post(f"/api/scans/{run_id}/skills/run-recommended")

    assert response.status_code == 200
    skill_runs = response.json()["skill_runs"]
    ran_skill_ids = {run["skill_id"] for run in skill_runs}
    assert ReviewSkillId.ACCOUNT_BOUNDARY not in ran_skill_ids
    assert len(ran_skill_ids) >= 1
