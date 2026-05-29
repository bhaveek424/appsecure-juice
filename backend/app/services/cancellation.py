from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.review_run_status import ReviewRunStatus
from app.models.review_run import ReviewRun
from app.schemas.scans import ScanSummary
from app.services.exceptions import (
    ReviewRunCancelledError,
    ReviewRunNotCancellableError,
    ReviewRunNotFoundError,
)
from app.services.findings import finding_counts_for_run
from app.zap.factory import get_zap_client

_TERMINAL_STATUSES = frozenset(
    {
        ReviewRunStatus.COMPLETED,
        ReviewRunStatus.FAILED,
        ReviewRunStatus.CANCELLED,
    }
)


def review_run_is_cancelled(db: Session, review_run_id: str) -> bool:
    status = db.execute(
        text("SELECT status FROM review_runs WHERE id = :review_run_id"),
        {"review_run_id": review_run_id},
    ).scalar_one_or_none()
    return status == ReviewRunStatus.CANCELLED


def ensure_not_cancelled(db: Session, review_run_id: str) -> None:
    if review_run_is_cancelled(db, review_run_id):
        raise ReviewRunCancelledError()


def cancel_review_run(db: Session, review_run_id: str) -> ScanSummary:
    review_run = db.get(ReviewRun, review_run_id)
    if review_run is None:
        raise ReviewRunNotFoundError

    if review_run.status in _TERMINAL_STATUSES:
        raise ReviewRunNotCancellableError

    try:
        get_zap_client().stop_active_scans()
    except Exception:
        pass

    review_run.status = ReviewRunStatus.CANCELLED
    review_run.current_step = "Review Run cancelled"
    review_run.is_active = False
    review_run.completed_at = datetime.now(UTC)
    review_run.progress = None
    db.commit()
    db.refresh(review_run)
    return ScanSummary(
        id=review_run.id,
        status=review_run.status,
        started_at=review_run.started_at,
        completed_at=review_run.completed_at,
        current_step=review_run.current_step,
        finding_counts=finding_counts_for_run(db, review_run.id),
    )
