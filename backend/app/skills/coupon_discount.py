from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.actor_context import ActorContext
from app.domain.review_skill import REVIEW_SKILL_NAMES, ReviewSkillId
from app.domain.severity import Severity
from app.evidence.sanitizer import sanitize_probe_capture
from app.models.evidence_packet import EvidencePacket
from app.models.finding import Finding
from app.models.review_run import ReviewRun
from app.models.skill_run import SkillRun
from app.services.actors import ensure_review_run_actors
from app.services.cancellation import ensure_not_cancelled
from app.skills.coupon_logic import (
    coupon_reuse_violation_detected,
    cross_actor_coupon_violation_detected,
    invalid_coupon_accepted_detected,
    invalid_coupon_probe_code,
)
from app.skills.juice_shop_coupon import juice_shop_monthly_coupon
from app.target.types import ProbeCapture, TargetClient


@dataclass(frozen=True)
class CouponScenarioEvaluation:
    supports_finding: bool
    probe: ProbeCapture
    expected_behavior: str
    observed_behavior: str
    reasoning_summary: str
    inconclusive_reason: str | None = None
    finding_title: str | None = None
    finding_description: str | None = None
    remediation: str | None = None


def _observed_behavior(probe: ProbeCapture) -> str:
    return (
        f"{probe.actor_context.value} received HTTP {probe.response_status} "
        f"for {probe.request_method} {probe.request_path}."
    )


def evaluate_coupon_reuse_probe(
    first_probe: ProbeCapture,
    second_probe: ProbeCapture,
) -> CouponScenarioEvaluation:
    expected = (
        "Re-applying the same coupon must not increase the basket discount."
    )
    observed = (
        f"First apply: {_observed_behavior(first_probe)} "
        f"Second apply: {_observed_behavior(second_probe)}"
    )
    if coupon_reuse_violation_detected(first_probe, second_probe):
        return CouponScenarioEvaluation(
            supports_finding=True,
            probe=second_probe,
            expected_behavior=expected,
            observed_behavior=observed,
            reasoning_summary=(
                "The server increased the discount when the same coupon was "
                "applied twice, which indicates missing reuse enforcement."
            ),
            finding_title="Coupon reuse increases discount",
            finding_description=(
                "The application accepted the same coupon again and returned "
                "a higher discount than the first application."
            ),
            remediation=(
                "Track redeemed coupons per basket or user and reject repeat "
                "applications that would stack promotional discounts."
            ),
        )

    return CouponScenarioEvaluation(
        supports_finding=False,
        probe=second_probe,
        expected_behavior=expected,
        observed_behavior=observed,
        reasoning_summary=(
            "The second coupon application did not show a clear reuse abuse signal."
        ),
        inconclusive_reason=(
            "Coupon reuse did not produce an increased discount in observed responses."
        ),
    )


def evaluate_cross_actor_coupon_probe(
    probe: ProbeCapture,
    *,
    actor_basket_id: int,
    other_basket_id: int,
) -> CouponScenarioEvaluation:
    expected = (
        "User B must not apply coupons to User A basket."
    )
    observed = _observed_behavior(probe)
    if cross_actor_coupon_violation_detected(
        probe,
        actor_basket_id=actor_basket_id,
        other_basket_id=other_basket_id,
    ):
        return CouponScenarioEvaluation(
            supports_finding=True,
            probe=probe,
            expected_behavior=expected,
            observed_behavior=observed,
            reasoning_summary=(
                "The server applied a discount coupon to another user's basket."
            ),
            finding_title="Cross-actor coupon application allowed",
            finding_description=(
                "User B could apply a coupon to User A's basket and received "
                "a successful discount response."
            ),
            remediation=(
                "Bind coupon application to the authenticated user's basket and "
                "reject cross-account basket identifiers."
            ),
        )

    return CouponScenarioEvaluation(
        supports_finding=False,
        probe=probe,
        expected_behavior=expected,
        observed_behavior=observed,
        reasoning_summary=(
            "The cross-actor coupon probe did not show an unauthorized discount."
        ),
        inconclusive_reason=(
            "Server rejected or did not discount another user's basket."
        ),
    )


def evaluate_invalid_coupon_probe(probe: ProbeCapture) -> CouponScenarioEvaluation:
    expected = "Known-invalid coupon codes must be rejected without a discount."
    observed = _observed_behavior(probe)
    if invalid_coupon_accepted_detected(probe):
        return CouponScenarioEvaluation(
            supports_finding=True,
            probe=probe,
            expected_behavior=expected,
            observed_behavior=observed,
            reasoning_summary=(
                "The server returned a discount for a deterministic invalid coupon probe."
            ),
            finding_title="Invalid coupon accepted",
            finding_description=(
                "A clearly invalid coupon code received a successful discount response."
            ),
            remediation=(
                "Validate coupon codes server-side and return an error when the "
                "code is unknown or expired."
            ),
        )

    return CouponScenarioEvaluation(
        supports_finding=False,
        probe=probe,
        expected_behavior=expected,
        observed_behavior=observed,
        reasoning_summary=(
            "The invalid coupon probe was rejected or did not return a discount."
        ),
        inconclusive_reason="Invalid coupon probe was rejected as expected.",
    )


