import os
import cv2
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from apps.ai_engine.detector import YOLODetector, DetectionResult
from apps.ai_engine.tracker import BoTSORTTracker, TrackedObject
from apps.ai_engine.video_sources import VideoSource, FileVideoSource, RTSPVideoSource

logger = logging.getLogger("aeromind.ai.video_analytics")

class VideoAnalyticsEngine:
    """
    Extensible Physical AI Video Analytics Engine.
    Supports local MP4 files, uploaded video streams, and live RTSP/Hikvision cameras.
    """

    def __init__(self, detector: Optional[YOLODetector] = None, snapshot_dir: str = "data/processed/snapshots"):
        self.detector = detector or YOLODetector()
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def analyze_source(
        self,
        source: VideoSource,
        job_id: str,
        camera_id: str,
        location_id: str,
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.45,
        frame_skip: int = 2,
        max_frames: Optional[int] = None,
        danger_zones: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[float, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end computer vision and tracking over an open VideoSource.
        """
        tracker = BoTSORTTracker()
        
        if not source.open():
            raise RuntimeError(f"Failed to open video source: {source.get_health()}")

        health = source.get_health()
        total_frames = health.get("total_frames", 0)
        native_fps = health.get("fps", 30.0)

        processed_detections: List[Dict[str, Any]] = []
        video_events: List[Dict[str, Any]] = []
        unique_tracks: Dict[int, Dict[str, Any]] = {}

        frame_idx = 0
        processed_count = 0
        start_time = time.time()

        try:
            while True:
                ret, frame, frame_ts = source.read_frame()
                if not ret or frame is None:
                    break

                frame_idx += 1
                if max_frames and frame_idx > max_frames:
                    break

                if frame_idx % frame_skip != 0:
                    continue

                processed_count += 1
                timestamp = frame_ts or datetime.now(timezone.utc)

                # 1. Neural & CV Perception
                detections = self.detector.detect(
                    frame,
                    conf_threshold=confidence_threshold,
                    iou_threshold=iou_threshold
                )

                # 2. Tracking with BoT-SORT
                active_tracks = tracker.update(
                    detections,
                    timestamp=timestamp,
                    danger_zones=danger_zones
                )

                for track in active_tracks:
                    unique_tracks[track.track_id] = track.to_dict()

                # 3. Store structured detection records
                for det in detections:
                    det_dict = det.to_dict()
                    det_dict["object_id"] = str(uuid.uuid4())
                    det_dict["camera_id"] = camera_id
                    det_dict["source_frame"] = frame_idx
                    det_dict["timestamp"] = timestamp.isoformat()
                    processed_detections.append(det_dict)

                # 4. Behavioral & Spatial Hazard Extraction
                smoke_dets = [d for d in detections if d.class_name == "smoke"]
                fire_dets = [d for d in detections if d.class_name == "fire"]
                danger_people = [t for t in active_tracks if t.class_name == "person" and t.in_danger_zone]
                crowd_people = [t for t in active_tracks if t.class_name == "person"]

                def save_snapshot(ev_type: str) -> str:
                    snap_id = f"snap_{uuid.uuid4().hex[:8]}.jpg"
                    snap_path = os.path.join(self.snapshot_dir, snap_id)
                    annotated = frame.copy()
                    for d in detections:
                        b = [int(c) for c in d.bbox]
                        cv2.rectangle(annotated, (b[0], b[1]), (b[2], b[3]), (0, 0, 255), 2)
                        cv2.putText(annotated, f"{d.class_name} {d.confidence:.2f}", (b[0], max(15, b[1] - 5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    cv2.imwrite(snap_path, annotated)
                    return snap_path

                if fire_dets and not any(e["event_type"] == "FIRE_DETECTED" and (frame_idx - e.get("frame_index", 0) < 30) for e in video_events):
                    snap = save_snapshot("FIRE_DETECTED")
                    video_events.append({
                        "id": str(uuid.uuid4()),
                        "camera_id": camera_id,
                        "location_id": location_id,
                        "video_job_id": job_id,
                        "frame_index": frame_idx,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "FIRE_DETECTED",
                        "confidence": max(d.confidence for d in fire_dets),
                        "severity": "CRITICAL",
                        "description": f"Active flame detection identified in frame {frame_idx}",
                        "snapshot_path": snap,
                        "metadata": {"detections_count": len(fire_dets)}
                    })

                if smoke_dets and not any(e["event_type"] == "SMOKE_DETECTED" and (frame_idx - e.get("frame_index", 0) < 30) for e in video_events):
                    snap = save_snapshot("SMOKE_DETECTED")
                    video_events.append({
                        "id": str(uuid.uuid4()),
                        "camera_id": camera_id,
                        "location_id": location_id,
                        "video_job_id": job_id,
                        "frame_index": frame_idx,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "SMOKE_DETECTED",
                        "confidence": max(d.confidence for d in smoke_dets),
                        "severity": "HIGH",
                        "description": f"Smoke plume verified in frame {frame_idx}",
                        "snapshot_path": snap,
                        "metadata": {"detections_count": len(smoke_dets)}
                    })

                if danger_people and not any(e["event_type"] == "PERSON_IN_DANGER_ZONE" and (frame_idx - e.get("frame_index", 0) < 30) for e in video_events):
                    snap = save_snapshot("PERSON_IN_DANGER_ZONE")
                    video_events.append({
                        "id": str(uuid.uuid4()),
                        "camera_id": camera_id,
                        "location_id": location_id,
                        "video_job_id": job_id,
                        "frame_index": frame_idx,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "PERSON_IN_DANGER_ZONE",
                        "confidence": 0.95,
                        "severity": "CRITICAL",
                        "description": f"{len(danger_people)} personnel breached designated hazard perimeter",
                        "snapshot_path": snap,
                        "metadata": {"person_track_ids": [t.track_id for t in danger_people]}
                    })

                if len(crowd_people) >= 5 and not any(e["event_type"] == "CROWD_EVENT" and (frame_idx - e.get("frame_index", 0) < 45) for e in video_events):
                    snap = save_snapshot("CROWD_EVENT")
                    video_events.append({
                        "id": str(uuid.uuid4()),
                        "camera_id": camera_id,
                        "location_id": location_id,
                        "video_job_id": job_id,
                        "frame_index": frame_idx,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "CROWD_EVENT",
                        "confidence": 0.88,
                        "severity": "MEDIUM",
                        "description": f"Crowd clustering detected ({len(crowd_people)} people tracked)",
                        "snapshot_path": snap,
                        "metadata": {"crowd_count": len(crowd_people)}
                    })

                if progress_callback and total_frames > 0:
                    pct = min(100.0, (frame_idx / total_frames) * 100.0)
                    progress_callback(pct, frame_idx, total_frames)

        finally:
            source.release()

        elapsed_sec = max(0.001, time.time() - start_time)
        effective_fps = round(processed_count / elapsed_sec, 1)

        return {
            "job_id": job_id,
            "total_frames": total_frames if total_frames > 0 else frame_idx,
            "processed_frames": processed_count,
            "elapsed_seconds": round(elapsed_sec, 2),
            "effective_fps": effective_fps,
            "native_fps": native_fps,
            "total_detections": len(processed_detections),
            "total_tracks": len(unique_tracks),
            "total_events": len(video_events),
            "events": video_events,
            "detections": processed_detections[:500],
            "tracks": list(unique_tracks.values()),
            "source_health": health
        }

    def analyze_video_file(
        self,
        video_path: str,
        job_id: str,
        camera_id: str,
        location_id: str,
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.45,
        frame_skip: int = 2,
        danger_zones: Optional[List[Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[float, int, int], None]] = None
    ) -> Dict[str, Any]:
        """Convenience wrapper for file-based processing."""
        source = FileVideoSource(video_path)
        return self.analyze_source(
            source=source,
            job_id=job_id,
            camera_id=camera_id,
            location_id=location_id,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            frame_skip=frame_skip,
            danger_zones=danger_zones,
            progress_callback=progress_callback
        )
