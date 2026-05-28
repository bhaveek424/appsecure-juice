from fastapi.testclient import TestClient

from app.domain.actor_context import ActorContext
from app.domain.review_skill import ReviewSkillId
from app.domain.skill_run_outcome import SkillRunOutcome
from app.skills.review_ownership import evaluate_cross_actor_review_probe
from app.target.mock import MockTargetClient
from app.target.types import ProbeCapture


def test_evaluate_cross_actor_review_probe_detects_ownership_bypass():
    violation_probe = ProbeCapture(
        scenario="Cross-actor review edit",
        actor_context=ActorContext.USER_B,
        request_method="PATCH",
        request_path="/rest/products/reviews",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body=(
            '{"modified":1,"original":[{"_id":"abc","author":"user-a@review.local",'
            '"message":"tampered"}]}'
        ),
    )

    result = evaluate_cross_actor_review_probe(
        violation_probe, owner_email="user-a@review.local"
    )
    assert result.supports_finding is True


def test_evaluate_cross_actor_review_probe_rejects_unrelated_author():
    other_author_probe = ProbeCapture(
        scenario="Cross-actor review edit",
        actor_context=ActorContext.USER_B,
        request_method="PATCH",
        request_path="/rest/products/reviews",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body=(
            '{"modified":1,"original":[{"_id":"abc","author":"user-b@review.local",'
            '"message":"tampered"}]}'
        ),
    )

    result = evaluate_cross_actor_review_probe(
        other_author_probe, owner_email="user-a@review.local"
    )
    assert result.supports_finding is False


def test_evaluate_cross_actor_review_probe_creates_finding_only_with_boundary_evidence():
    violation_probe = ProbeCapture(
        scenario="Cross-actor review edit",
        actor_context=ActorContext.USER_B,
        request_method="PATCH",
        request_path="/rest/products/reviews",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body=(
            '{"modified":1,"original":[{"author":"user-a@review.local"}]}'
        ),
    )
    inconclusive_probe = ProbeCapture(
        scenario="Cross-actor review edit",
        actor_context=ActorContext.USER_B,
        request_method="PATCH",
        request_path="/rest/products/reviews",
        request_headers={"Authorization": "Bearer secret"},
        response_status=403,
        response_headers={},
        response_body='{"error":"Forbidden"}',
    )

    assert (
        evaluate_cross_actor_review_probe(
            violation_probe, owner_email="user-a@review.local"
        ).supports_finding
        is True
    )
    assert (
        evaluate_cross_actor_review_probe(
            inconclusive_probe, owner_email="user-a@review.local"
        ).supports_finding
        is False
    )


def _ready_review_run(client: TestClient) -> str:
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]
    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == "Ready For Skills"
    return run_id


def test_run_review_ownership_skill_creates_finding_when_ownership_violated(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            review_ownership_violation=True,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.REVIEW_OWNERSHIP}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["outcome"] == SkillRunOutcome.FINDING_CREATED
        assert skill_run["finding_id"] is not None
        assert len(skill_run["evidence_packets"]) == 1

        packet = skill_run["evidence_packets"][0]
        assert packet["actor_context"] == ActorContext.USER_B.value
        assert packet["response_status"] == 200
        assert "Bearer" not in str(packet)
        assert "token-user-b" not in str(packet)

        detail = client.get(f"/api/scans/{run_id}").json()
        business_findings = [
            finding
            for finding in detail["findings"]
            if finding["source"] == "Business Logic"
        ]
        assert len(business_findings) == 1

        finding_detail = client.get(
            f"/api/scans/{run_id}/findings/{business_findings[0]['id']}"
        ).json()
        assert finding_detail["business_logic"] is not None
        assert (
            finding_detail["business_logic"]["skill_id"]
            == ReviewSkillId.REVIEW_OWNERSHIP
        )
    finally:
        target_factory.clear_target_client()


def test_run_review_ownership_skill_stores_inconclusive_outcome_without_finding(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            review_ownership_violation=False,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.REVIEW_OWNERSHIP}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["outcome"] == SkillRunOutcome.INCONCLUSIVE
        assert skill_run["finding_id"] is None
        assert skill_run["inconclusive_reason"]

        detail = client.get(f"/api/scans/{run_id}").json()
        assert not any(
            finding["source"] == "Business Logic" for finding in detail["findings"]
        )
        assert len(detail["skill_runs"]) == 1
    finally:
        target_factory.clear_target_client()
