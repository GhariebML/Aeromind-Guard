from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

class ProviderStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"

class EnvironmentalDataProvider(ABC):
    """
    Abstract base provider for environmental and meteorological data ingestion.
    Designed for FortyGuard, Open-Meteo, IoT Sensors, and Synthetic Demonstration feeds.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the unique provider identifier."""
        pass

    @abstractmethod
    async def get_status(self) -> ProviderStatus:
        """Checks API readiness, connectivity and authentication status."""
        pass

    @abstractmethod
    async def fetch_current_readings(self, latitude: float, longitude: float, location_id: str) -> List[Dict[str, Any]]:
        """
        Fetches normalized real-time readings:
        Returns list of dicts with: metric, value, unit, quality, timestamp, metadata
        """
        pass

    @abstractmethod
    async def fetch_forecast(self, latitude: float, longitude: float, location_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Fetches temperature and environmental forecast points.
        """
        pass
