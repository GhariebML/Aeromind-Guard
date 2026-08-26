import os
import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from services.ingestion.provider import EnvironmentalDataProvider, ProviderStatus

logger = logging.getLogger("aeromind.fortyguard")

class FortyGuardProvider(EnvironmentalDataProvider):
    """
    FortyGuard Environmental Intelligence API Client.
    Follows enterprise resilience: exponential backoff, rate limiting, and zero-crash configuration.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
        max_retries: int = 3
    ):
        self._api_key = api_key or os.getenv("FORTYGUARD_API_KEY")
        self._base_url = (base_url or os.getenv("FORTYGUARD_BASE_URL", "https://api.fortyguard.io/v1")).rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._last_status = ProviderStatus.NOT_CONFIGURED if not self._api_key else ProviderStatus.DISCONNECTED
        self._last_check_time: Optional[datetime] = None
        self._last_latency_ms: Optional[float] = None
        self._last_error_message: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "FORTYGUARD"

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def last_latency_ms(self) -> Optional[float]:
        return self._last_latency_ms

    @property
    def error_message(self) -> Optional[str]:
        return self._last_error_message

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key.strip()) > 0)

    async def get_status(self) -> ProviderStatus:
        """Verify API connectivity and authentication credentials."""
        if not self.is_configured():
            self._last_status = ProviderStatus.NOT_CONFIGURED
            self._last_error_message = "FORTYGUARD_API_KEY environment variable is not set."
            return self._last_status

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "AeroMind-ClimateGuard/1.0"
        }

        start_time = asyncio.get_event_loop().time()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/health", headers=headers)
                latency = (asyncio.get_event_loop().time() - start_time) * 1000.0
                self._last_latency_ms = round(latency, 2)
                self._last_check_time = datetime.now(timezone.utc)

                if response.status_code == 200:
                    self._last_status = ProviderStatus.CONNECTED
                    self._last_error_message = None
                elif response.status_code in (401, 403):
                    self._last_status = ProviderStatus.ERROR
                    self._last_error_message = f"Authentication Failed (HTTP {response.status_code}): Invalid FortyGuard API Key."
                elif response.status_code == 429:
                    self._last_status = ProviderStatus.ERROR
                    self._last_error_message = "Rate limit exceeded on FortyGuard API."
                else:
                    self._last_status = ProviderStatus.DISCONNECTED
                    self._last_error_message = f"HTTP {response.status_code}: {response.text[:100]}"
        except httpx.ConnectError:
            self._last_status = ProviderStatus.DISCONNECTED
            self._last_error_message = f"Connection refused to {self._base_url}"
        except httpx.TimeoutException:
            self._last_status = ProviderStatus.DISCONNECTED
            self._last_error_message = f"Connection timeout after {self._timeout}s to {self._base_url}"
        except Exception as e:
            self._last_status = ProviderStatus.ERROR
            self._last_error_message = f"Unexpected error: {str(e)}"

        return self._last_status

    async def _request_with_backoff(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Performs robust HTTP requests with exponential backoff and rate-limit handling."""
        if not self.is_configured():
            logger.warning("[FORTYGUARD] API call attempted but provider is NOT CONFIGURED.")
            return None

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "AeroMind-ClimateGuard/1.0"
        }

        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        backoff = 1.0

        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(method, url, headers=headers, params=params)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        # Rate limited, backoff
                        retry_after = float(response.headers.get("Retry-After", backoff))
                        logger.warning(f"[FORTYGUARD] Rate limited (429). Retrying in {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                    elif response.status_code in (401, 403):
                        logger.error(f"[FORTYGUARD] Authentication rejected (HTTP {response.status_code}).")
                        return None
                    else:
                        logger.error(f"[FORTYGUARD] Request failed: HTTP {response.status_code} - {response.text[:200]}")
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.warning(f"[FORTYGUARD] Attempt {attempt}/{self._max_retries} failed: {exc}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
            except Exception as e:
                logger.error(f"[FORTYGUARD] Unexpected request error: {e}")
                break

        return None

    async def fetch_current_readings(self, latitude: float, longitude: float, location_id: str) -> List[Dict[str, Any]]:
        """
        Fetch real-time ambient temperature, surface temperature, humidity and urban heat index.
        """
        if not self.is_configured():
            return []

        payload = await self._request_with_backoff("GET", "current", params={"lat": latitude, "lon": longitude})
        if not payload:
            return []

        now = datetime.now(timezone.utc)
        readings = []

        # Validate and map incoming schema safely without assuming fabricated fields
        if "temperature" in payload:
            readings.append({
                "metric": "ambient_temp",
                "value": float(payload["temperature"]),
                "unit": "C",
                "quality": float(payload.get("quality", 1.0)),
                "timestamp": now,
                "metadata": {"provider": "FORTYGUARD", "raw": payload}
            })

        if "surface_temperature" in payload:
            readings.append({
                "metric": "surface_temp",
                "value": float(payload["surface_temperature"]),
                "unit": "C",
                "quality": float(payload.get("quality", 1.0)),
                "timestamp": now,
                "metadata": {"provider": "FORTYGUARD"}
            })

        if "humidity" in payload:
            readings.append({
                "metric": "humidity",
                "value": float(payload["humidity"]),
                "unit": "%",
                "quality": float(payload.get("quality", 1.0)),
                "timestamp": now,
                "metadata": {"provider": "FORTYGUARD"}
            })

        return readings

    async def fetch_forecast(self, latitude: float, longitude: float, location_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Fetch thermal and weather forecast series."""
        if not self.is_configured():
            return []

        payload = await self._request_with_backoff("GET", "forecast", params={"lat": latitude, "lon": longitude, "hours": hours})
        if not payload or "forecasts" not in payload:
            return []

        results = []
        for item in payload.get("forecasts", []):
            try:
                results.append({
                    "location_id": location_id,
                    "forecast_timestamp": datetime.fromisoformat(item["timestamp"]),
                    "predicted_temp_c": float(item["temperature"]),
                    "predicted_humidity_pct": float(item.get("humidity", 50.0)),
                    "predicted_risk_score": float(item.get("risk_score", 0.0)),
                    "confidence_interval_lower": float(item.get("temp_min", item["temperature"] - 1.5)),
                    "confidence_interval_upper": float(item.get("temp_max", item["temperature"] + 1.5)),
                    "provider": "FORTYGUARD",
                    "metadata_json": item
                })
            except Exception as parse_err:
                logger.warning(f"[FORTYGUARD] Skipping invalid forecast item: {parse_err}")

        return results
