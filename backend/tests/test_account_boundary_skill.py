from fastapi.testclient import TestClient

from app.domain.review_skill import ReviewSkillId
from app.domain.skill_run_outcome import SkillRunOutcome
from app.skills.account_boundary import evaluate_cross_actor_basket_probe
from app.target.mock import MockTargetClient
from app.target.types import ProbeCapture
from app.domain.actor_context import ActorContext


def test_evaluate_cross_actor_basket_probe_detects_juice_shop_products_shape():
    juice_shop_probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/10",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body=(
            '{"id":10,"UserId":1,"Products":[{"id":1,"name":"Apple Juice"}]}'
        ),
    )

    assert evaluate_cross_actor_basket_probe(juice_shop_probe).supports_finding is True


def test_evaluate_cross_actor_basket_probe_detects_empty_products_basket():
    empty_basket_probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/10",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body='{"id":10,"UserId":1,"Products":[]}',
    )

    assert evaluate_cross_actor_basket_probe(empty_basket_probe).supports_finding is True


def test_evaluate_cross_actor_basket_probe_rejects_mock_only_items_without_basket_id():
    mock_only_probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/10",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body='{"items":[{"name":"Apple Juice"}]}',
    )

    assert evaluate_cross_actor_basket_probe(mock_only_probe).supports_finding is False


def test_evaluate_cross_actor_basket_probe_creates_finding_only_with_boundary_evidence():
    violation_probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/10",
        request_headers={"Authorization": "Bearer secret"},
        response_status=200,
        response_headers={},
        response_body='{"id":10,"UserId":1,"items":[{"name":"Apple Juice"}]}',
    )
    inconclusive_probe = ProbeCapture(
        scenario="Cross-actor basket read",
        actor_context=ActorContext.USER_B,
        request_method="GET",
        request_path="/rest/basket/10",
        request_headers={"Authorization": "Bearer secret"},
        response_status=403,
        response_headers={},
        response_body='{"error":"Forbidden"}',
    )

    assert evaluate_cross_actor_basket_probe(violation_probe).supports_finding is True
    assert evaluate_cross_actor_basket_probe(inconclusive_probe).supports_finding is False


def _ready_review_run(client: TestClient) -> str:
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]
    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == "Ready For Skills"
    return run_id


def test_run_account_boundary_skill_creates_finding_when_boundary_violated(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(MockTargetClient(boundary_violation=True))
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.ACCOUNT_BOUNDARY}/run"
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
            finding for finding in detail["findings"] if finding["source"] == "Business Logic"
        ]
        assert len(business_findings) == 1

        finding_detail = client.get(
            f"/api/scans/{run_id}/findings/{business_findings[0]['id']}"
        ).json()
        assert finding_detail["business_logic"] is not None
        assert finding_detail["business_logic"]["skill_id"] == ReviewSkillId.ACCOUNT_BOUNDARY
    finally:
        target_factory.clear_target_client()


def test_run_account_boundary_skill_stores_inconclusive_outcome_without_finding(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(MockTargetClient(boundary_violation=False))
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.ACCOUNT_BOUNDARY}/run"
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


def test_run_account_boundary_skill_rejects_unknown_skill(client: TestClient):
    run_id = _ready_review_run(client)
    response = client.post(f"/api/scans/{run_id}/skills/unknown-skill/run")
    assert response.status_code == 404
