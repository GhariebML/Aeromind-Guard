import pytest
import httpx
from datetime import datetime, timezone
from services.temperature.fortyguard_client import FortyGuardProvider
from services.temperature.provider import ProviderStatus

# Mock settings to avoid using real API key in tests
@pytest.fixture
def fortyguard_provider(monkeypatch):
    monkeypatch.setenv("FORTYGUARD_API_KEY", "test-key")
    provider = FortyGuardProvider()
    provider.api_key = "test-key"
    provider.max_retries = 1
    return provider

@pytest.mark.asyncio
async def test_fortyguard_health_connected(fortyguard_provider, monkeypatch):
    class MockResponse:
        status_code = 200
        
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    status = await fortyguard_provider.get_status()
    assert status == ProviderStatus.CONNECTED

@pytest.mark.asyncio
async def test_fortyguard_health_auth_error(fortyguard_provider, monkeypatch):
    class MockResponse:
        status_code = 401
        
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    status = await fortyguard_provider.get_status()
    assert status == ProviderStatus.AUTHENTICATION_ERROR

@pytest.mark.asyncio
async def test_fortyguard_fetch_valid_response(fortyguard_provider, monkeypatch):
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "temperature": 32.5,
                "risk_level": 15.0,
                "resolution": "100m"
            }
            
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    obs = await fortyguard_provider.fetch_temperature("Dubai")
    assert obs is not None
    assert obs.temperature == 32.5
    assert obs.risk_level == 15.0
    assert obs.provider == "FORTYGUARD"
    assert obs.location == "Dubai"

@pytest.mark.asyncio
async def test_fortyguard_fetch_rate_limit(fortyguard_provider, monkeypatch):
    class MockResponse:
        status_code = 429
        headers = {"Retry-After": "0.1"}
        
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    obs = await fortyguard_provider.fetch_temperature("Dubai")
    assert obs is None  # Fails after retries exhaust

@pytest.mark.asyncio
async def test_fortyguard_unconfigured():
    provider = FortyGuardProvider()
    provider.api_key = ""
    status = await provider.get_status()
    assert status == ProviderStatus.NOT_CONFIGURED
