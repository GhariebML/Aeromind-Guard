from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from services.risk_engine.factors import RiskFactor, RiskAssessment

class RiskEngine:
    """
    Deterministic, fully explainable Physical AI Risk Engine.
    Combines environmental telemetry, visual computer vision hazards,
    temporal rates of change, spatial proximity, and forecast trends.
    """

    @staticmethod
    def calculate_severity(score: float) -> str:
        if score >= 80.0:
            return "CRITICAL"
        elif score >= 60.0:
            return "HIGH"
        elif score >= 30.0:
            return "MEDIUM"
        else:
            return "LOW"

    def assess_risk(
        self,
        location_id: str,
        current_temp_c: float,
        baseline_temp_c: float = 24.0,
        rate_of_change_c_per_hr: float = 0.0,
        anomaly_score: float = 0.0,
        visual_hazards: Optional[List[Dict[str, Any]]] = None,
        forecast_temp_c: Optional[float] = None,
        persistence_minutes: float = 0.0,
        people_in_danger_zone: int = 0
    ) -> RiskAssessment:
        factors: List[RiskFactor] = []
        visual_hazards = visual_hazards or []

        # 1. Base Environmental Factor (Temp offset from nominal baseline)
        temp_delta = max(0.0, current_temp_c - baseline_temp_c)
        temp_score = 0.0
        if temp_delta > 0:
            temp_score = min(25.0, temp_delta * 1.8)
            factors.append(RiskFactor(
                name="Temperature Elevation",
                category="ENVIRONMENTAL",
                score_contribution=round(temp_score, 1),
                weight=1.0,
                description=f"+{temp_delta:.1f}°C above baseline ({baseline_temp_c:.1f}°C)",
                evidence={"current_temp": current_temp_c, "baseline_temp": baseline_temp_c}
            ))

        # 2. Anomaly Severity Factor
        if anomaly_score > 0.1:
            anomaly_contrib = min(20.0, anomaly_score * 20.0)
            factors.append(RiskFactor(
                name="Environmental Anomaly",
                category="ENVIRONMENTAL",
                score_contribution=round(anomaly_contrib, 1),
                weight=1.0,
                description=f"Statistical anomaly score {anomaly_score:.2f}",
                evidence={"anomaly_score": anomaly_score}
            ))

        # 3. Rate of Change Factor (Rapid thermal spike)
        if rate_of_change_c_per_hr > 1.5:
            roc_score = min(15.0, (rate_of_change_c_per_hr - 1.5) * 4.0)
            factors.append(RiskFactor(
                name="Rapid Thermal Rate of Change",
                category="TEMPORAL",
                score_contribution=round(roc_score, 1),
                weight=1.0,
                description=f"Rising at {rate_of_change_c_per_hr:.2f}°C/hr",
                evidence={"rate_of_change_c_per_hr": rate_of_change_c_per_hr}
            ))

        # 4. Computer Vision Hazards (Smoke, Fire, High Heat Flares)
        for hazard in visual_hazards:
            hazard_type = hazard.get("type", "UNKNOWN")
            confidence = hazard.get("confidence", 0.8)
            
            if hazard_type == "FIRE_DETECTED":
                contrib = 35.0 * confidence
                factors.append(RiskFactor(
                    name="Visual Fire Confirmation",
                    category="VISUAL",
                    score_contribution=round(contrib, 1),
                    weight=1.2,
                    description=f"Optical confirmation with {confidence*100:.0f}% confidence",
                    evidence=hazard
                ))
            elif hazard_type == "SMOKE_DETECTED":
                contrib = 25.0 * confidence
                factors.append(RiskFactor(
                    name="Visual Smoke Detection",
                    category="VISUAL",
                    score_contribution=round(contrib, 1),
                    weight=1.0,
                    description=f"Smoke plume detected with {confidence*100:.0f}% confidence",
                    evidence=hazard
                ))
            elif hazard_type == "EQUIPMENT_OVERHEAT":
                contrib = 18.0 * confidence
                factors.append(RiskFactor(
                    name="Thermal Imager Hotspot",
                    category="VISUAL",
                    score_contribution=round(contrib, 1),
                    weight=1.0,
                    description="Industrial machinery hotspot detected",
                    evidence=hazard
                ))

        # 5. Proximity & Human Danger Zone Factor
        if people_in_danger_zone > 0:
            people_score = min(20.0, 10.0 + (people_in_danger_zone * 5.0))
            factors.append(RiskFactor(
                name="Human Presence in Risk Zone",
                category="PROXIMITY",
                score_contribution=round(people_score, 1),
                weight=1.2,
                description=f"{people_in_danger_zone} personnel tracked in high-risk perimeter",
                evidence={"people_count": people_in_danger_zone}
            ))

        # 6. Persistence Factor (How long condition has persisted)
        if persistence_minutes > 5.0:
            persist_score = min(10.0, (persistence_minutes / 30.0) * 10.0)
            factors.append(RiskFactor(
                name="Condition Persistence",
                category="TEMPORAL",
                score_contribution=round(persist_score, 1),
                weight=1.0,
                description=f"Condition unmitigated for {persistence_minutes:.0f} minutes",
                evidence={"persistence_minutes": persistence_minutes}
            ))

        # 7. Predictive Forecast Multiplier / Addition
        if forecast_temp_c and forecast_temp_c > current_temp_c + 2.0:
            forecast_score = min(10.0, (forecast_temp_c - current_temp_c) * 2.0)
            factors.append(RiskFactor(
                name="Adverse Forecast Trajectory",
                category="FORECAST",
                score_contribution=round(forecast_score, 1),
                weight=0.8,
                description=f"Forecast predicts further rise to {forecast_temp_c:.1f}°C",
                evidence={"forecast_temp_c": forecast_temp_c}
            ))

        # Sum raw contributions
        raw_total = sum(f.score_contribution * f.weight for f in factors)
        overall_score = round(max(0.0, min(100.0, raw_total)), 1)
        severity = self.calculate_severity(overall_score)

        # Generate transparent breakdown explanation
        breakdown_lines = [f"Overall Risk Score: {overall_score} ({severity})"]
        for f in factors:
            breakdown_lines.append(f"- {f.name}: +{f.score_contribution:.1f} ({f.description})")
        calculation_breakdown = "\n".join(breakdown_lines)

        # Recommended immediate operational directive based on deterministic score
        if severity == "CRITICAL":
            recommended_action = "IMMEDIATE EMERGENCY EVACUATION & AUTOMATED SUPPRESSION ENGAGEMENT"
        elif severity == "HIGH":
            recommended_action = "DISPATCH SAFETY CREW FOR URGENT ON-SITE INSPECTION & CONTAINMENT"
        elif severity == "MEDIUM":
            recommended_action = "ACTIVATE ENHANCED SENSOR POLLING AND MONITOR RISK ZONE PERIMETER"
        else:
            recommended_action = "CONTINUE STANDARD MONITORING — ALL METRICS NOMINAL"

        return RiskAssessment(
            location_id=location_id,
            overall_score=overall_score,
            severity=severity,
            factors=factors,
            calculation_breakdown=calculation_breakdown,
            is_anomaly_present=anomaly_score > 0.35,
            recommended_action=recommended_action
        )
