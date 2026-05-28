from datetime import datetime
from typing import Any

from app.domain.severity import Severity


def map_zap_risk(alert: dict[str, Any]) -> str:
    riskcode = str(alert.get("riskcode", "")).strip()
    risk = str(alert.get("risk", "")).strip().lower()

    mapping_by_code = {
        "4": Severity.CRITICAL,
        "3": Severity.HIGH,
        "2": Severity.MEDIUM,
        "1": Severity.LOW,
        "0": Severity.INFORMATIONAL,
    }
    if riskcode in mapping_by_code:
        return mapping_by_code[riskcode]

    mapping_by_name = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "informational": Severity.INFORMATIONAL,
        "info": Severity.INFORMATIONAL,
    }
    return mapping_by_name.get(risk, Severity.INFORMATIONAL)


def normalize_zap_alert(
    alert: dict[str, Any],
    *,
    discovered_at: datetime,
) -> dict[str, Any]:
    title = alert.get("name") or alert.get("alert") or "Untitled scanner finding"
    category = alert.get("alert") or alert.get("pluginId") or "General"

    return {
        "source": "Scanner",
        "title": str(title),
        "category": str(category),
        "severity": map_zap_risk(alert),
        "endpoint": str(alert.get("url") or ""),
        "description": str(alert.get("desc") or alert.get("description") or ""),
        "remediation": str(alert.get("solution") or ""),
        "confidence": str(alert.get("confidence") or "") or None,
        "evidence_excerpt": str(alert.get("evidence") or "") or None,
        "discovered_at": discovered_at,
    }
