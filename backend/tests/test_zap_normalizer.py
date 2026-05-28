from datetime import datetime

from app.zap.normalizer import normalize_zap_alert


def test_normalize_zap_alert_maps_high_risk_to_high_severity():
    finding = normalize_zap_alert(
        {
            "alert": "Cross Site Scripting",
            "name": "Cross Site Scripting",
            "risk": "High",
            "riskcode": "3",
            "url": "http://juice-shop:3000/rest/track-order",
            "desc": "XSS description",
            "solution": "Validate input",
            "evidence": "<script>alert(1)</script>",
            "confidence": "Medium",
        },
        discovered_at=datetime(2026, 5, 28, 12, 0, 0),
    )

    assert finding["severity"] == "High"
    assert finding["title"] == "Cross Site Scripting"


def test_normalize_zap_alert_maps_critical_riskcode():
    finding = normalize_zap_alert(
        {"alert": "RCE", "risk": "Critical", "riskcode": "4", "url": "http://x/"},
        discovered_at=datetime(2026, 5, 28, 12, 0, 0),
    )

    assert finding["severity"] == "Critical"


def test_normalize_zap_alert_maps_informational_riskcode():
    finding = normalize_zap_alert(
        {
            "alert": "Information Disclosure",
            "risk": "Informational",
            "riskcode": "0",
            "url": "http://juice-shop:3000/",
        },
        discovered_at=datetime(2026, 5, 28, 12, 0, 0),
    )

    assert finding["severity"] == "Informational"


def test_normalize_zap_alert_returns_product_finding_shape_without_raw_zap_fields():
    raw = {
        "alert": "SQL Injection",
        "pluginId": "40018",
        "risk": "High",
        "riskcode": "3",
        "url": "http://juice-shop:3000/rest/products/search",
        "desc": "SQLi description",
        "solution": "Use parameterized queries",
        "evidence": "q=' OR 1=1--",
        "confidence": "High",
        "other": "should-not-leak",
    }
    discovered_at = datetime(2026, 5, 28, 15, 30, 0)

    finding = normalize_zap_alert(raw, discovered_at=discovered_at)

    assert finding == {
        "source": "Scanner",
        "title": "SQL Injection",
        "category": "SQL Injection",
        "severity": "High",
        "endpoint": "http://juice-shop:3000/rest/products/search",
        "description": "SQLi description",
        "remediation": "Use parameterized queries",
        "confidence": "High",
        "evidence_excerpt": "q=' OR 1=1--",
        "discovered_at": discovered_at,
    }
    assert "riskcode" not in finding
    assert "pluginId" not in finding
    assert "other" not in finding
