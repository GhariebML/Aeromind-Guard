import pytest
from fastapi.testclient import TestClient
from apps.backend.src.main import app
from apps.backend.src.routes.video import _sanitize_filename

client = TestClient(app)

def test_filename_sanitization_path_traversal():
    assert _sanitize_filename("../../../etc/passwd") == "passwd"
    assert _sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert _sanitize_filename("safe_video.mp4") == "safe_video.mp4"

def test_request_id_and_observability_headers():
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers

def test_invalid_video_upload_rejection():
    # Submit non-existent sample
    response = client.post("/api/v1/video/analyze", data={"sample_filename": "non_existent_fake.mp4"})
    assert response.status_code == 404
