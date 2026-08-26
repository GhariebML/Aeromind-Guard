import asyncio
import json
import logging
import os
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
from typing import Dict, Any, List

from .provider import EnvironmentalDataProvider, ProviderStatus

logger = logging.getLogger("aeromind.mqtt_provider")

class MQTTProvider(EnvironmentalDataProvider):
    """
    Subscribes to live IoT sensor feeds over MQTT to provide real-time
    temperature, humidity, and environmental data for the AI engine.
    """
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.client_id = os.getenv("MQTT_CLIENT_ID", "aeromind_backend")
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.status = ProviderStatus.DISCONNECTED
        self._last_readings: Dict[str, Dict[str, Any]] = {}
        self._loop = asyncio.get_event_loop()
        
        self.connect()

    def connect(self):
        try:
            # Note: For production, TLS/SSL configuration should be added here
            self.client.connect_async(self.broker, self.port, 60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.status = ProviderStatus.ERROR

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            logger.info("Connected to MQTT Broker!")
            self.status = ProviderStatus.CONNECTED
            # Subscribe to all sensor telemetry topics
            client.subscribe("telemetry/+/sensors")
        else:
            logger.error(f"Failed to connect, return code {reason_code}")
            self.status = ProviderStatus.ERROR

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.warning(f"Disconnected from MQTT broker (code {reason_code})")
        self.status = ProviderStatus.DISCONNECTED

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            location_id = payload.get("location_id")
            
            if location_id:
                # Update the latest reading for this location
                if location_id not in self._last_readings:
                    self._last_readings[location_id] = {}
                    
                # The payload format is assumed to be {"metric": "value"} mapping
                # Example: {"location_id": "LOC-123", "ambient_temp_c": 32.5, "humidity": 45.0}
                for key, value in payload.items():
                    if key != "location_id":
                        self._last_readings[location_id][key] = {
                            "value": value,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload on topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    @property
    def provider_name(self) -> str:
        return "MQTT Industrial IoT Provider"

    async def get_status(self) -> ProviderStatus:
        return self.status

    async def fetch_current_readings(self, latitude: float, longitude: float, location_id: str) -> List[Dict[str, Any]]:
        readings = []
        if location_id in self._last_readings:
            loc_data = self._last_readings[location_id]
            if "ambient_temp_c" in loc_data:
                readings.append({
                    "metric": "ambient_temp",
                    "value": loc_data["ambient_temp_c"]["value"],
                    "unit": "C",
                    "quality": "ACTUAL",
                    "timestamp": loc_data["ambient_temp_c"]["timestamp"],
                    "metadata": {"source": "mqtt"}
                })
            if "surface_temp_c" in loc_data:
                readings.append({
                    "metric": "surface_temp",
                    "value": loc_data["surface_temp_c"]["value"],
                    "unit": "C",
                    "quality": "ACTUAL",
                    "timestamp": loc_data["surface_temp_c"]["timestamp"],
                    "metadata": {"source": "mqtt"}
                })
        return readings

    async def fetch_forecast(self, latitude: float, longitude: float, location_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        # MQTT sensors don't provide forecasts. This must be handled by another provider.
        return []

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
