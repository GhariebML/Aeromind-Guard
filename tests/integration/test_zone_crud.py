import pytest
from fastapi.testclient import TestClient
from apps.backend.src.main import app

client = TestClient(app)

def test_camera_danger_zone_crud():
    # 1. Fetch available cameras
    cams_resp = client.get("/api/v1/cameras")
    assert cams_resp.status_code == 200
    cameras = cams_resp.json()
    assert len(cameras) > 0
    camera_id = cameras[0]["id"]

    # 2. Add custom safety zone
    new_zone = {
        "name": "TEST_BATTERY_ZONE",
        "severity": "CRITICAL",
        "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]]
    }
    add_resp = client.post(f"/api/v1/video/cameras/{camera_id}/zones", json=new_zone)
    assert add_resp.status_code == 200
    assert "saved successfully" in add_resp.json()["message"]
    assert any(z["name"] == "TEST_BATTERY_ZONE" for z in add_resp.json()["danger_zones"])

    # 3. Delete custom safety zone
    del_resp = client.delete(f"/api/v1/video/cameras/{camera_id}/zones/TEST_BATTERY_ZONE")
    assert del_resp.status_code == 200
    assert "removed" in del_resp.json()["message"]
    assert not any(z["name"] == "TEST_BATTERY_ZONE" for z in del_resp.json()["danger_zones"])

def test_hse_compliance_report_endpoint():
    resp = client.get("/api/v1/reports/compliance-report")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "AeroMind ClimateGuard" in resp.text
    assert "Compliance Audit Report" in resp.text
