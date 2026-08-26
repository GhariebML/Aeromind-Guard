import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.risk_engine.factors import RiskAssessment

class OperationalDecision(BaseModel):
    id: str
    location_id: str
    timestamp: datetime
    action: str
    priority: str  # IMMEDIATE, HIGH, MEDIUM, LOW
    explanation: str
    evidence: Dict[str, Any]
    confidence: float
    recommended_response: str
    grounded_context: Dict[str, Any]

class DecisionEngine:
    """
    AI Decision Layer.
    Translates multi-modal risk assessments, anomalies, and visual hazard events
    into prioritized, explainable operational actions.
    """

    def generate_decision(
        self,
        risk_assessment: RiskAssessment,
        active_anomalies: List[Dict[str, Any]],
        visual_hazards: List[Dict[str, Any]],
        people_in_danger_zone: int = 0
    ) -> OperationalDecision:
        now = datetime.now(timezone.utc)
        score = risk_assessment.overall_score
        severity = risk_assessment.severity

        # Determine Priority & Action
        if severity == "CRITICAL" or score >= 80.0:
            priority = "IMMEDIATE"
            if any(h.get("type") == "FIRE_DETECTED" for h in visual_hazards):
                action = "Trigger Sector Fire Suppression & Initiate Immediate Evacuation"
                recommended_response = "1. Sound visual & audible sector alarms.\n2. Isolate main fuel/gas & electrical manifolds.\n3. Dispatch emergency response unit to Sector coordinates."
            elif people_in_danger_zone > 0:
                action = "Emergency Perimeter Alarm: Remove Personnel from Critical Zone"
                recommended_response = "1. Broadcast automated audio warning to zone.\n2. Contact sector supervisor via radio.\n3. Seal automated entry turnstiles."
            else:
                action = "Deploy Emergency Rapid Response & Automated Cool-Down"
                recommended_response = "1. Maximize HVAC auxiliary cooling.\n2. Restrict sector access.\n3. Verify secondary sensor telemetry."
        elif severity == "HIGH" or score >= 60.0:
            priority = "HIGH"
            action = "Dispatch Safety Crew for On-Site Thermal & Visual Inspection"
            recommended_response = "1. Notify on-duty technician.\n2. Check thermal camera feeds.\n3. Prepare containment kit."
        elif severity == "MEDIUM" or score >= 30.0:
            priority = "MEDIUM"
            action = "Elevate Sensor Polling Frequency & Monitor Perimeter"
            recommended_response = "1. Increase camera frame sampling to 30 FPS.\n2. Review upcoming thermal forecast.\n3. Log baseline divergence."
        else:
            priority = "LOW"
            action = "Continue Nominal Facility Monitoring"
            recommended_response = "Standard baseline telemetry within expected bounds."

        # Transparent evidence compilation
        evidence = {
            "overall_risk_score": score,
            "severity": severity,
            "contributing_factors": [
                {"name": f.name, "contribution": f.score_contribution, "description": f.description}
                for f in risk_assessment.factors
            ],
            "active_anomalies_count": len(active_anomalies),
            "visual_hazards_count": len(visual_hazards),
            "people_in_danger_zone": people_in_danger_zone
        }

        # Explainable summary
        explanation = (
            f"Evaluated risk score of {score}/100 ({severity}). "
            f"Primary driver: {risk_assessment.factors[0].name if risk_assessment.factors else 'Baseline'} "
            f"with {len(visual_hazards)} visual hazards and {len(active_anomalies)} statistical anomalies active."
        )

        return OperationalDecision(
            id=str(uuid.uuid4()),
            location_id=risk_assessment.location_id,
            timestamp=now,
            action=action,
            priority=priority,
            explanation=explanation,
            evidence=evidence,
            confidence=0.96,
            recommended_response=recommended_response,
            grounded_context={"raw_factors": [f.name for f in risk_assessment.factors]}
        )
