import pytest
from fastapi.testclient import TestClient


def test_review_run_zap_scan_persists_normalized_findings(client: TestClient):
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]

    detail = client.get(f"/api/scans/{run_id}").json()

    assert detail["status"] == "Ready For Skills"
    assert detail["current_step"] == "Agent triage complete"
    assert detail["progress"] == 1.0
    assert len(detail["findings"]) == 1

    finding = detail["findings"][0]
    assert finding["source"] == "Scanner"
    assert finding["severity"] == "High"
    assert finding["title"] == "Cross Site Scripting"
    assert "riskcode" not in finding
    assert "pluginId" not in finding

    summary = client.get("/api/scans").json()[0]
    assert summary["finding_counts"]["high"] == 1
    assert summary["finding_counts"]["critical"] == 0


def test_review_run_transitions_through_triage_with_hypotheses(client: TestClient):
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]

    detail = client.get(f"/api/scans/{run_id}").json()

    assert detail["status"] == "Ready For Skills"
    assert detail["current_step"] == "Agent triage complete"
    assert len(detail["findings"]) == 1
    assert len(detail["hypotheses"]) >= 1

    hypothesis = detail["hypotheses"][0]
    assert hypothesis["title"]
    assert hypothesis["rationale"]
    assert hypothesis["recommended_skill_id"]
    assert hypothesis["recommended_skill_name"]
    assert hypothesis["priority"]
    assert len(hypothesis["source_observations"]) >= 1
    assert hypothesis["source_observations"][0]["finding_id"] == detail["findings"][0]["id"]


class _FailingReasoningClient:
    def triage(self, observations):
        raise RuntimeError("NIM 500")


def test_triage_failure_falls_back_to_mock_without_zap_failure_label(client):
    from app.reasoning import factory as reasoning_factory

    reasoning_factory.set_reasoning_client(_FailingReasoningClient())
    try:
        created = client.post("/api/scans")
        assert created.status_code == 201
        run_id = created.json()["id"]

        detail = client.get(f"/api/scans/{run_id}").json()

        assert detail["status"] == "Ready For Skills"
        assert detail["current_step"] == "Agent triage complete (mock fallback)"
        assert len(detail["findings"]) == 1
        assert len(detail["hypotheses"]) >= 1
        assert detail["current_step"] != "ZAP scan failed"
    finally:
        reasoning_factory.clear_reasoning_client()


def test_zap_failure_reports_zap_not_triage(client):
    from app.db import get_session_factory
    from app.services.review_runs import create_review_run
    from app.services.zap_scan import execute_zap_scan
    from app.zap import factory as zap_factory
    from app.zap.client import MockZapClient

    class _FailingZapClient(MockZapClient):
        def run_scan(self, target_url, progress_callback):
            raise RuntimeError("ZAP unavailable")

    zap_factory.set_zap_client(_FailingZapClient())
    db = get_session_factory()()
    try:
        run = create_review_run(db)
        run_id = run.id
        with pytest.raises(RuntimeError, match="ZAP unavailable"):
            execute_zap_scan(db, run_id, zap_factory.get_zap_client())

        detail = client.get(f"/api/scans/{run_id}").json()

        assert detail["status"] == "Failed"
        assert detail["current_step"] == "ZAP scan failed"
        assert detail["findings"] == []
        assert detail["hypotheses"] == []
    finally:
        db.close()
        zap_factory.clear_zap_client()
