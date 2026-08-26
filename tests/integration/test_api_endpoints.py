import pytest
from fastapi.testclient import TestClient
from database.connection import init_db, SessionLocal
from database.seeds.seed_data import seed_database
from apps.backend.src.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "uptime_seconds" in data

def test_system_status_endpoint():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "hardware" in data
    assert "providers" in data
    assert len(data["providers"]) >= 2
    # Verify FortyGuard provider exists and shows valid status
    fg_prov = next(p for p in data["providers"] if "FortyGuard" in p["provider_name"])
    assert fg_prov["status"] in ("CONNECTED", "DISCONNECTED", "NOT_CONFIGURED", "ERROR")

def test_locations_and_temperature():
    loc_resp = client.get("/api/v1/locations")
    assert loc_resp.status_code == 200
    locs = loc_resp.json()
    assert len(locs) >= 1

    temp_resp = client.get("/api/v1/temperature/current")
    assert temp_resp.status_code == 200
    temps = temp_resp.json()
    assert len(temps) >= 1

def test_forecast_endpoint():
    response = client.get("/api/v1/forecast")
    assert response.status_code == 200
    data = response.json()
    assert "series" in data
    assert len(data["series"]) >= 5

def test_copilot_grounded_query():
    response = client.post("/api/v1/copilot/query", json={"query": "What are the highest risk events today?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "grounded_data" in data
    assert "sources_used" in data

def test_reports_export_json_and_csv():
    json_resp = client.get("/api/v1/reports/export?format=json")
    assert json_resp.status_code == 200
    assert "platform" in json_resp.json()

    csv_resp = client.get("/api/v1/reports/export?format=csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
