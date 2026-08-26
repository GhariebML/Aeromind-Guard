import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from apps.ai_engine.detector import DetectionResult

class TrackedObject:
    def __init__(
        self,
        track_id: int,
        class_name: str,
        bbox: List[float],
        timestamp: datetime
    ):
        self.track_id = track_id
        self.class_name = class_name
        self.bbox = bbox
        self.first_seen = timestamp
        self.last_seen = timestamp
        self.total_frames = 1
        self.trajectory = [[(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0, timestamp.timestamp()]]
        self.avg_velocity_px_per_s = 0.0
        self.is_active = True
        self.in_danger_zone = False
        self.current_zone_id: Optional[str] = None
        self.zone_entry_time: Optional[datetime] = None
        self.zone_dwell_seconds: float = 0.0

    def update(self, bbox: List[float], timestamp: datetime):
        self.bbox = bbox
        self.last_seen = timestamp
        self.total_frames += 1

        curr_cx = (bbox[0] + bbox[2]) / 2.0
        curr_cy = (bbox[1] + bbox[3]) / 2.0
        self.trajectory.append([curr_cx, curr_cy, timestamp.timestamp()])

        # Keep last 50 points
        if len(self.trajectory) > 50:
            self.trajectory = self.trajectory[-50:]

        # Estimate velocity
        if len(self.trajectory) >= 2:
            prev_x, prev_y, prev_t = self.trajectory[-2]
            dt = max(0.01, timestamp.timestamp() - prev_t)
            dist = math.sqrt((curr_cx - prev_x) ** 2 + (curr_cy - prev_y) ** 2)
            inst_vel = dist / dt
            self.avg_velocity_px_per_s = (self.avg_velocity_px_per_s * 0.7) + (inst_vel * 0.3)

        if self.in_danger_zone and self.zone_entry_time:
            self.zone_dwell_seconds = max(0.0, (timestamp - self.zone_entry_time).total_seconds())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "bbox": [round(float(c), 2) for c in self.bbox],
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_frames": self.total_frames,
            "avg_velocity_px_per_s": round(self.avg_velocity_px_per_s, 2),
            "trajectory": [[round(x, 1), round(y, 1), t] for x, y, t in self.trajectory],
            "is_active": self.is_active,
            "in_danger_zone": self.in_danger_zone,
            "current_zone_id": self.current_zone_id,
            "zone_dwell_seconds": round(self.zone_dwell_seconds, 1)
        }

class BaseTracker(ABC):
    @abstractmethod
    def update(self, detections: List[DetectionResult], timestamp: datetime) -> List[TrackedObject]:
        pass

