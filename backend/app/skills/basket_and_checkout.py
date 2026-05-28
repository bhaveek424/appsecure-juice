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
from app.skills.basket_manipulation import negative_basket_quantity_manipulation_detected
from app.target.types import ProbeCapture, TargetClient


class BasketAndCheckoutResult:
    def __init__(
        self,
        *,
        supports_finding: bool,
        probe: ProbeCapture,
        expected_behavior: str,
        observed_behavior: str,
        reasoning_summary: str,
        inconclusive_reason: str | None = None,
    ):
        self.supports_finding = supports_finding
        self.probe = probe
        self.expected_behavior = expected_behavior
        self.observed_behavior = observed_behavior
        self.reasoning_summary = reasoning_summary
        self.inconclusive_reason = inconclusive_reason


def evaluate_negative_basket_quantity_probe(probe: ProbeCapture) -> BasketAndCheckoutResult:
    expected = "The server must reject negative basket line item quantities."
    observed = (
        f"{probe.actor_context.value} received HTTP {probe.response_status} "
        f"for {probe.request_method} {probe.request_path}."
    )
    supports_finding = negative_basket_quantity_manipulation_detected(probe)
    if supports_finding:
        reasoning = (
            "The server accepted a negative basket quantity and returned it in "
            "the response, which indicates checkout-relevant basket state can be "
            "manipulated."
        )
        return BasketAndCheckoutResult(
            supports_finding=True,
            probe=probe,
            expected_behavior=expected,
            observed_behavior=observed,
            reasoning_summary=reasoning,
        )

    return BasketAndCheckoutResult(
        supports_finding=False,
        probe=probe,
        expected_behavior=expected,
        observed_behavior=observed,
        reasoning_summary=(
            "The probe did not show the server accepting a negative basket quantity."
        ),
        inconclusive_reason=(
            "Server rejected the negative quantity or did not persist it in the response."
        ),
    )


def run_basket_and_checkout_skill(
    db: Session,
    review_run: ReviewRun,
    skill_run: SkillRun,
    target_client: TargetClient,
) -> None:
    actors = ensure_review_run_actors(db, review_run.id, target_client)
    user_a = target_client.login(
        actors[ActorContext.USER_A].email,
        actors[ActorContext.USER_A].password,
        ActorContext.USER_A,
    )

    probe = target_client.probe_negative_basket_quantity(user_a)
    evaluation = evaluate_negative_basket_quantity_probe(probe)
    sanitized = sanitize_probe_capture(probe.to_dict())
    response_excerpt = sanitized["response_body"][:500]

    evidence = EvidencePacket(
        skill_run_id=skill_run.id,
        skill_id=ReviewSkillId.BASKET_AND_CHECKOUT,
        scenario=probe.scenario,
        actor_context=probe.actor_context.value,
        expected_behavior=evaluation.expected_behavior,
        observed_behavior=evaluation.observed_behavior,
        request_method=probe.request_method,
        request_path=probe.request_path,
        response_status=probe.response_status,
        response_excerpt=response_excerpt,
        reasoning_summary=evaluation.reasoning_summary,
        captured_at=datetime.now(UTC),
    )
    db.add(evidence)

    if evaluation.supports_finding:
        finding = Finding(
            review_run_id=review_run.id,
            source="Business Logic",
            title="Negative basket quantity accepted",
            category=REVIEW_SKILL_NAMES[ReviewSkillId.BASKET_AND_CHECKOUT],
            severity=Severity.HIGH,
            endpoint=probe.request_path,
            description=evaluation.reasoning_summary,
            remediation=(
                "Validate basket line item quantities server-side and reject "
                "impossible values before checkout."
            ),
            confidence="High",
            evidence_excerpt=response_excerpt,
            discovered_at=datetime.now(UTC),
        )
        db.add(finding)
        db.flush()
        evidence.finding_id = finding.id
        skill_run.finding_id = finding.id
        skill_run.summary = (
            "Created a Business Logic Finding for negative basket quantity acceptance."
        )
        return

    skill_run.summary = evaluation.inconclusive_reason or "Probe was inconclusive."
