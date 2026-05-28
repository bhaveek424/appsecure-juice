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
from app.skills.review_ownership_boundary import (
    cross_actor_review_ownership_bypass_detected,
)
from app.target.types import ProbeCapture, TargetClient

DEFAULT_REVIEW_PRODUCT_ID = 1
USER_A_REVIEW_MESSAGE = "AppSec review ownership probe (User A)"
USER_B_TAMPER_MESSAGE = "AppSec review ownership tamper (User B)"


class ReviewOwnershipResult:
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


def evaluate_cross_actor_review_probe(
    probe: ProbeCapture, *, owner_email: str
) -> ReviewOwnershipResult:
    expected = "User B must not edit or delete User A product reviews."
    observed = (
        f"{probe.actor_context.value} received HTTP {probe.response_status} "
        f"for {probe.request_method} {probe.request_path}."
    )
    supports_finding = cross_actor_review_ownership_bypass_detected(
        probe, owner_email=owner_email
    )
    if supports_finding:
        reasoning = (
            "The server allowed User B to modify a product review owned by User A, "
            "which indicates a cross-actor review ownership failure."
        )
        return ReviewOwnershipResult(
            supports_finding=True,
            probe=probe,
            expected_behavior=expected,
            observed_behavior=observed,
            reasoning_summary=reasoning,
        )

    return ReviewOwnershipResult(
        supports_finding=False,
        probe=probe,
        expected_behavior=expected,
        observed_behavior=observed,
        reasoning_summary=(
            "The probe did not show a clear cross-actor review ownership violation."
        ),
        inconclusive_reason=(
            "Server rejected the edit or did not modify another user's review."
        ),
    )


def run_review_ownership_skill(
    db: Session,
    review_run: ReviewRun,
    skill_run: SkillRun,
    target_client: TargetClient,
) -> None:
    actors = ensure_review_run_actors(db, review_run.id, target_client)
    user_a_actor = actors[ActorContext.USER_A]
    user_b_actor = actors[ActorContext.USER_B]

    user_a = target_client.login(
        user_a_actor.email,
        user_a_actor.password,
        ActorContext.USER_A,
    )
    user_b = target_client.login(
        user_b_actor.email,
        user_b_actor.password,
        ActorContext.USER_B,
    )

    review_id = target_client.ensure_user_product_review(
        user_a,
        DEFAULT_REVIEW_PRODUCT_ID,
        USER_A_REVIEW_MESSAGE,
        user_a_actor.email,
    )
    probe = target_client.probe_cross_actor_review_edit(
        user_b,
        review_id,
        USER_B_TAMPER_MESSAGE,
    )
    evaluation = evaluate_cross_actor_review_probe(
        probe, owner_email=user_a_actor.email
    )
    sanitized = sanitize_probe_capture(probe.to_dict())
    response_excerpt = sanitized["response_body"][:500]

    evidence = EvidencePacket(
        skill_run_id=skill_run.id,
        skill_id=ReviewSkillId.REVIEW_OWNERSHIP,
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
            title="Cross-actor product review modification allowed",
            category=REVIEW_SKILL_NAMES[ReviewSkillId.REVIEW_OWNERSHIP],
            severity=Severity.HIGH,
            endpoint=probe.request_path,
            description=evaluation.reasoning_summary,
            remediation=(
                "Enforce review ownership checks so authenticated users can only "
                "edit or delete product reviews they created."
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
            "Created a Business Logic Finding for cross-actor review modification."
        )
        return

    skill_run.summary = evaluation.inconclusive_reason or "Probe was inconclusive."
