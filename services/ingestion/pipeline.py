import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from services.ingestion.mqtt_provider import MQTTProvider
from services.temperature.fortyguard_client import FortyGuardProvider
from services.temperature.provider import LocalDemoProvider, ProviderStatus
from services.analytics.anomaly import AnomalyDetector
from services.risk_engine.calculator import RiskEngine
from services.correlation.engine import CorrelationEngine
from services.event_engine.engine import EventEngine
from services.alert_engine.engine import AlertEngine
from services.decision_engine.engine import DecisionEngine
import os

from database.models import (
    Location, EnvironmentalReading, TemperatureReading,
    RiskScore, RiskEvent, Alert, AIDecision
)

logger = logging.getLogger("aeromind.ingestion.pipeline")

class IngestionPipeline:
    """
    Central real-time ingestion pipeline.
    Orchestrates: Provider Fetch -> Anomaly Detection -> Risk Assessment ->
    Correlation Engine -> Event & Alert Generation -> Database Persistence.
    """

    def __init__(
        self,
        fortyguard_provider: Optional[FortyGuardProvider] = None,
        demo_provider: Optional[DemoEnvironmentalProvider] = None,
        mqtt_provider: Optional[MQTTProvider] = None
    ):
        self.fortyguard = fortyguard_provider or FortyGuardProvider()
        self.demo_provider = demo_provider or LocalDemoProvider()
        self.mqtt_provider = mqtt_provider
        if os.getenv("USE_MQTT_BROKER", "false").lower() == "true" and not self.mqtt_provider:
            self.mqtt_provider = MQTTProvider()
            
        self.anomaly_detector = AnomalyDetector()
        self.risk_engine = RiskEngine()
        self.correlation_engine = CorrelationEngine()
        self.alert_engine = AlertEngine()
        self.decision_engine = DecisionEngine()

    async def ingest_location(
        self,
        db: Session,
        location: Location,
        use_demo_mode: bool = False,
        visual_hazards: Optional[List[Dict[str, Any]]] = None,
        people_in_danger_zone: int = 0
    ) -> Dict[str, Any]:
        """
        Runs a complete end-to-end ingestion and processing cycle for a given location.
        """
        now = datetime.now(timezone.utc)
        visual_hazards = visual_hazards or []

        # 1. Select provider
        ambient_temp = location.baseline_temp_c
        surface_temp = None
        current_anomaly_score = 0.0
        active_anomalies = []
        rate_of_change = 0.0
        provider_name = "DEMO"
        
        obs = None
        status = await self.fortyguard.get_status()
        if not use_demo_mode and status == ProviderStatus.CONNECTED:
            obs = await self.fortyguard.fetch_temperature(location=location.name)
            
        if not obs:
            obs = await self.demo_provider.fetch_temperature(location=location.name)
            
        if obs:
            ambient_temp = obs.temperature
            provider_name = obs.provider
            
            # Run Anomaly Detector on ambient_temp
            anomaly_res = self.anomaly_detector.update_and_detect(
                location_id=location.id,
                metric="ambient_temp",
                value=ambient_temp,
                timestamp=obs.measured_at
            )
            current_anomaly_score = max(current_anomaly_score, anomaly_res.anomaly_score)
            rate_of_change = anomaly_res.rate_of_change
            if anomaly_res.is_anomaly:
                active_anomalies.append(anomaly_res.model_dump())
                
            # Persist Environmental Reading to DB
            env_record = EnvironmentalReading(
                location_id=location.id,
                timestamp=obs.measured_at,
                metric="ambient_temp",
                value=ambient_temp,
                unit="C",
                quality=1.0,
                is_anomaly=anomaly_res.is_anomaly,
                anomaly_score=anomaly_res.anomaly_score,
                metadata_json={"provider": provider_name}
            )
            db.add(env_record)

        # Persist Temperature Reading
        temp_record = TemperatureReading(
            location_id=location.id,
            timestamp=now,
            ambient_temp_c=ambient_temp,
            surface_temp_c=surface_temp,
            rate_of_change_c_per_hr=rate_of_change,
            is_anomaly=len(active_anomalies) > 0,
            anomaly_score=current_anomaly_score,
            source_provider=provider_name
        )
        db.add(temp_record)

        # 3. Deterministic Risk Assessment
        risk_assessment = self.risk_engine.assess_risk(
            location_id=location.id,
            current_temp_c=ambient_temp,
            baseline_temp_c=location.baseline_temp_c,
            rate_of_change_c_per_hr=rate_of_change,
            anomaly_score=current_anomaly_score,
            visual_hazards=visual_hazards,
            people_in_danger_zone=people_in_danger_zone
        )

        # Persist Risk Score
        risk_db = RiskScore(
            location_id=location.id,
            timestamp=now,
            overall_score=risk_assessment.overall_score,
            severity=risk_assessment.severity,
            factors_json=[
                {
                    "name": f.name,
                    "category": f.category,
                    "score_contribution": f.score_contribution,
                    "weight": f.weight,
                    "description": f.description,
                    "evidence": f.evidence
                } for f in risk_assessment.factors
            ],
            calculation_breakdown=risk_assessment.calculation_breakdown
        )
        db.add(risk_db)

        # 4. Multi-modal Correlation Engine
        visual_event_types = [h.get("type", "") for h in visual_hazards]
        correlations = self.correlation_engine.evaluate(
            location_id=location.id,
            current_temp_c=ambient_temp,
            anomaly_score=current_anomaly_score,
            rate_of_change_c_per_hr=rate_of_change,
            visual_event_types=visual_event_types,
            people_in_danger_zone=people_in_danger_zone
        )

        # 5. Generate Events & Alerts
        created_events = []
        created_alerts = []

        # If correlation found
        for corr in correlations:
            ev = EventEngine.create_event(
                event_type="CORRELATED_PHYSICAL_THREAT",
                location_id=location.id,
                source="CORRELATION_ENGINE",
                severity=corr.severity,
                risk_score=min(100.0, risk_assessment.overall_score + corr.risk_boost),
                description=corr.description,
                evidence=corr.matched_conditions
            )
            created_events.append(ev)

            # Create Alert
            alert_rec = self.alert_engine.create_alert(
                location_id=location.id,
                title=f"CRITICAL HAZARD: {corr.rule_name}",
                message=f"{corr.description} — Required Action: {corr.action_directive}",
                severity=corr.severity,
                event_id=ev.id
            )
            created_alerts.append(alert_rec)

            db_alert = Alert(
                id=alert_rec.id,
                location_id=location.id,
                event_id=ev.id,
                title=alert_rec.title,
                message=alert_rec.message,
                severity=alert_rec.severity,
                status=alert_rec.status,
                channels=alert_rec.channels,
                created_at=alert_rec.created_at
            )
            db.add(db_alert)

        # Anomaly Alerts if score is HIGH or CRITICAL
        if current_anomaly_score >= 0.6 and not correlations:
            ev = EventEngine.create_event(
                event_type="TEMPERATURE_ANOMALY",
                location_id=location.id,
                source="ANOMALY_ENGINE",
                severity=risk_assessment.severity,
                risk_score=risk_assessment.overall_score,
                description=f"Significant thermal spike ({ambient_temp:.1f}°C, anomaly score {current_anomaly_score:.2f})",
                evidence={"ambient_temp": ambient_temp, "rate_of_change": rate_of_change}
            )
            created_events.append(ev)

            alert_rec = self.alert_engine.create_alert(
                location_id=location.id,
                title=f"Thermal Anomaly Alert: {location.name}",
                message=f"Temperature rose to {ambient_temp:.1f}°C ({rate_of_change:.1f}°C/hr rate of change)",
                severity=risk_assessment.severity,
                event_id=ev.id
            )
            created_alerts.append(alert_rec)
            db.add(Alert(
                id=alert_rec.id,
                location_id=location.id,
                event_id=ev.id,
                title=alert_rec.title,
                message=alert_rec.message,
                severity=alert_rec.severity,
                status=alert_rec.status,
                channels=alert_rec.channels,
                created_at=alert_rec.created_at
            ))

        for ev in created_events:
            db.add(RiskEvent(
                id=ev.id,
                location_id=location.id,
                event_type=ev.event_type,
                timestamp=ev.timestamp,
                severity=ev.severity,
                risk_score=ev.risk_score,
                confidence=ev.confidence,
                description=ev.description,
                evidence=ev.evidence
            ))

        # 6. AI Decision Layer
        decision = self.decision_engine.generate_decision(
            risk_assessment=risk_assessment,
            active_anomalies=active_anomalies,
            visual_hazards=visual_hazards,
            people_in_danger_zone=people_in_danger_zone
        )
        db.add(AIDecision(
            id=decision.id,
            location_id=location.id,
            timestamp=decision.timestamp,
            action=decision.action,
            priority=decision.priority,
            explanation=decision.explanation,
            evidence=decision.evidence,
            confidence=decision.confidence,
            recommended_response=decision.recommended_response,
            grounded_context=decision.grounded_context
        ))

        db.commit()

        return {
            "location_id": location.id,
            "location_name": location.name,
            "timestamp": now.isoformat(),
            "ambient_temp_c": ambient_temp,
            "surface_temp_c": surface_temp,
            "rate_of_change_c_per_hr": rate_of_change,
            "risk_score": risk_assessment.overall_score,
            "severity": risk_assessment.severity,
            "factors": [f.name for f in risk_assessment.factors],
            "anomalies_count": len(active_anomalies),
            "events_count": len(created_events),
            "alerts_count": len(created_alerts),
            "decision": decision.model_dump(),
            "provider": provider_name
        }
