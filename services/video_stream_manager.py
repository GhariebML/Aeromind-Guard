import os
import cv2
import time
import threading
import logging
from typing import Dict, Optional, Generator
from datetime import datetime, timezone
import numpy as np

from apps.ai_engine.detector import YOLODetector
from apps.ai_engine.tracker import BoTSORTTracker
from apps.ai_engine.video_sources import VideoSource, FileVideoSource, RTSPVideoSource

logger = logging.getLogger("aeromind.stream_manager")

class CameraStreamWorker:
    """
    Worker thread that reads, annotates, and buffers live frames for a specific camera.
    """

    def __init__(
        self,
        camera_id: str,
        video_source: VideoSource,
        danger_zones: Optional[list] = None,
        inference_interval: int = 3
    ):
        self.camera_id = camera_id
        self.source = video_source
        self.danger_zones = danger_zones or []
        self.inference_interval = inference_interval

        self.detector = YOLODetector()
        self.tracker = BoTSORTTracker()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._latest_jpeg: Optional[bytes] = None
        self._lock = threading.Lock()

        self.fps = 0.0
        self.total_frames = 0
        self.dropped_frames = 0
        self.status = "INITIALIZING"
        self.active_tracks_count = 0
        self.hazard_detected = False

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info(f"[StreamWorker] Started stream worker for camera: {self.camera_id}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.source.release()
        self.status = "STOPPED"
        logger.info(f"[StreamWorker] Stopped stream worker for camera: {self.camera_id}")

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def _run_loop(self):
        if not self.source.open():
            self.status = "OFFLINE"
            logger.error(f"[StreamWorker] Failed to open video source for camera: {self.camera_id}")
            return

        self.status = "STREAMING"
        frame_count = 0
        fps_timer = time.time()
        fps_counter = 0

        # Cached detections to display between inference decimation frames
        cached_detections = []
        cached_tracks = []

        try:
            while self._running:
                ret, frame, frame_ts = self.source.read_frame()
                if not ret or frame is None:
                    # If file reached end, loop for simulation continuity
                    if isinstance(self.source, FileVideoSource):
                        self.source.open()
                        continue
                    time.sleep(0.04)
                    continue

                frame_count += 1
                fps_counter += 1
                now = frame_ts or datetime.now(timezone.utc)

                # AI Inference Decimation (run neural detection every N frames)
                if frame_count % self.inference_interval == 0:
                    cached_detections = self.detector.detect(frame, conf_threshold=0.4)
                    cached_tracks = self.tracker.update(
                        cached_detections,
                        timestamp=now,
                        danger_zones=self.danger_zones
                    )
                    self.active_tracks_count = len(cached_tracks)
                    self.hazard_detected = any(
                        d.class_name in ("fire", "smoke") for d in cached_detections
                    ) or any(t.in_danger_zone for t in cached_tracks)

                # Real-Time Visual Annotation
                annotated = frame.copy()
                h, w, _ = annotated.shape

                # 1. Draw Safety Zone Polygons
                for zone in self.danger_zones:
                    poly = zone.get("polygon", [])
                    if len(poly) >= 3:
                        pts = np.array(poly, np.int32).reshape((-1, 1, 2))
                        # Semi-transparent overlay
                        overlay = annotated.copy()
                        cv2.fillPoly(overlay, [pts], (0, 0, 180))
                        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)
                        cv2.polylines(annotated, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
                        # Zone Label
                        cv2.putText(
                            annotated,
                            zone.get("name", "DANGER ZONE"),
                            (poly[0][0], max(20, poly[0][1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2
                        )

                # 2. Draw Object Detections & Tracks
                for track in cached_tracks:
                    b = [int(c) for c in track.bbox]
                    color = (0, 0, 255) if track.in_danger_zone else (0, 255, 0)
                    cv2.rectangle(annotated, (b[0], b[1]), (b[2], b[3]), color, 2)
                    label = f"#{track.track_id} {track.class_name}"
                    if track.in_danger_zone:
                        label += f" [ZONE: {track.zone_dwell_seconds:.0f}s]"
                    cv2.putText(annotated, label, (b[0], max(15, b[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                for det in cached_detections:
                    if det.class_name in ("fire", "smoke"):
                        b = [int(c) for c in det.bbox]
                        cv2.rectangle(annotated, (b[0], b[1]), (b[2], b[3]), (0, 140, 255), 2)
                        cv2.putText(
                            annotated,
                            f"{det.class_name.upper()} {det.confidence:.2f}",
                            (b[0], max(15, b[1] - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 140, 255),
                            2
                        )

                # 3. HUD Telemetry Overlay
                cv2.putText(
                    annotated,
                    f"CAM: {self.camera_id} | FPS: {self.fps:.1f} | TRACKS: {self.active_tracks_count}",
                    (12, 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2
                )

                # Encode JPEG
                _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
                with self._lock:
                    self._latest_jpeg = buffer.tobytes()

                # Calculate real FPS
                dt = time.time() - fps_timer
                if dt >= 1.5:
                    self.fps = round(fps_counter / dt, 1)
                    fps_timer = time.time()
                    fps_counter = 0

                time.sleep(0.025)  # Throttle to ~35 FPS max

        except Exception as exc:
            self.status = "ERROR"
            logger.error(f"[StreamWorker] Camera {self.camera_id} loop exception: {exc}")
        finally:
            self.source.release()
            self.status = "STOPPED"

class VideoStreamManager:
    """
    Central Video Stream Manager.
    Orchestrates live camera workers and provides Motion-JPEG streaming generators.
    """

    def __init__(self):
        self._workers: Dict[str, CameraStreamWorker] = {}
        self._lock = threading.Lock()

    def get_or_create_stream(
        self,
        camera_id: str,
        stream_url: Optional[str] = None,
        danger_zones: Optional[list] = None
    ) -> CameraStreamWorker:
        with self._lock:
            if camera_id in self._workers and self._workers[camera_id].status in ("STREAMING", "INITIALIZING"):
                worker = self._workers[camera_id]
                if danger_zones is not None:
                    worker.danger_zones = danger_zones
                return worker

            # Choose source (RTSP if starts with rtsp://, else sample MP4)
            sample_path = "data/samples/demo_physical_hazards.mp4"
            if stream_url and stream_url.startswith("rtsp://"):
                source = RTSPVideoSource(stream_url, camera_id=camera_id)
            else:
                source = FileVideoSource(sample_path)

            worker = CameraStreamWorker(
                camera_id=camera_id,
                video_source=source,
                danger_zones=danger_zones or []
            )
            worker.start()
            self._workers[camera_id] = worker
            return worker

    def generate_mjpeg_stream(self, camera_id: str) -> Generator[bytes, None, None]:
        """Yields multipart/x-mixed-replace Motion-JPEG stream."""
        worker = self.get_or_create_stream(camera_id)
        while True:
            frame_bytes = worker.get_latest_jpeg()
            if frame_bytes is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            time.sleep(0.04)

    def get_stream_health(self, camera_id: str) -> Dict[str, Any]:
        with self._lock:
            if camera_id in self._workers:
                w = self._workers[camera_id]
                return {
                    "camera_id": camera_id,
                    "status": w.status,
                    "fps": w.fps,
                    "active_tracks": w.active_tracks_count,
                    "hazard_detected": w.hazard_detected
                }
            return {
                "camera_id": camera_id,
                "status": "OFFLINE",
                "fps": 0.0,
                "active_tracks": 0,
                "hazard_detected": False
            }

# Global singleton
stream_manager = VideoStreamManager()
