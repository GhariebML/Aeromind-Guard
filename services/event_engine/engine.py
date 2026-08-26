import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class PhysicalAIEventType(str, Enum):
    PERSON_DETECTED = "person.detected"
    FORKLIFT_DETECTED = "forklift.detected"
    PPE_VIOLATION = "ppe.violation"
    RESTRICTED_ZONE_ENTER = "restricted_zone.enter"
    RESTRICTED_ZONE_DWELL = "restricted_zone.dwell"
    RESTRICTED_ZONE_EXIT = "restricted_zone.exit"
    FORKLIFT_PROXIMITY = "forklift.proximity"
    SMOKE_DETECTED = "smoke.detected"
    FIRE_DETECTED = "fire.detected"
    FLAME_DETECTED = "flame.detected"
    TANK_LEAKAGE = "tank.leakage"
    TANK_OVERFLOW = "tank.overflow"
    SMOKING_DETECTED = "smoking.detected"
    MOBILE_USAGE_DETECTED = "mobile_usage.detected"
    SLEEPING_DETECTED = "sleeping.detected"
    TEMPERATURE_ANOMALY = "temperature.anomaly"
    THERMAL_SPIKE = "thermal.spike"

class UnifiedEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_type: str
    timestamp: datetime
    location_id: str
    source: str
    camera_id: Optional[str] = None
    confidence: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: float
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    snapshot_reference: Optional[str] = None
    bounding_box: Optional[List[float]] = None
    track_id: Optional[int] = None
    zone_id: Optional[str] = None
    related_tracks: List[int] = Field(default_factory=list)
    related_sensor_data: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

class EventEngine:
    """
    Unified Physical AI Event Bus & Factory:
    Normalizes, types, and validates events across physical sensors and visual analytics.
    """

    @staticmethod
    def create_event(
        event_type: str,
        location_id: str,
        source: str,
        severity: str,
        risk_score: float,
        description: str,
        confidence: float = 0.9,
        camera_id: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        snapshot_reference: Optional[str] = None,
        bounding_box: Optional[List[float]] = None,
        track_id: Optional[int] = None,
        zone_id: Optional[str] = None,
        related_tracks: Optional[List[int]] = None,
        related_sensor_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> UnifiedEvent:
        return UnifiedEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=timestamp or datetime.now(timezone.utc),
            location_id=location_id,
            source=source,
            camera_id=camera_id,
            confidence=round(confidence, 3),
            severity=severity,
            risk_score=round(risk_score, 1),
            description=description,
            evidence=evidence or {},
            snapshot_reference=snapshot_reference,
            bounding_box=bounding_box,
            track_id=track_id,
            zone_id=zone_id,
            related_tracks=related_tracks or [],
            related_sensor_data=related_sensor_data or {},
            correlation_id=correlation_id or str(uuid.uuid4())
        )
