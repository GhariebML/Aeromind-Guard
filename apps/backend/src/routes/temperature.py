from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from services.temperature.provider import ProviderStatus
from services.temperature.fortyguard_client import FortyGuardProvider

router = APIRouter(prefix="/api/v1/temperature", tags=["Temperature"])
fortyguard = FortyGuardProvider()

class HealthResponse(BaseModel):
    provider: str
    connected: bool
    status: str
    last_successful_request: Optional[datetime] = None
    last_error: Optional[str] = None
    data_available: bool

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    status: str
    data_parsed: bool

@router.get("/health", response_model=HealthResponse)
async def get_health():
    status = await fortyguard.get_status()
    
    # We do NOT expose the API key or any sensitive headers here.
    return HealthResponse(
        provider=fortyguard.provider_name,
        connected=status == ProviderStatus.CONNECTED,
        status=status.value,
        data_available=status == ProviderStatus.CONNECTED
    )

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection():
    status = await fortyguard.get_status()
    if status in (ProviderStatus.AUTHENTICATION_ERROR, ProviderStatus.NOT_CONFIGURED, ProviderStatus.UNAVAILABLE):
        return TestConnectionResponse(
            success=False,
            message="Connection or authentication failed.",
            status=status.value,
            data_parsed=False
        )
        
    # Attempt a fetch to verify response parsing
    data = await fortyguard.fetch_temperature(location="Dubai")
    if data:
        return TestConnectionResponse(
            success=True,
            message="API reachable, authentication valid, and data parsed successfully.",
            status=status.value,
            data_parsed=True
        )
    
    return TestConnectionResponse(
        success=False,
        message="API reachable but failed to parse valid data.",
        status=status.value,
        data_parsed=False
    )
