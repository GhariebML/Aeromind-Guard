import logging
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional

from services.temperature.provider import TemperatureProvider, ProviderStatus
from services.temperature.models import TemperatureObservation
from apps.backend.src.config import settings

logger = logging.getLogger("aeromind.fortyguard")

class FortyGuardProvider(TemperatureProvider):
    def __init__(self):
        self.api_key = settings.fortyguard_api_key
        self.base_url = settings.fortyguard_base_url.rstrip("/")
        self.timeout = settings.fortyguard_timeout
        self.max_retries = settings.fortyguard_max_retries
        self._last_status = ProviderStatus.NOT_CONFIGURED

    @property
    def provider_name(self) -> str:
        return "FORTYGUARD"
        
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "AeroMind-ClimateGuard/1.0"
        }

    async def get_status(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus.NOT_CONFIGURED
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # We assume a health endpoint exists for checking credentials
                # Or we can just check if we can make a basic request
                response = await client.get(f"{self.base_url}/health", headers=self._get_headers())
                
                if response.status_code == 200:
                    self._last_status = ProviderStatus.CONNECTED
                elif response.status_code in (401, 403):
                    self._last_status = ProviderStatus.AUTHENTICATION_ERROR
                else:
                    self._last_status = ProviderStatus.DEGRADED
                    
        except (httpx.ConnectError, httpx.TimeoutException):
            self._last_status = ProviderStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"[FORTYGUARD] Health check failed unexpectedly: {e}")
            self._last_status = ProviderStatus.UNAVAILABLE
            
        return self._last_status

    async def fetch_temperature(self, location: str) -> Optional[TemperatureObservation]:
        if not self.api_key:
            return None
            
        backoff = 1.0
        
        # Typically the API might take coordinates, here we assume it takes a location query
        # or we pass the location directly to /current
        params = {"location": location}
        url = f"{self.base_url}/current"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self._get_headers(), params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        now = datetime.now(timezone.utc)
                        # Normalize according to TemperatureObservation schema
                        return TemperatureObservation(
                            location=location,
                            temperature=float(data.get("temperature", 0.0)),
                            risk_level=data.get("risk_level"),
                            resolution=data.get("resolution"),
                            measured_at=datetime.fromisoformat(data.get("measured_at", now.isoformat())),
                            timestamp=now,
                            provider=self.provider_name
                        )
                    elif response.status_code == 429:
                        retry_after = float(response.headers.get("Retry-After", backoff))
                        logger.warning(f"[FORTYGUARD] Rate limited. Retrying in {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                    elif response.status_code in (401, 403):
                        logger.error("[FORTYGUARD] Authentication failed. Invalid API Key.")
                        return None
                    else:
                        logger.error(f"[FORTYGUARD] API error {response.status_code}: {response.text[:100]}")
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.warning(f"[FORTYGUARD] Attempt {attempt}/{self.max_retries} failed: {exc}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
            except Exception as e:
                logger.error(f"[FORTYGUARD] Unexpected request error: {e}")
                break
                
        return None
