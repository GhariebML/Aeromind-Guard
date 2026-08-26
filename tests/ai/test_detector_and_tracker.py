import pytest
import numpy as np
from datetime import datetime, timezone
from apps.ai_engine.detector import YOLODetector, DetectionResult
from apps.ai_engine.tracker import BoTSORTTracker

def test_yolo_detector_heuristic_perception():
    detector = YOLODetector()
    
    # Create test image with simulated flame color (bright orange/yellow in HSV)
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    test_img[100:200, 100:200] = (0, 200, 255)  # Orange flame BGR

    results = detector.detect(test_img, conf_threshold=0.4)
    assert isinstance(results, list)
    # Should detect flame region
    assert any(r.class_name == "fire" for r in results)

def test_tracker_trajectory_and_velocity():
    tracker = BoTSORTTracker()
    now = datetime.now(timezone.utc)
    
    # Frame 1
    det1 = [DetectionResult(class_name="person", confidence=0.9, bbox=[100, 100, 150, 200])]
    tracks1 = tracker.update(det1, timestamp=now)
    assert len(tracks1) == 1
    assert tracks1[0].track_id == 1

    # Frame 2 - moved right
    det2 = [DetectionResult(class_name="person", confidence=0.9, bbox=[140, 100, 190, 200])]
    tracks2 = tracker.update(det2, timestamp=now)
    assert len(tracks2) == 1
    assert tracks2[0].track_id == 1  # Retained same track ID
    assert len(tracks2[0].trajectory) >= 2

def test_danger_zone_polygon_intersection():
    tracker = BoTSORTTracker()
    now = datetime.now(timezone.utc)
    danger_zones = [{"name": "Zone A", "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]]}]

    # Person inside zone
    det_inside = [DetectionResult(class_name="person", confidence=0.9, bbox=[150, 150, 200, 250])]
    tracks_inside = tracker.update(det_inside, timestamp=now, danger_zones=danger_zones)
    assert tracks_inside[0].in_danger_zone is True

    # Person outside zone
    det_outside = [DetectionResult(class_name="person", confidence=0.9, bbox=[450, 150, 500, 250])]
    tracker_out = BoTSORTTracker()
    tracks_outside = tracker_out.update(det_outside, timestamp=now, danger_zones=danger_zones)
    assert tracks_outside[0].in_danger_zone is False

def test_danger_zone_dwell_time_accumulation():
    tracker = BoTSORTTracker()
    t0 = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 25, 12, 0, 10, tzinfo=timezone.utc)
    danger_zones = [{"name": "Zone Alpha", "polygon": [[0, 0], [300, 0], [300, 300], [0, 300]]}]

    det = [DetectionResult(class_name="person", confidence=0.95, bbox=[100, 100, 150, 200])]
    tracks0 = tracker.update(det, timestamp=t0, danger_zones=danger_zones)
    assert tracks0[0].in_danger_zone is True
    assert tracks0[0].zone_dwell_seconds == 0.0

    tracks1 = tracker.update(det, timestamp=t1, danger_zones=danger_zones)
    assert tracks1[0].in_danger_zone is True
    assert tracks1[0].zone_dwell_seconds == 10.0

def test_forklift_person_proximity_breach():
    tracker = BoTSORTTracker(forklift_danger_distance_px=100.0)
    now = datetime.now(timezone.utc)

    # Forklift at (100, 100) and Person at (140, 100) -> distance 40px (< 100px)
    det_fl = DetectionResult(class_name="forklift", confidence=0.9, bbox=[80, 80, 120, 120])
    det_p = DetectionResult(class_name="person", confidence=0.95, bbox=[130, 80, 150, 120])

    active_tracks = tracker.update([det_fl, det_p], timestamp=now)
    proximity_events = tracker.check_forklift_person_proximity(active_tracks)

    assert len(proximity_events) == 1
    assert proximity_events[0]["severity"] == "CRITICAL"
    assert proximity_events[0]["distance_px"] < 50.0

