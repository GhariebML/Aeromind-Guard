from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CorrelationRule(BaseModel):
    rule_id: str
    name: str
    description: str
    min_temp_c: Optional[float] = None
    min_anomaly_score: Optional[float] = None
    required_visual_events: List[str] = []  # e.g. ["SMOKE_DETECTED", "FIRE_DETECTED", "PERSON_IN_DANGER_ZONE"]
    min_people_in_danger_zone: Optional[int] = None
    min_rate_of_change: Optional[float] = None
    risk_boost: float = 0.0
    severity_override: Optional[str] = None
    action_directive: str
    is_active: bool = True

DEFAULT_CORRELATION_RULES = [
    CorrelationRule(
        rule_id="CORR-01",
        name="Thermal Spike + Visual Smoke Confirmation",
        description="High ambient temperature with optical smoke detection confirms active combustion event.",
        min_temp_c=34.0,
        min_anomaly_score=0.4,
        required_visual_events=["SMOKE_DETECTED"],
        risk_boost=30.0,
        severity_override="CRITICAL",
        action_directive="TRIGGER INDUSTRIAL SUPPRESSION & DISPATCH RESPONSE TEAM",
        is_active=True
    ),
    CorrelationRule(
        rule_id="CORR-02",
        name="Personnel in Extreme Thermal Hazard Zone",
        description="Workers detected inside a sector experiencing rapid rate-of-change and temperature > 38°C.",
        min_temp_c=38.0,
        min_rate_of_change=2.0,
        min_people_in_danger_zone=1,
        risk_boost=25.0,
        severity_override="CRITICAL",
        action_directive="INITIATE EMERGENCY ALARM AND SECTOR EVACUATION",
        is_active=True
    ),
    CorrelationRule(
        rule_id="CORR-03",
        name="Early Pre-Fire Smolder Pattern",
        description="Elevated temperature anomaly with micro-particulate increase and subtle visual haze.",
        min_temp_c=32.0,
        min_anomaly_score=0.6,
        required_visual_events=["SMOKE_DETECTED"],
        risk_boost=20.0,
        severity_override="HIGH",
        action_directive="INSPECT HVAC DUCTS AND ELECTRICAL CABINETS",
        is_active=True
    ),
    CorrelationRule(
        rule_id="CORR-04",
        name="Heat Wave Forecast Compound Hazard",
        description="Current elevated temperature with forecast projecting persistent thermal stress.",
        min_temp_c=36.0,
        min_anomaly_score=0.3,
        risk_boost=15.0,
        severity_override="HIGH",
        action_directive="ACTIVATE FACILITY AUXILIARY CHILLERS AND RESTRICT HIGH-EXERTION WORK",
        is_active=True
    )
]
