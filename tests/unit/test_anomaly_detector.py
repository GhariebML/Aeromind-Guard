import pytest
from datetime import datetime, timezone, timedelta
from services.analytics.anomaly import AnomalyDetector

def test_anomaly_detector_baseline_and_spike():
    detector = AnomalyDetector(z_score_threshold=2.0, rate_of_change_threshold=3.0)
    now = datetime.now(timezone.utc)
    
    # Establish nominal baseline
    for i in range(10):
        t = now - timedelta(minutes=(10 - i) * 5)
        res = detector.update_and_detect("LOC-1", "ambient_temp", 24.0 + (i % 2) * 0.2, timestamp=t)

    assert not res.is_anomaly
    assert res.severity == "LOW"

    # Inject significant spike
    spike_time = now + timedelta(minutes=5)
    spike_res = detector.update_and_detect("LOC-1", "ambient_temp", 45.0, timestamp=spike_time)

    assert spike_res.is_anomaly
    assert spike_res.z_score > 2.0
    assert spike_res.severity in ("HIGH", "CRITICAL")
    assert spike_res.anomaly_score > 0.6
