from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.actor_context import ActorContext
from app.domain.review_skill import ReviewSkillId
from app.domain.skill_run_outcome import SkillRunOutcome
from app.skills.coupon_discount import (
    evaluate_coupon_reuse_probe,
    evaluate_cross_actor_coupon_probe,
    evaluate_invalid_coupon_probe,
)
from app.skills.coupon_logic import invalid_coupon_probe_code
from app.skills.juice_shop_coupon import juice_shop_monthly_coupon, z85_encode
from app.target.mock import MockTargetClient
from app.target.types import ProbeCapture


def test_z85_encode_matches_juice_shop_monthly_shape():
    encoded = juice_shop_monthly_coupon(10, when=datetime(2026, 5, 15, tzinfo=UTC))
    assert encoded == z85_encode(b"MAY26-10")


def test_evaluate_coupon_reuse_probe_detects_increased_discount():
    first = ProbeCapture(
        scenario="Repeat valid coupon application",
        actor_context=ActorContext.USER_A,
        request_method="PUT",
        request_path="/rest/basket/10/coupon/test",
        request_headers={},
        response_status=200,
        response_headers={},
        response_body='{"discount":10}',
    )
    second = ProbeCapture(
        scenario="Repeat valid coupon application",
        actor_context=ActorContext.USER_A,
        request_method="PUT",
        request_path="/rest/basket/10/coupon/test",
        request_headers={},
        response_status=200,
        response_headers={},
        response_body='{"discount":20}',
    )

    assert evaluate_coupon_reuse_probe(first, second).supports_finding is True


def test_evaluate_coupon_reuse_probe_is_inconclusive_for_stable_discount():
    stable = ProbeCapture(
        scenario="Repeat valid coupon application",
        actor_context=ActorContext.USER_A,
        request_method="PUT",
        request_path="/rest/basket/10/coupon/test",
        request_headers={},
        response_status=200,
        response_headers={},
        response_body='{"discount":10}',
    )

    assert evaluate_coupon_reuse_probe(stable, stable).supports_finding is False


def test_evaluate_cross_actor_coupon_probe_detects_foreign_basket_discount():
    probe = ProbeCapture(
        scenario="Cross-actor coupon application",
        actor_context=ActorContext.USER_B,
        request_method="PUT",
        request_path="/rest/basket/10/coupon/test",
        request_headers={},
        response_status=200,
        response_headers={},
        response_body='{"discount":10}',
    )

    result = evaluate_cross_actor_coupon_probe(
        probe,
        actor_basket_id=20,
        other_basket_id=10,
    )
    assert result.supports_finding is True


def test_evaluate_invalid_coupon_probe_rejects_non_discount_response():
    rejected = ProbeCapture(
        scenario="Invalid coupon application",
        actor_context=ActorContext.USER_A,
        request_method="PUT",
        request_path=f"/rest/basket/10/coupon/{invalid_coupon_probe_code()}",
        request_headers={},
        response_status=404,
        response_headers={},
        response_body="Invalid coupon.",
    )

    assert evaluate_invalid_coupon_probe(rejected).supports_finding is False


def _ready_review_run(client: TestClient) -> str:
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]
    detail = client.get(f"/api/scans/{run_id}").json()
    assert detail["status"] == "Ready For Skills"
    return run_id


def test_run_coupon_skill_creates_finding_for_cross_actor_coupon_violation(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            cross_actor_coupon_violation=True,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.COUPON_AND_DISCOUNT}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["outcome"] == SkillRunOutcome.FINDING_CREATED
        assert skill_run["finding_id"] is not None
        assert len(skill_run["evidence_packets"]) == 3

        detail = client.get(f"/api/scans/{run_id}").json()
        business_findings = [
            finding
            for finding in detail["findings"]
            if finding["source"] == "Business Logic"
        ]
        assert len(business_findings) == 1
        assert business_findings[0]["category"] == "Coupon And Discount"
    finally:
        target_factory.clear_target_client()


def test_run_coupon_skill_stores_inconclusive_outcome_without_finding(
    client: TestClient,
):
    from app.target import factory as target_factory

    target_factory.set_target_client(
        MockTargetClient(
            boundary_violation=False,
            cross_actor_coupon_violation=False,
            coupon_reuse_violation=False,
            invalid_coupon_accepted=False,
        )
    )
    try:
        run_id = _ready_review_run(client)
        response = client.post(
            f"/api/scans/{run_id}/skills/{ReviewSkillId.COUPON_AND_DISCOUNT}/run"
        )

        assert response.status_code == 201
        skill_run = response.json()["skill_run"]
        assert skill_run["outcome"] == SkillRunOutcome.INCONCLUSIVE
        assert skill_run["finding_id"] is None
        assert skill_run["inconclusive_reason"]
        assert len(skill_run["evidence_packets"]) == 3

        detail = client.get(f"/api/scans/{run_id}").json()
        assert not any(
            finding["source"] == "Business Logic" for finding in detail["findings"]
        )
    finally:
        target_factory.clear_target_client()
