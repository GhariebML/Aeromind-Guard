from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class RiskFactor:
    name: str
    category: str  # ENVIRONMENTAL, VISUAL, TEMPORAL, PROXIMITY, FORECAST
    score_contribution: float
    weight: float = 1.0
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RiskAssessment:
    location_id: str
    overall_score: float  # 0.0 to 100.0
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[RiskFactor]
    calculation_breakdown: str
    is_anomaly_present: bool = False
    recommended_action: str = ""
