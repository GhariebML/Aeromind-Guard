import pytest
from apps.ai_engine.video_sources import FileVideoSource, RTSPVideoSource

def test_file_video_source():
    source = FileVideoSource("data/samples/demo_physical_hazards.mp4")
    assert source.open() is True
    health = source.get_health()
    assert health["status"] == "ONLINE"
    assert health["fps"] > 0
    assert health["total_frames"] > 0

    ret, frame, ts = source.read_frame()
    assert ret is True
    assert frame is not None
    assert ts is not None

    source.release()
    assert source.get_health()["status"] == "CLOSED"

def test_rtsp_video_source_credential_sanitization():
    rtsp = RTSPVideoSource("rtsp://admin:super_secret_pass@192.168.1.100:554/live/ch0")
    sanitized = rtsp._sanitize_url()
    assert "super_secret_pass" not in sanitized
    assert "rtsp://***:***@192.168.1.100:554/live/ch0" == sanitized

def test_rtsp_video_source_timeout_handling():
    # Immediate connection refused on localhost closed port 1
    rtsp = RTSPVideoSource("rtsp://127.0.0.1:1/live/ch0", connect_timeout_sec=0.5)
    opened = rtsp.open()
    assert opened is False
    assert rtsp.status == "DISCONNECTED"
