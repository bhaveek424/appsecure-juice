from fastapi.testclient import TestClient

from app.domain.actor_context import ActorContext
from app.domain.review_skill import ReviewSkillId
from app.domain.skill_run_outcome import SkillRunOutcome
from app.skills.basket_and_checkout import evaluate_negative_basket_quantity_probe
from app.target.mock import MockTargetClient
from app.target.types import ProbeCapture


def test_evaluate_negative_basket_quantity_probe_detects_accepted_negative_quantity():
    positive_probe = ProbeCapture(
        scenario="Negative basket quantity",
        actor_context=ActorContext.USER_A,
        request_method="POST",
        request_path="/api/BasketItems/",
        request_headers={"Authorization": "Bearer secret"},
        response_status=201,
        response_headers={},
        response_body='{"ProductId":1,"BasketId":10,"quantity":-1,"id":99}',
    )

    assert evaluate_negative_basket_quantity_probe(positive_probe).supports_finding is True


def test_evaluate_negative_basket_quantity_probe_inconclusive_when_rejected():
    inconclusive_probe = ProbeCapture(
        scenario="Negative basket quantity",
        actor_context=ActorContext.USER_A,
        request_method="POST",
        request_path="/api/BasketItems/",
        request_headers={"Authorization": "Bearer secret"},
        response_status=400,
        response_headers={},
        response_body='{"error":"Invalid quantity"}',
    )

    result = evaluate_negative_basket_quantity_probe(inconclusive_probe)
    assert result.supports_finding is False
    assert result.inconclusive_reason


def _ready_review_run(client: TestClient) -> str:
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]
    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == "Ready For Skills"
    return run_id


def test_run_basket_and_checkout_skill_creates_finding_when_manipulation_accepted(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            checkout_manipulation_accepted=True,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.BASKET_AND_CHECKOUT}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["outcome"] == SkillRunOutcome.FINDING_CREATED
        assert skill_run["finding_id"] is not None
        assert len(skill_run["evidence_packets"]) == 1

        packet = skill_run["evidence_packets"][0]
        assert packet["actor_context"] == ActorContext.USER_A.value
        assert packet["response_status"] == 201
        assert packet["skill_id"] == ReviewSkillId.BASKET_AND_CHECKOUT
        assert "Bearer" not in str(packet)

        detail = client.get(f"/api/scans/{run_id}").json()
        business_findings = [
            finding for finding in detail["findings"] if finding["source"] == "Business Logic"
        ]
        assert len(business_findings) == 1

        finding_detail = client.get(
            f"/api/scans/{run_id}/findings/{business_findings[0]['id']}"
        ).json()
        assert finding_detail["business_logic"] is not None
        assert (
            finding_detail["business_logic"]["skill_id"]
            == ReviewSkillId.BASKET_AND_CHECKOUT
        )
    finally:
        target_factory.clear_target_client()


def test_run_basket_and_checkout_skill_stores_inconclusive_outcome_without_finding(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            checkout_manipulation_accepted=False,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.BASKET_AND_CHECKOUT}/run"
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
    finally:
        target_factory.clear_target_client()
