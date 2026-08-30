from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from datetime import datetime, timezone
import random
from services.temperature.models import TemperatureObservation

class ProviderStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"

class TemperatureProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_status(self) -> ProviderStatus:
        pass

    @abstractmethod
    async def fetch_temperature(self, location: str) -> Optional[TemperatureObservation]:
        pass

class LocalDemoProvider(TemperatureProvider):
    @property
    def provider_name(self) -> str:
        return "DEMO"
        
    async def get_status(self) -> ProviderStatus:
        return ProviderStatus.CONNECTED
        
    async def fetch_temperature(self, location: str) -> Optional[TemperatureObservation]:
        now = datetime.now(timezone.utc)
        base_temp = 25.0
        random_variance = random.uniform(-5.0, 15.0)
        temp = base_temp + random_variance
        
        return TemperatureObservation(
            location=location,
            temperature=round(temp, 2),
            risk_level=round(temp / 50.0 * 100, 2),  # Fake risk based on temp
            resolution="DEMO_RESOLUTION",
            measured_at=now,
            timestamp=now,
            provider=self.provider_name
        )
