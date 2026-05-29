from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.review_run_status import ReviewRunStatus
from app.models.finding import Finding
from app.models.review_run import ReviewRun
from app.reasoning.factory import get_reasoning_client
from app.reasoning.mock import MockReasoningClient
from app.reasoning.sanitize import sanitize_findings_as_observations
from app.reasoning.types import SanitizedObservation, TriageHypothesisResult
from app.services.cancellation import ensure_not_cancelled
from app.services.exceptions import ReviewRunCancelledError
from app.services.hypotheses import persist_hypotheses


def execute_agent_triage(db: Session, review_run_id: str) -> None:
    review_run = db.get(ReviewRun, review_run_id)
    if review_run is None:
        return

    ensure_not_cancelled(db, review_run_id)

    review_run.status = ReviewRunStatus.TRIAGING
    review_run.current_step = "Running Agent Triage"
    db.commit()

    findings = list(
        db.scalars(
            select(Finding).where(Finding.review_run_id == review_run_id)
        ).all()
    )
    observations = sanitize_findings_as_observations(findings)

    try:
        ensure_not_cancelled(db, review_run_id)
        completion_step, triage_results = _run_triage(observations)
    except ReviewRunCancelledError:
        raise
    except Exception:
        _mark_triage_failed(db, review_run)
        raise

    ensure_not_cancelled(db, review_run_id)
    persist_hypotheses(db, review_run_id, triage_results)
    review_run.status = ReviewRunStatus.READY_FOR_SKILLS
    review_run.current_step = completion_step
    review_run.progress = 1.0
    db.commit()


def _run_triage(
    observations: list[SanitizedObservation],
) -> tuple[str, list[TriageHypothesisResult]]:
    primary = get_reasoning_client()
    try:
        return "Agent triage complete", primary.triage(observations)
    except Exception:
        if isinstance(primary, MockReasoningClient):
            raise
        return (
            "Agent triage complete (mock fallback)",
            MockReasoningClient().triage(observations),
        )


def _mark_triage_failed(db: Session, review_run: ReviewRun) -> None:
    review_run.status = ReviewRunStatus.FAILED
    review_run.current_step = "Agent triage failed"
    review_run.is_active = False
    review_run.completed_at = datetime.now(UTC)
    review_run.progress = None
    db.commit()
