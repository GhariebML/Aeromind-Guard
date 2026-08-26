import pytest
from services.correlation.engine import CorrelationEngine

def test_correlation_engine_rule_match():
    engine = CorrelationEngine()
    matches = engine.evaluate(
        location_id="ZONE-BESS-01",
        current_temp_c=36.5,
        anomaly_score=0.75,
        rate_of_change_c_per_hr=3.2,
        visual_event_types=["SMOKE_DETECTED"],
        people_in_danger_zone=0
    )

    assert len(matches) >= 1
    assert any("Smoke Confirmation" in m.rule_name for m in matches)
    assert matches[0].severity in ("HIGH", "CRITICAL")
