from app.models.finding import Finding
from app.reasoning.types import SanitizedObservation


def sanitize_findings_as_observations(
    findings: list[Finding],
) -> list[SanitizedObservation]:
    return [
        SanitizedObservation(
            finding_id=finding.id,
            title=finding.title,
            severity=finding.severity,
            category=finding.category,
            endpoint=finding.endpoint,
            source=finding.source,
        )
        for finding in findings
    ]
