import time
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone
import cv2
import numpy as np

logger = logging.getLogger("aeromind.ai.video_sources")

class VideoSource(ABC):
    """Abstract base class for all physical video ingestion feeds."""

    @abstractmethod
    def open(self) -> bool:
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[datetime]]:
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        pass

class FileVideoSource(VideoSource):
    """Robust local and uploaded MP4/video file reader."""

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self.total_frames = 0
        self.fps = 30.0
        self.width = 0
        self.height = 0
        self.current_frame_index = 0

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            logger.error(f"[FileVideoSource] Failed to open video file: {self.video_path}")
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 30.0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_frame_index = 0
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[datetime]]:
        if not self.cap or not self.cap.isOpened():
            return False, None, None

        ret, frame = self.cap.read()
        if ret:
            self.current_frame_index += 1
            now = datetime.now(timezone.utc)
            return True, frame, now
        return False, None, None

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def get_health(self) -> Dict[str, Any]:
        return {
            "source_type": "FILE",
            "path": self.video_path,
            "status": "ONLINE" if self.cap and self.cap.isOpened() else "CLOSED",
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "total_frames": self.total_frames,
            "current_frame": self.current_frame_index,
            "dropped_frames": 0
        }

class RTSPVideoSource(VideoSource):
    """
    Production-ready RTSP / Hikvision CCTV Stream Ingester.
    Features auto-reconnection loop, connection timeout, frame timeouts,
    stream health tracking, and dropped-frame metrics.
    """

    def __init__(
        self,
        stream_url: str,
        camera_id: str = "CAM-RTSP",
        connect_timeout_sec: float = 5.0,
        frame_timeout_sec: float = 3.0,
        max_reconnect_attempts: int = 5
    ):
        self.stream_url = stream_url
        self.camera_id = camera_id
        self.connect_timeout_sec = connect_timeout_sec
        self.frame_timeout_sec = frame_timeout_sec
        self.max_reconnect_attempts = max_reconnect_attempts

        self.cap: Optional[cv2.VideoCapture] = None
        self.status = "OFFLINE"
        self.fps = 0.0
        self.width = 0
        self.height = 0
        self.total_frames_received = 0
        self.dropped_frames = 0
        self.last_frame_timestamp: Optional[datetime] = None
        self.reconnect_count = 0
        self.last_error: Optional[str] = None
        self._fps_timer = time.time()
        self._fps_frame_count = 0

    def _sanitize_url(self) -> str:
        """Sanitize RTSP URL for logging so credentials are never exposed."""
        if "@" in self.stream_url:
            parts = self.stream_url.split("@")
            prefix = parts[0].split("://")[0]
            return f"{prefix}://***:***@{parts[1]}"
        return self.stream_url

    def open(self) -> bool:
        import socket
        from urllib.parse import urlparse
        safe_url = self._sanitize_url()
        logger.info(f"[RTSPVideoSource] Connecting to {safe_url} (Timeout: {self.connect_timeout_sec}s)...")

        # Fast socket reachability pre-check if host:port provided
        try:
            parsed = urlparse(self.stream_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 554
            with socket.create_connection((host, port), timeout=self.connect_timeout_sec):
                pass
        except Exception as sock_err:
            self.last_error = f"Socket connection failed: {sock_err}"
            self.status = "DISCONNECTED"
            logger.warning(f"[RTSPVideoSource] Fast pre-check failed for {safe_url}: {sock_err}")
            return False

        try:
            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            if self.cap.isOpened():
                self.status = "ONLINE"
                self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.fps = float(self.cap.get(cv2.CAP_PROP_FPS)) or 25.0
                self.last_frame_timestamp = datetime.now(timezone.utc)
                self.last_error = None
                logger.info(f"[RTSPVideoSource] Successfully connected to {safe_url} [{self.width}x{self.height} @ {self.fps} FPS]")
                return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"[RTSPVideoSource] Connection error for {safe_url}: {e}")

        self.status = "DISCONNECTED"
        return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], Optional[datetime]]:
        if not self.cap or not self.cap.isOpened():
            # Attempt auto-reconnect
            if self.reconnect_count < self.max_reconnect_attempts:
                self.reconnect_count += 1
                logger.warning(f"[RTSPVideoSource] Attempting reconnect {self.reconnect_count}/{self.max_reconnect_attempts}...")
                if self.open():
                    self.reconnect_count = 0
            else:
                self.status = "FAILED"
                return False, None, None

        if not self.cap:
            return False, None, None

        ret, frame = self.cap.read()
        now = datetime.now(timezone.utc)

        if ret and frame is not None:
            self.total_frames_received += 1
            self._fps_frame_count += 1
            self.last_frame_timestamp = now
            self.status = "ONLINE"

            # Compute real-time FPS
            dt = time.time() - self._fps_timer
            if dt >= 2.0:
                self.fps = round(self._fps_frame_count / dt, 1)
                self._fps_timer = time.time()
                self._fps_frame_count = 0

            return True, frame, now

        # Frame read failed or timeout
        self.dropped_frames += 1
        if self.last_frame_timestamp:
            elapsed_since_last = (now - self.last_frame_timestamp).total_seconds()
            if elapsed_since_last > self.frame_timeout_sec:
                self.status = "DEGRADED"
                logger.warning(f"[RTSPVideoSource] Frame timeout ({elapsed_since_last:.1f}s > {self.frame_timeout_sec}s) on {self._sanitize_url()}")

        return False, None, None

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.status = "CLOSED"

    def get_health(self) -> Dict[str, Any]:
        return {
            "source_type": "RTSP",
            "camera_id": self.camera_id,
            "url": self._sanitize_url(),
            "status": self.status,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "total_frames_received": self.total_frames_received,
            "dropped_frames": self.dropped_frames,
            "last_frame_timestamp": self.last_frame_timestamp.isoformat() if self.last_frame_timestamp else None,
            "reconnect_count": self.reconnect_count,
            "last_error": self.last_error
        }
