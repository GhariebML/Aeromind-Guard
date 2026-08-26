import pytest
import json
from fastapi.testclient import TestClient
from apps.backend.src.main import app

client = TestClient(app)

def test_websocket_heartbeat_ping_pong():
    with client.websocket_connect("/ws") as websocket:
        # Send heartbeat ping
        websocket.send_text("ping")
        data = websocket.receive_text()
        parsed = json.loads(data)
        assert parsed.get("event_type") == "pong"
        assert "timestamp" in parsed

def test_websocket_custom_message_ack():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text('{"event_type": "client.status"}')
        data = websocket.receive_text()
        parsed = json.loads(data)
        assert parsed.get("event_type") == "ack"
