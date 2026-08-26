import math
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from services.ingestion.provider import EnvironmentalDataProvider, ProviderStatus

class DemoEnvironmentalProvider(EnvironmentalDataProvider):
    """
    Deterministic Synthetic Environmental Provider for DEMO MODE.
    Provides realistic diurnal temperature cycles, industrial heat pockets,
    and simulated anomalies clearly demarcated with source metadata.
    """

    def __init__(self, baseline_temp: float = 28.5, inject_anomaly: bool = False):
        self.baseline_temp = baseline_temp
        self.inject_anomaly = inject_anomaly
        self._step = 0

    @property
    def provider_name(self) -> str:
        return "SYNTHETIC_DEMO"

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus.CONNECTED

    async def fetch_current_readings(self, latitude: float, longitude: float, location_id: str) -> List[Dict[str, Any]]:
        self._step += 1
        now = datetime.now(timezone.utc)
        
        # Diurnal solar cycle calculation based on current hour
        hour_frac = now.hour + (now.minute / 60.0)
        diurnal_offset = 6.0 * math.sin(math.pi * (hour_frac - 8) / 12)  # Peak around 14:00
        noise = (random.random() - 0.5) * 0.8
        
        ambient_temp = self.baseline_temp + diurnal_offset + noise
        surface_temp = ambient_temp + 4.5 + (random.random() * 1.5)
        humidity = max(15.0, min(95.0, 60.0 - (diurnal_offset * 2.5) + noise))
        air_quality_pm25 = max(5.0, 18.0 + (random.random() * 5.0))
        wind_speed = max(0.5, 4.2 + (random.random() * 1.8))

        # If anomaly injection is active
        if self.inject_anomaly or (self._step % 15 == 0):
            ambient_temp += 12.5  # Critical heat spike
            surface_temp += 22.0
            air_quality_pm25 += 45.0

        return [
            {
                "metric": "ambient_temp",
                "value": round(ambient_temp, 2),
                "unit": "C",
                "quality": 1.0,
                "timestamp": now,
                "metadata": {"provider": "DEMO_MODE", "is_synthetic": True}
            },
            {
                "metric": "surface_temp",
                "value": round(surface_temp, 2),
                "unit": "C",
                "quality": 1.0,
                "timestamp": now,
                "metadata": {"provider": "DEMO_MODE", "is_synthetic": True}
            },
            {
                "metric": "humidity",
                "value": round(humidity, 1),
                "unit": "%",
                "quality": 1.0,
                "timestamp": now,
                "metadata": {"provider": "DEMO_MODE", "is_synthetic": True}
            },
            {
                "metric": "air_quality_pm25",
                "value": round(air_quality_pm25, 1),
                "unit": "ug/m3",
                "quality": 1.0,
                "timestamp": now,
                "metadata": {"provider": "DEMO_MODE", "is_synthetic": True}
            },
            {
                "metric": "wind_speed",
                "value": round(wind_speed, 1),
                "unit": "m/s",
                "quality": 1.0,
                "timestamp": now,
                "metadata": {"provider": "DEMO_MODE", "is_synthetic": True}
            }
        ]

    async def fetch_forecast(self, latitude: float, longitude: float, location_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        forecasts = []

        for h in range(1, hours + 1):
            future_time = now + timedelta(hours=h)
            hour_frac = future_time.hour + (future_time.minute / 60.0)
            diurnal_offset = 6.0 * math.sin(math.pi * (hour_frac - 8) / 12)
            predicted_temp = self.baseline_temp + diurnal_offset
            predicted_hum = max(20.0, min(90.0, 58.0 - (diurnal_offset * 2.2)))
            
            # Forecast risk estimation
            risk_score = 15.0
            if predicted_temp > 35.0:
                risk_score += (predicted_temp - 35.0) * 8.0
            risk_score = min(95.0, risk_score)

            forecasts.append({
                "location_id": location_id,
                "forecast_timestamp": future_time,
                "predicted_temp_c": round(predicted_temp, 2),
                "predicted_humidity_pct": round(predicted_hum, 1),
                "predicted_risk_score": round(risk_score, 1),
                "confidence_interval_lower": round(predicted_temp - 1.2, 2),
                "confidence_interval_upper": round(predicted_temp + 1.2, 2),
                "provider": "DEMO_MODE",
                "metadata_json": {"is_synthetic": True}
            })

        return forecasts
