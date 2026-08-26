import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

class RiskForecaster:
    """
    Forecasting Engine:
    Projects thermal trajectory, humidity depression, and composite risk over 6h / 12h / 24h horizons.
    """

    def forecast_risk_trajectory(
        self,
        location_id: str,
        current_temp_c: float,
        rate_of_change_c_per_hr: float,
        baseline_temp_c: float = 24.0,
        forecast_points: int = 12
    ) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        results = []

        for step in range(1, forecast_points + 1):
            future_time = now + timedelta(hours=step)
            # Damped extrapolation of current rate of change towards diurnal solar model
            hour_frac = future_time.hour + (future_time.minute / 60.0)
            diurnal_offset = 5.5 * math.sin(math.pi * (hour_frac - 8) / 12)
            
            decay = math.exp(-step * 0.25)
            projected_temp = baseline_temp_c + diurnal_offset + (rate_of_change_c_per_hr * 1.5 * decay)
            projected_humidity = max(15.0, min(90.0, 60.0 - (projected_temp - 24.0) * 1.8))
            
            # Predict risk
            predicted_risk = 10.0
            if projected_temp > 32.0:
                predicted_risk += (projected_temp - 32.0) * 6.5
            predicted_risk = round(min(98.0, max(5.0, predicted_risk)), 1)

            results.append({
                "location_id": location_id,
                "forecast_timestamp": future_time.isoformat(),
                "hour_offset": step,
                "predicted_temp_c": round(projected_temp, 2),
                "predicted_humidity_pct": round(projected_humidity, 1),
                "predicted_risk_score": predicted_risk,
                "confidence_interval_lower": round(projected_temp - (0.8 + step * 0.15), 2),
                "confidence_interval_upper": round(projected_temp + (0.8 + step * 0.15), 2),
            })

        return results
