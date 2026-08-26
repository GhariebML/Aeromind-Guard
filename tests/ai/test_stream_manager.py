import pytest
import time
from services.video_stream_manager import VideoStreamManager, CameraStreamWorker
from apps.ai_engine.video_sources import FileVideoSource

def test_camera_stream_worker_lifecycle():
    source = FileVideoSource("data/samples/demo_physical_hazards.mp4")
    worker = CameraStreamWorker(
        camera_id="CAM-TEST-STREAM",
        video_source=source,
        danger_zones=[{"name": "Hazard Area", "polygon": [[100, 100], [400, 100], [400, 400], [100, 400]]}]
    )

    worker.start()
    time.sleep(0.3)
    assert worker.status == "STREAMING"

    jpeg = worker.get_latest_jpeg()
    assert jpeg is not None
    assert len(jpeg) > 100  # Valid JPEG buffer

    worker.stop()
    assert worker.status == "STOPPED"

def test_video_stream_manager_singleton():
    manager = VideoStreamManager()
    worker = manager.get_or_create_stream("CAM-TEST-01")
    assert worker is not None
    time.sleep(0.2)
    health = manager.get_stream_health("CAM-TEST-01")
    assert health["camera_id"] == "CAM-TEST-01"
    assert health["status"] in ("STREAMING", "INITIALIZING")
    worker.stop()
