import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AnomalyDetectionResult(BaseModel):
    metric: str
    value: float
    baseline: float
    z_score: float
    rate_of_change: float
    anomaly_score: float  # Normalized 0.0 to 1.0
    is_anomaly: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    timestamp: datetime
    location_id: str

class AnomalyDetector:
    """
    Modular statistical and deterministic anomaly detection engine.
    Computes rolling z-scores, rate-of-change spikes, and persistence indicators.
    """

    def __init__(
        self,
        z_score_threshold: float = 2.5,
        rate_of_change_threshold: float = 4.0,  # Degrees C / unit per hour
        critical_z_score: float = 4.0
    ):
        self.z_score_threshold = z_score_threshold
        self.rate_of_change_threshold = rate_of_change_threshold
        self.critical_z_score = critical_z_score
        # In-memory history buffer per (location_id, metric) -> list of (timestamp, value)
        self._history: Dict[str, List[tuple]] = {}

    def _get_key(self, location_id: str, metric: str) -> str:
        return f"{location_id}:{metric}"

    def update_and_detect(
        self,
        location_id: str,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None,
        window_size: int = 30
    ) -> AnomalyDetectionResult:
        now = timestamp or datetime.now(timezone.utc)
        key = self._get_key(location_id, metric)

        if key not in self._history:
            self._history[key] = []

        history = self._history[key]
        history.append((now, value))

        # Trim window size
        if len(history) > window_size:
            self._history[key] = history[-window_size:]
            history = self._history[key]

        values = [v for _, v in history]
        n = len(values)

        if n < 3:
            # Insufficient samples for robust rolling baseline
            return AnomalyDetectionResult(
                metric=metric,
                value=value,
                baseline=value,
                z_score=0.0,
                rate_of_change=0.0,
                anomaly_score=0.0,
                is_anomaly=False,
                severity="LOW",
                reason="Establishing statistical baseline",
                timestamp=now,
                location_id=location_id
            )

        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance) if variance > 1e-6 else 0.5

        # Z-score computation
        z_score = (value - mean_val) / std_dev

        # Rate of change computation (units per hour)
        rate_of_change = 0.0
        if len(history) >= 2:
            prev_time, prev_val = history[-2]
            dt_seconds = max(1.0, (now - prev_time).total_seconds())
            rate_of_change = ((value - prev_val) / dt_seconds) * 3600.0

        # Anomaly scoring logic
        is_z_anomaly = abs(z_score) >= self.z_score_threshold
        is_roc_anomaly = abs(rate_of_change) >= self.rate_of_change_threshold
        is_anomaly = is_z_anomaly or is_roc_anomaly

        # Continuous anomaly score between 0.0 and 1.0
        normalized_z = min(1.0, abs(z_score) / (self.critical_z_score + 1.0))
        normalized_roc = min(1.0, abs(rate_of_change) / (self.rate_of_change_threshold * 2.5))
        anomaly_score = max(normalized_z, normalized_roc)

        # Severity classification
        if anomaly_score >= 0.8 or abs(z_score) >= self.critical_z_score:
            severity = "CRITICAL"
        elif anomaly_score >= 0.6 or abs(z_score) >= 3.0:
            severity = "HIGH"
        elif anomaly_score >= 0.35 or is_anomaly:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Explainable reason
        reasons = []
        if is_z_anomaly:
            reasons.append(f"Z-Score {z_score:.2f} exceeds threshold {self.z_score_threshold:.1f} (Baseline: {mean_val:.1f})")
        if is_roc_anomaly:
            reasons.append(f"Rate of change {rate_of_change:.2f}/hr exceeds threshold {self.rate_of_change_threshold:.1f}/hr")
        
        reason = "; ".join(reasons) if reasons else "Nominal operating parameters"

        return AnomalyDetectionResult(
            metric=metric,
            value=value,
            baseline=round(mean_val, 2),
            z_score=round(z_score, 2),
            rate_of_change=round(rate_of_change, 2),
            anomaly_score=round(anomaly_score, 3),
            is_anomaly=is_anomaly,
            severity=severity,
            reason=reason,
            timestamp=now,
            location_id=location_id
        )
