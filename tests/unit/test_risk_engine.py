import pytest
from services.risk_engine.calculator import RiskEngine

def test_risk_engine_baseline():
    engine = RiskEngine()
    assessment = engine.assess_risk(
        location_id="LOC-TEST-01",
        current_temp_c=24.5,
        baseline_temp_c=24.0,
        rate_of_change_c_per_hr=0.1,
        anomaly_score=0.0
    )
    assert 0.0 <= assessment.overall_score <= 100.0
    assert assessment.severity == "LOW"
    assert assessment.overall_score < 30.0

def test_risk_engine_fire_and_smoke():
    engine = RiskEngine()
    visual_hazards = [
        {"type": "FIRE_DETECTED", "confidence": 0.95},
        {"type": "SMOKE_DETECTED", "confidence": 0.90}
    ]
    assessment = engine.assess_risk(
        location_id="LOC-TEST-01",
        current_temp_c=42.0,
        baseline_temp_c=24.0,
        rate_of_change_c_per_hr=5.2,
        anomaly_score=0.85,
        visual_hazards=visual_hazards,
        people_in_danger_zone=2
    )
    assert assessment.overall_score >= 80.0
    assert assessment.severity == "CRITICAL"
    assert "FIRE" in assessment.calculation_breakdown or "Visual Fire" in assessment.calculation_breakdown
    assert len(assessment.factors) >= 4

def test_severity_levels():
    engine = RiskEngine()
    assert engine.calculate_severity(15.0) == "LOW"
    assert engine.calculate_severity(45.0) == "MEDIUM"
    assert engine.calculate_severity(68.0) == "HIGH"
    assert engine.calculate_severity(88.0) == "CRITICAL"
