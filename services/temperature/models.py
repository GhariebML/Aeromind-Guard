from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TemperatureObservation(BaseModel):
    """Normalized internal model for temperature readings from any provider."""
    location: str = Field(..., description="Location identifier (e.g., coordinates or logical name)")
    temperature: float = Field(..., description="Temperature value in Celsius")
    risk_level: Optional[float] = Field(None, description="Risk level directly from provider if available")
    resolution: Optional[str] = Field(None, description="Resolution metadata if provided")
    measured_at: datetime = Field(..., description="Timestamp of the actual measurement")
    timestamp: datetime = Field(..., description="Timestamp of when the data was ingested")
    provider: str = Field(..., description="Provider identifier (e.g., FORTYGUARD, DEMO)")
