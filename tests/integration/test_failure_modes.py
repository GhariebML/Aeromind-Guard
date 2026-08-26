import pytest
from fastapi.testclient import TestClient
from apps.backend.src.main import app
from services.ingestion.fortyguard import FortyGuardProvider, ProviderStatus
from services.copilot.agent import AeroMindCopilot

client = TestClient(app)

@pytest.mark.asyncio
async def test_fortyguard_unconfigured_graceful_handling():
    # Unconfigured provider must never throw exception
    provider = FortyGuardProvider(api_key=None)
    assert provider.is_configured() is False
    status = await provider.get_status()
    assert status == ProviderStatus.NOT_CONFIGURED

@pytest.mark.asyncio
async def test_copilot_ollama_offline_graceful_fallback():
    copilot = AeroMindCopilot(ollama_url="http://127.0.0.1:99999")  # Dead port
    is_online = await copilot.check_ollama_status()
    assert is_online is False

    grounded_context = {
        "locations": [{"name": "BESS-01"}],
        "alerts": [{"severity": "CRITICAL", "title": "Heat Spike", "message": "High temp", "status": "OPEN"}],
        "risk_assessments": [{"location_name": "BESS-01", "overall_score": 85.0, "severity": "CRITICAL"}],
        "anomalies": [],
        "visual_hazards": []
    }

    result = await copilot.query("What are the highest risk events today?", grounded_data=grounded_context)
    assert result["is_llm_active"] is False
    assert "85.0" in result["answer"]
    assert "BESS-01" in result["answer"]

def test_invalid_alert_id_not_found():
    response = client.post("/api/v1/alerts/non-existent-id/acknowledge", json={"operator_name": "Sarah"})
    assert response.status_code == 404
    assert "Alert not found" in response.json()["detail"]

def test_invalid_video_job_id_not_found():
    response = client.get("/api/v1/video/jobs/fake-uuid-0000")
    assert response.status_code == 404