def _persist_evidence(
    db: Session,
    skill_run: SkillRun,
    evaluation: CouponScenarioEvaluation,
) -> EvidencePacket:
    sanitized = sanitize_probe_capture(evaluation.probe.to_dict())
    response_excerpt = sanitized["response_body"][:500]
    evidence = EvidencePacket(
        skill_run_id=skill_run.id,
        skill_id=ReviewSkillId.COUPON_AND_DISCOUNT,
        scenario=evaluation.probe.scenario,
        actor_context=evaluation.probe.actor_context.value,
        expected_behavior=evaluation.expected_behavior,
        observed_behavior=evaluation.observed_behavior,
        request_method=evaluation.probe.request_method,
        request_path=evaluation.probe.request_path,
        response_status=evaluation.probe.response_status,
        response_excerpt=response_excerpt,
        reasoning_summary=evaluation.reasoning_summary,
        captured_at=datetime.now(UTC),
    )
    db.add(evidence)
    return evidence


def run_coupon_and_discount_skill(
    db: Session,
    review_run: ReviewRun,
    skill_run: SkillRun,
    target_client: TargetClient,
) -> None:
    actors = ensure_review_run_actors(db, review_run.id, target_client)
    ensure_not_cancelled(db, review_run.id)
    user_a = target_client.login(
        actors[ActorContext.USER_A].email,
        actors[ActorContext.USER_A].password,
        ActorContext.USER_A,
    )
    user_b = target_client.login(
        actors[ActorContext.USER_B].email,
        actors[ActorContext.USER_B].password,
        ActorContext.USER_B,
    )

    valid_coupon = juice_shop_monthly_coupon(10)
    invalid_coupon = invalid_coupon_probe_code()

    first_apply = target_client.probe_apply_coupon(
        user_a,
        user_a.basket_id,
        valid_coupon,
        scenario="Initial valid coupon application",
    )
    ensure_not_cancelled(db, review_run.id)
    second_apply = target_client.probe_apply_coupon(
        user_a,
        user_a.basket_id,
        valid_coupon,
        scenario="Repeat valid coupon application",
    )
    ensure_not_cancelled(db, review_run.id)
    cross_actor_apply = target_client.probe_apply_coupon(
        user_b,
        user_a.basket_id,
        valid_coupon,
        scenario="Cross-actor coupon application",
    )
    ensure_not_cancelled(db, review_run.id)
    invalid_apply = target_client.probe_apply_coupon(
        user_a,
        user_a.basket_id,
        invalid_coupon,
        scenario="Invalid coupon application",
    )
    ensure_not_cancelled(db, review_run.id)

    ensure_not_cancelled(db, review_run.id)
    evaluations = [
        evaluate_coupon_reuse_probe(first_apply, second_apply),
        evaluate_cross_actor_coupon_probe(
            cross_actor_apply,
            actor_basket_id=user_b.basket_id,
            other_basket_id=user_a.basket_id,
        ),
        evaluate_invalid_coupon_probe(invalid_apply),
    ]

    primary_finding: CouponScenarioEvaluation | None = None
    inconclusive_reasons: list[str] = []
    evidence_by_evaluation: list[tuple[EvidencePacket, CouponScenarioEvaluation]] = []

    for evaluation in evaluations:
        evidence = _persist_evidence(db, skill_run, evaluation)
        evidence_by_evaluation.append((evidence, evaluation))
        if evaluation.supports_finding and primary_finding is None:
            primary_finding = evaluation
        elif evaluation.inconclusive_reason:
            inconclusive_reasons.append(evaluation.inconclusive_reason)

    if primary_finding is not None:
        sanitized = sanitize_probe_capture(primary_finding.probe.to_dict())
        response_excerpt = sanitized["response_body"][:500]
        finding = Finding(
            review_run_id=review_run.id,
            source="Business Logic",
            title=primary_finding.finding_title or "Coupon discount logic issue",
            category=REVIEW_SKILL_NAMES[ReviewSkillId.COUPON_AND_DISCOUNT],
            severity=Severity.HIGH,
            endpoint=primary_finding.probe.request_path,
            description=primary_finding.finding_description
            or primary_finding.reasoning_summary,
            remediation=primary_finding.remediation or "",
            confidence="High",
            evidence_excerpt=response_excerpt,
            discovered_at=datetime.now(UTC),
        )
        db.add(finding)
        db.flush()
        for evidence, evaluation in evidence_by_evaluation:
            if evaluation is primary_finding:
                evidence.finding_id = finding.id
        skill_run.finding_id = finding.id
        skill_run.summary = (
            "Created a Business Logic Finding for a coupon discount logic issue."
        )
        return

    skill_run.summary = inconclusive_reasons[0] if inconclusive_reasons else (
        "Coupon and discount probes were inconclusive."
    )
