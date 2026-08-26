import pytest
from datetime import datetime, timezone
from services.event_engine.engine import EventEngine, PhysicalAIEventType, UnifiedEvent

def test_unified_event_creation_and_attributes():
    now = datetime.now(timezone.utc)
    ev = EventEngine.create_event(
        event_type=PhysicalAIEventType.FORKLIFT_PROXIMITY,
        location_id="ZONE-WAREHOUSE-01",
        source="CAM-FORKLIFT-01",
        camera_id="CAM-01",
        severity="CRITICAL",
        risk_score=85.0,
        description="Worker in immediate path of reversing forklift",
        confidence=0.94,
        bounding_box=[100.0, 150.0, 200.0, 250.0],
        track_id=12,
        zone_id="ZONE-WH-AISLE-3",
        related_tracks=[12, 14],
        evidence={"distance_px": 35.0},
        timestamp=now
    )

    assert isinstance(ev, UnifiedEvent)
    assert ev.event_type == "forklift.proximity"
    assert ev.severity == "CRITICAL"
    assert ev.risk_score == 85.0
    assert ev.track_id == 12
    assert ev.zone_id == "ZONE-WH-AISLE-3"
    assert len(ev.related_tracks) == 2
    assert ev.correlation_id is not None
