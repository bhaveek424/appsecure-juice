from fastapi.testclient import TestClient


def test_review_run_zap_scan_persists_normalized_findings(client: TestClient):
    created = client.post("/api/scans")
    assert created.status_code == 201
    run_id = created.json()["id"]

    detail = client.get(f"/api/scans/{run_id}").json()

    assert detail["status"] == "Ready For Skills"
    assert detail["current_step"] == "ZAP scan complete"
    assert detail["progress"] == 1.0
    assert len(detail["findings"]) == 1

    finding = detail["findings"][0]
    assert finding["source"] == "Scanner"
    assert finding["severity"] == "High"
    assert finding["title"] == "Cross Site Scripting"
    assert "riskcode" not in finding
    assert "pluginId" not in finding

    summary = client.get("/api/scans").json()[0]
    assert summary["finding_counts"]["high"] == 1
    assert summary["finding_counts"]["critical"] == 0
