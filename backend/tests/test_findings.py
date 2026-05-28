from fastapi.testclient import TestClient


def _scan_with_finding(client: TestClient) -> tuple[str, str]:
    created = client.post("/api/scans")
    assert created.status_code == 201
    scan_id = created.json()["id"]
    detail = client.get(f"/api/scans/{scan_id}").json()
    finding_id = detail["findings"][0]["id"]
    return scan_id, finding_id


def test_patch_finding_disposition_persists(client: TestClient):
    scan_id, finding_id = _scan_with_finding(client)

    response = client.patch(
        f"/api/findings/{finding_id}/disposition",
        json={"disposition": "True Positive"},
    )

    assert response.status_code == 200
    assert response.json()["disposition"] == "True Positive"

    detail = client.get(f"/api/scans/{scan_id}/findings/{finding_id}").json()
    assert detail["disposition"] == "True Positive"

    listed = client.get(f"/api/scans/{scan_id}").json()["findings"]
    assert listed[0]["disposition"] == "True Positive"


def test_patch_finding_disposition_rejects_invalid_value(client: TestClient):
    _, finding_id = _scan_with_finding(client)

    response = client.patch(
        f"/api/findings/{finding_id}/disposition",
        json={"disposition": "Definitely Real"},
    )

    assert response.status_code == 422


def test_get_finding_detail_includes_scanner_metadata(client: TestClient):
    scan_id, finding_id = _scan_with_finding(client)

    detail = client.get(f"/api/scans/{scan_id}/findings/{finding_id}").json()

    assert detail["disposition"] == "Unreviewed"
    assert detail["source"] == "Scanner"
    assert detail["scanner"] is not None
    assert detail["scanner"]["alert"] == "Cross Site Scripting"
    assert detail["scanner"]["description"] == "Reflected XSS"
    assert detail["scanner"]["remediation"] == "Encode output"
    assert detail["scanner"]["confidence"] == "Medium"
    assert detail["scanner"]["evidence_excerpt"] == "<script>"
