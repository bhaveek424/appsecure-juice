from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.review_run_status import ReviewRunStatus
from app.models.finding import Finding
from app.models.review_run import ReviewRun
from app.services.agent_triage import execute_agent_triage
from app.services.findings import persist_scanner_findings
from app.zap.client import ZapClient, ZapProgress
from app.zap.normalizer import normalize_zap_alert


def execute_zap_scan(db: Session, review_run_id: str, zap_client: ZapClient) -> None:
    review_run = db.get(ReviewRun, review_run_id)
    if review_run is None:
        return

    review_run.status = ReviewRunStatus.ZAPPING
    review_run.current_step = "Starting ZAP scan"
    review_run.progress = 0.0
    db.commit()

    def on_progress(progress: ZapProgress) -> None:
        review_run.status = ReviewRunStatus.ZAPPING
        review_run.current_step = progress.current_step
        review_run.progress = progress.percent / 100.0
        db.commit()

    try:
        alerts = zap_client.run_scan(review_run.target_url, on_progress)
        discovered_at = datetime.now(UTC)
        normalized = [
            normalize_zap_alert(alert, discovered_at=discovered_at) for alert in alerts
        ]
        persist_scanner_findings(db, review_run_id, normalized)
    except Exception:
        review_run.status = ReviewRunStatus.FAILED
        review_run.current_step = "ZAP scan failed"
        review_run.is_active = False
        review_run.completed_at = datetime.now(UTC)
        review_run.progress = None
        db.commit()
        raise

    execute_agent_triage(db, review_run_id)
