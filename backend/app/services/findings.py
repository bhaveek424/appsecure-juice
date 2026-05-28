from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.severity import SEVERITY_SORT_ORDER, Severity
from app.models.finding import Finding
from app.schemas.findings import FindingResponse
from app.schemas.scans import FindingCounts


def persist_scanner_findings(
    db: Session,
    review_run_id: str,
    normalized_findings: list[dict[str, Any]],
) -> None:
    for payload in normalized_findings:
        db.add(
            Finding(
                review_run_id=review_run_id,
                source=payload["source"],
                title=payload["title"],
                category=payload["category"],
                severity=payload["severity"],
                endpoint=payload["endpoint"],
                description=payload["description"],
                remediation=payload["remediation"],
                confidence=payload["confidence"],
                evidence_excerpt=payload["evidence_excerpt"],
                discovered_at=payload["discovered_at"],
            )
        )


def finding_counts_for_run(db: Session, review_run_id: str) -> FindingCounts:
    rows = db.execute(
        select(Finding.severity, func.count())
        .where(Finding.review_run_id == review_run_id)
        .group_by(Finding.severity)
    ).all()
    counts = FindingCounts()
    for severity, count in rows:
        match severity:
            case Severity.CRITICAL:
                counts.critical = count
            case Severity.HIGH:
                counts.high = count
            case Severity.MEDIUM:
                counts.medium = count
            case Severity.LOW:
                counts.low = count
            case Severity.INFORMATIONAL:
                counts.informational = count
    return counts


def list_findings_for_run(db: Session, review_run_id: str) -> list[FindingResponse]:
    findings = db.scalars(
        select(Finding)
        .where(Finding.review_run_id == review_run_id)
        .order_by(Finding.discovered_at.desc())
    ).all()
    sorted_findings = sorted(
        findings,
        key=lambda finding: (
            SEVERITY_SORT_ORDER.get(finding.severity, 99),
            finding.title.lower(),
        ),
    )
    return [FindingResponse.model_validate(finding) for finding in sorted_findings]
