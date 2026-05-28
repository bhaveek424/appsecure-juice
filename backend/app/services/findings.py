from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.review_disposition import ReviewDisposition
from app.domain.severity import SEVERITY_SORT_ORDER, Severity
from app.models.evidence_packet import EvidencePacket
from app.models.finding import Finding
from app.schemas.findings import (
    BusinessLogicEvidenceDetail,
    DispositionResponse,
    FindingDetail,
    FindingResponse,
    ScannerFindingDetail,
)
from app.schemas.scans import FindingCounts


class FindingNotFoundError(Exception):
    pass


class InvalidDispositionError(Exception):
    pass


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
                disposition=ReviewDisposition.UNREVIEWED,
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


def _to_response(finding: Finding) -> FindingResponse:
    return FindingResponse.model_validate(finding)


def _business_logic_detail(
    db: Session, finding: Finding
) -> BusinessLogicEvidenceDetail | None:
    if finding.source != "Business Logic":
        return None

    packet = db.scalars(
        select(EvidencePacket).where(EvidencePacket.finding_id == finding.id)
    ).first()
    if packet is None:
        return None

    return BusinessLogicEvidenceDetail(
        skill_id=packet.skill_id,
        scenario=packet.scenario,
        actor_context=packet.actor_context,
        expected_behavior=packet.expected_behavior,
        observed_behavior=packet.observed_behavior,
        request_method=packet.request_method,
        request_path=packet.request_path,
        response_status=packet.response_status,
        response_excerpt=packet.response_excerpt,
        reasoning_summary=packet.reasoning_summary,
        captured_at=packet.captured_at,
    )


def _scanner_detail(finding: Finding) -> ScannerFindingDetail | None:
    if finding.source != "Scanner":
        return None
    return ScannerFindingDetail(
        alert=finding.category,
        description=finding.description,
        remediation=finding.remediation,
        confidence=finding.confidence,
        evidence_excerpt=finding.evidence_excerpt,
    )


def _to_detail(db: Session, finding: Finding) -> FindingDetail:
    response = _to_response(finding)
    return FindingDetail(
        **response.model_dump(),
        review_run_id=finding.review_run_id,
        scanner=_scanner_detail(finding),
        business_logic=_business_logic_detail(db, finding),
    )


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
    return [_to_response(finding) for finding in sorted_findings]


def get_finding_for_run(
    db: Session, review_run_id: str, finding_id: str
) -> FindingDetail:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.review_run_id != review_run_id:
        raise FindingNotFoundError
    return _to_detail(db, finding)


def get_finding(db: Session, finding_id: str) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise FindingNotFoundError
    return finding


def update_disposition(
    db: Session, finding_id: str, disposition: ReviewDisposition
) -> DispositionResponse:
    if disposition.value not in ReviewDisposition.values():
        raise InvalidDispositionError

    finding = get_finding(db, finding_id)
    finding.disposition = disposition.value
    db.commit()
    db.refresh(finding)
    return DispositionResponse(id=finding.id, disposition=finding.disposition)
