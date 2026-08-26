import pytest
import asyncio
from unittest.mock import MagicMock, patch
from services.ingestion.mqtt_provider import MQTTProvider
from services.ingestion.provider import ProviderStatus

@pytest.fixture
def mock_mqtt_client():
    with patch('services.ingestion.mqtt_provider.mqtt.Client') as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_mqtt_provider_initialization(mock_mqtt_client):
    provider = MQTTProvider()
    assert provider.provider_name == "MQTT Industrial IoT Provider"
    
    # Simulate successful connection callback
    provider._on_connect(provider.client, None, None, 0, None)
    
    status = await provider.get_status()
    assert status == ProviderStatus.CONNECTED
    
    # Check subscription
    provider.client.subscribe.assert_called_with("telemetry/+/sensors")

@pytest.mark.asyncio
async def test_mqtt_provider_message_handling(mock_mqtt_client):
    provider = MQTTProvider()
    provider.status = ProviderStatus.CONNECTED
    
    # Create a mock MQTT message
    mock_msg = MagicMock()
    mock_msg.topic = "telemetry/loc_123/sensors"
    mock_msg.payload = b'{"location_id": "loc_123", "ambient_temp_c": 35.5, "surface_temp_c": 40.0}'
    
    # Simulate receiving message
    provider._on_message(provider.client, None, mock_msg)
    
    # Fetch readings
    readings = await provider.fetch_current_readings(0.0, 0.0, "loc_123")
    
    assert len(readings) == 2
    temp_reading = next(r for r in readings if r["metric"] == "ambient_temp")
    assert temp_reading["value"] == 35.5
    assert temp_reading["unit"] == "C"
    
    surf_reading = next(r for r in readings if r["metric"] == "surface_temp")
    assert surf_reading["value"] == 40.0
