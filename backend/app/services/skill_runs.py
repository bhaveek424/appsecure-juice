from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.review_run_status import ReviewRunStatus
from app.domain.review_skill import ReviewSkillId
from app.domain.skill_run_outcome import SkillRunOutcome
from app.domain.skill_run_status import SkillRunStatus
from app.models.evidence_packet import EvidencePacket
from app.models.review_run import ReviewRun
from app.models.skill_run import SkillRun
from app.schemas.skill_runs import EvidencePacketResponse, RunSkillResponse, SkillRunResponse
from app.services.exceptions import (
    ReviewRunNotFoundError,
    ReviewRunNotReadyError,
    UnknownSkillError,
)
from app.skills.account_boundary import run_account_boundary_skill
from app.skills.basket_and_checkout import run_basket_and_checkout_skill
from app.skills.coupon_discount import run_coupon_and_discount_skill
from app.skills.review_ownership import run_review_ownership_skill
from app.target.factory import get_target_client
from app.target.types import TargetClient

_SkillRunner = Callable[[Session, ReviewRun, SkillRun, TargetClient], None]

_SKILL_HANDLERS: dict[ReviewSkillId, tuple[_SkillRunner, str]] = {
    ReviewSkillId.ACCOUNT_BOUNDARY: (
        run_account_boundary_skill,
        "Account Boundary",
    ),
    ReviewSkillId.BASKET_AND_CHECKOUT: (
        run_basket_and_checkout_skill,
        "Basket And Checkout",
    ),
    ReviewSkillId.REVIEW_OWNERSHIP: (
        run_review_ownership_skill,
        "Review Ownership",
    ),
    ReviewSkillId.COUPON_AND_DISCOUNT: (
        run_coupon_and_discount_skill,
        "Coupon And Discount",
    ),
}


def _to_evidence_response(packet: EvidencePacket) -> EvidencePacketResponse:
    return EvidencePacketResponse.model_validate(packet)


def _to_skill_run_response(
    db: Session, skill_run: SkillRun
) -> SkillRunResponse:
    packets = db.scalars(
        select(EvidencePacket).where(EvidencePacket.skill_run_id == skill_run.id)
    ).all()
    return SkillRunResponse(
        id=skill_run.id,
        skill_id=skill_run.skill_id,
        status=skill_run.status,
        outcome=skill_run.outcome,
        summary=skill_run.summary,
        inconclusive_reason=skill_run.inconclusive_reason,
        finding_id=skill_run.finding_id,
        started_at=skill_run.started_at,
        completed_at=skill_run.completed_at,
        evidence_packets=[_to_evidence_response(packet) for packet in packets],
    )


def list_skill_runs_for_run(db: Session, review_run_id: str) -> list[SkillRunResponse]:
    runs = db.scalars(
        select(SkillRun)
        .where(SkillRun.review_run_id == review_run_id)
        .order_by(SkillRun.started_at.desc())
    ).all()
    return [_to_skill_run_response(db, run) for run in runs]


def run_review_skill(
    db: Session, review_run_id: str, skill_id: str
) -> RunSkillResponse:
    review_run = db.get(ReviewRun, review_run_id)
    if review_run is None:
        raise ReviewRunNotFoundError

    if review_run.status != ReviewRunStatus.READY_FOR_SKILLS:
        raise ReviewRunNotReadyError

    try:
        skill = ReviewSkillId(skill_id)
    except ValueError as exc:
        raise UnknownSkillError from exc

    handler = _SKILL_HANDLERS.get(skill)
    if handler is None:
        raise UnknownSkillError

    run_skill, skill_label = handler
    skill_run = SkillRun(
        review_run_id=review_run_id,
        skill_id=skill_id,
        status=SkillRunStatus.RUNNING,
        summary=f"Running {skill_label} Skill",
    )
    db.add(skill_run)
    review_run.status = ReviewRunStatus.PROBING
    review_run.current_step = f"Running {skill_label} Skill"
    db.commit()
    db.refresh(skill_run)

    target_client = get_target_client()
    try:
        run_skill(db, review_run, skill_run, target_client)
        if skill_run.finding_id:
            skill_run.outcome = SkillRunOutcome.FINDING_CREATED
        else:
            skill_run.outcome = SkillRunOutcome.INCONCLUSIVE
            skill_run.inconclusive_reason = skill_run.summary
        skill_run.status = SkillRunStatus.COMPLETED
        review_run.status = ReviewRunStatus.READY_FOR_SKILLS
        review_run.current_step = f"{skill_label} Skill complete"
    except Exception:
        skill_run.status = SkillRunStatus.FAILED
        skill_run.outcome = SkillRunOutcome.FAILED
        skill_run.summary = f"{skill_label} Skill failed"
        review_run.status = ReviewRunStatus.READY_FOR_SKILLS
        review_run.current_step = f"{skill_label} Skill failed"
        skill_run.completed_at = datetime.now(UTC)
        db.commit()
        raise

    skill_run.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(skill_run)
    return RunSkillResponse(skill_run=_to_skill_run_response(db, skill_run))