class BoTSORTTracker(BaseTracker):
    """
    High performance multi-object tracker implementing IoU matching,
    centroid proximity association, spatial danger zone verification,
    dwell time analysis, and forklift proximity safety.
    """

    def __init__(
        self,
        max_distance_threshold: float = 75.0,
        max_inactive_frames: int = 15,
        forklift_danger_distance_px: float = 120.0
    ):
        self.max_distance_threshold = max_distance_threshold
        self.max_inactive_frames = max_inactive_frames
        self.forklift_danger_distance_px = forklift_danger_distance_px
        self._next_track_id = 1
        self._tracks: Dict[int, TrackedObject] = {}
        self._inactive_counts: Dict[int, int] = {}

    @staticmethod
    def _compute_iou(boxA: List[float], boxB: List[float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        boxBArea = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def update(
        self,
        detections: List[DetectionResult],
        timestamp: Optional[datetime] = None,
        danger_zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[TrackedObject]:
        now = timestamp or datetime.now(timezone.utc)
        matched_track_ids = set()
        matched_det_indices = set()

        # 1. Match existing active tracks with incoming detections using IoU and Centroid distance
        for det_idx, det in enumerate(detections):
            det_cx = (det.bbox[0] + det.bbox[2]) / 2.0
            det_cy = (det.bbox[1] + det.bbox[3]) / 2.0

            best_track_id = None
            best_score = -1.0

            for track_id, track in self._tracks.items():
                if track_id in matched_track_ids or not track.is_active or track.class_name != det.class_name:
                    continue

                iou = self._compute_iou(det.bbox, track.bbox)
                track_cx = (track.bbox[0] + track.bbox[2]) / 2.0
                track_cy = (track.bbox[1] + track.bbox[3]) / 2.0
                dist = math.sqrt((det_cx - track_cx) ** 2 + (det_cy - track_cy) ** 2)

                # Combined score: IoU + proximity
                score = (iou * 2.0) + max(0.0, (self.max_distance_threshold - dist) / self.max_distance_threshold)
                if score > best_score and (iou > 0.2 or dist < self.max_distance_threshold):
                    best_score = score
                    best_track_id = track_id

            if best_track_id is not None:
                self._tracks[best_track_id].update(det.bbox, now)
                self._inactive_counts[best_track_id] = 0
                matched_track_ids.add(best_track_id)
                matched_det_indices.add(det_idx)

        # 2. Create new tracks for unmatched detections
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_det_indices:
                new_id = self._next_track_id
                self._next_track_id += 1
                new_track = TrackedObject(
                    track_id=new_id,
                    class_name=det.class_name,
                    bbox=det.bbox,
                    timestamp=now
                )
                self._tracks[new_id] = new_track
                self._inactive_counts[new_id] = 0

        # 3. Handle inactive tracks
        for track_id, track in list(self._tracks.items()):
            if track_id not in matched_track_ids:
                self._inactive_counts[track_id] = self._inactive_counts.get(track_id, 0) + 1
                if self._inactive_counts[track_id] > self.max_inactive_frames:
                    track.is_active = False

        # 4. Danger zone evaluation & dwell time
        if danger_zones:
            for track in self._tracks.values():
                if not track.is_active:
                    continue
                cx = (track.bbox[0] + track.bbox[2]) / 2.0
                cy = (track.bbox[1] + track.bbox[3]) / 2.0
                in_zone = False
                matched_zone_name = None

                for zone in danger_zones:
                    poly = zone.get("polygon", [])
                    if len(poly) >= 3:
                        # Point in polygon check
                        n = len(poly)
                        inside = False
                        p1x, p1y = poly[0]
                        for i in range(n + 1):
                            p2x, p2y = poly[i % n]
                            if cy > min(p1y, p2y):
                                if cy <= max(p1y, p2y):
                                    if cx <= max(p1x, p2x):
                                        if p1y != p2y:
                                            xinters = (cy - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                        if p1x == p2x or cx <= xinters:
                                            inside = not inside
                            p1x, p1y = p2x, p2y
                        if inside:
                            in_zone = True
                            matched_zone_name = zone.get("name", "RESTRICTED_ZONE")
                            break

                # State transition handling (enter vs dwell vs exit)
                if in_zone and not track.in_danger_zone:
                    track.in_danger_zone = True
                    track.current_zone_id = matched_zone_name
                    track.zone_entry_time = now
                    track.zone_dwell_seconds = 0.0
                elif in_zone and track.in_danger_zone:
                    if track.zone_entry_time:
                        track.zone_dwell_seconds = (now - track.zone_entry_time).total_seconds()
                elif not in_zone and track.in_danger_zone:
                    track.in_danger_zone = False
                    track.current_zone_id = None
                    track.zone_entry_time = None
                    track.zone_dwell_seconds = 0.0

        return [t for t in self._tracks.values() if t.is_active]

    def check_forklift_person_proximity(self, active_tracks: List[TrackedObject]) -> List[Dict[str, Any]]:
        """Identifies hazardous proximity between moving forklifts and personnel."""
        forklifts = [t for t in active_tracks if t.class_name in ("forklift", "vehicle")]
        persons = [t for t in active_tracks if t.class_name == "person"]
        proximity_events = []

        for fl in forklifts:
            fl_cx = (fl.bbox[0] + fl.bbox[2]) / 2.0
            fl_cy = (fl.bbox[1] + fl.bbox[3]) / 2.0

            for p in persons:
                p_cx = (p.bbox[0] + p.bbox[2]) / 2.0
                p_cy = (p.bbox[1] + p.bbox[3]) / 2.0

                dist = math.sqrt((fl_cx - p_cx) ** 2 + (fl_cy - p_cy) ** 2)
                if dist < self.forklift_danger_distance_px:
                    proximity_events.append({
                        "forklift_track_id": fl.track_id,
                        "person_track_id": p.track_id,
                        "distance_px": round(dist, 1),
                        "severity": "CRITICAL" if dist < (self.forklift_danger_distance_px * 0.5) else "HIGH",
                        "description": f"Worker (Track #{p.track_id}) is {dist:.1f}px from moving forklift (Track #{fl.track_id})"
                    })

        return proximity_events
