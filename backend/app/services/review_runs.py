from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session_factory
from app.domain.review_run_status import ReviewRunStatus
from app.domain.target import normalize_target
from app.models.review_run import ReviewRun
from app.schemas.scans import FindingCounts, ScanDetail, ScanSummary
from app.services.exceptions import ReviewRunNotFoundError
from app.services.findings import finding_counts_for_run, list_findings_for_run
from app.services.hypotheses import list_hypotheses_for_run
from app.services.skill_runs import list_skill_runs_for_run
from app.services.zap_scan import execute_zap_scan
from app.zap.factory import get_zap_client


class TargetNotAllowedError(Exception):
    pass


class ActiveReviewRunExistsError(Exception):
    def __init__(self, active_run_id: str):
        self.active_run_id = active_run_id
        super().__init__("A Review Run is already active")


def _configured_target(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return normalize_target(settings.target_application_url)


def _resolve_target(target: str | None) -> str:
    configured = _configured_target()
    if target is None:
        return configured

    normalized = normalize_target(target)
    if normalized != configured:
        raise TargetNotAllowedError
    return normalized


def _to_summary(db: Session, review_run: ReviewRun) -> ScanSummary:
    return ScanSummary(
        id=review_run.id,
        status=review_run.status,
        started_at=review_run.started_at,
        completed_at=review_run.completed_at,
        current_step=review_run.current_step,
        finding_counts=finding_counts_for_run(db, review_run.id),
    )


def _to_detail(db: Session, review_run: ReviewRun) -> ScanDetail:
    return ScanDetail(
        id=review_run.id,
        status=review_run.status,
        progress=review_run.progress,
        current_step=review_run.current_step,
        findings=list_findings_for_run(db, review_run.id),
        hypotheses=list_hypotheses_for_run(db, review_run.id),
        skill_runs=list_skill_runs_for_run(db, review_run.id),
    )


def find_active_review_run(db: Session) -> ReviewRun | None:
    statement = select(ReviewRun).where(ReviewRun.is_active.is_(True))
    return db.scalars(statement).first()


def create_review_run(db: Session, *, target: str | None = None) -> ReviewRun:
    normalized_target = _resolve_target(target)

    review_run = ReviewRun(
        target_url=normalized_target,
        status=ReviewRunStatus.QUEUED,
        current_step="Queued",
        is_active=True,
    )
    db.add(review_run)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        active = find_active_review_run(db)
        if active is None:
            raise exc
        raise ActiveReviewRunExistsError(active.id) from exc

    db.refresh(review_run)
    return review_run


def enqueue_zap_scan(review_run_id: str) -> None:
    db = get_session_factory()()
    try:
        execute_zap_scan(db, review_run_id, get_zap_client())
    finally:
        db.close()


def list_review_runs(db: Session) -> list[ScanSummary]:
    statement = select(ReviewRun).order_by(ReviewRun.started_at.desc())
    runs = db.scalars(statement).all()
    return [_to_summary(db, run) for run in runs]


def get_review_run(db: Session, review_run_id: str) -> ScanDetail:
    review_run = db.get(ReviewRun, review_run_id)
    if review_run is None:
        raise ReviewRunNotFoundError
    return _to_detail(db, review_run)
