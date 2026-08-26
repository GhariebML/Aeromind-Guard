import os
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Location
from services.ingestion.pipeline import IngestionPipeline
from apps.backend.src.websocket_hub import ws_hub

logger = logging.getLogger("aeromind.demo_simulator")

class DemoSimulator:
    """
    Background simulation worker for live demonstrations.
    Active only in DEMO mode or when explicitly started.
    Emits standardized typed WebSocket telemetry events.
    """

    def __init__(self, interval_seconds: float = 3.5):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task = None
        self.pipeline = IngestionPipeline()
        self._tick_counter = 0

    def start(self):
        # Check APP_MODE
        app_mode = os.getenv("APP_MODE", "demo").lower()
        if app_mode == "production" and not os.getenv("FORCE_DEMO"):
            logger.info("[DemoSimulator] APP_MODE is 'production'. Demo simulator start suppressed.")
            return

        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._loop())
            logger.info("[DemoSimulator] Background simulation loop started.")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            logger.info("[DemoSimulator] Background simulation loop stopped.")

    async def _loop(self):
        while self.is_running:
            try:
                await self.step()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[DemoSimulator] Error in loop step: {e}")
                await asyncio.sleep(self.interval_seconds)

    async def step(self):
        self._tick_counter += 1
        db: Session = SessionLocal()
        try:
            locations = db.query(Location).filter_by(is_active=True).all()
            if not locations:
                return

            loc_idx = (self._tick_counter - 1) % len(locations)
            target_location = locations[loc_idx]

            visual_hazards = []
            people_in_danger = 0

            # Intermittent simulated hazards for demonstration
            if self._tick_counter % 8 == 0 and "BESS" in target_location.name:
                visual_hazards.append({
                    "type": "SMOKE_DETECTED",
                    "confidence": 0.89,
                    "description": "Optical smoke plume tracked over Battery Rack 3",
                    "source": "CAM-BESS-01"
                })
                people_in_danger = 1

            if self._tick_counter % 14 == 0 and "Cracker" in target_location.name:
                visual_hazards.append({
                    "type": "FIRE_DETECTED",
                    "confidence": 0.94,
                    "description": "High-intensity flare/flame detected at Hydrocarbon Flange",
                    "source": "CAM-REFINERY-02"
                })
                people_in_danger = 2

            # Execute unified ingestion pipeline
            result = await self.pipeline.ingest_location(
                db=db,
                location=target_location,
                use_demo_mode=True,
                visual_hazards=visual_hazards,
                people_in_danger_zone=people_in_danger
            )

            # Broadcast typed events
            await ws_hub.broadcast("telemetry.updated", result)
            await ws_hub.broadcast("risk.updated", {
                "location_id": target_location.id,
                "risk_score": result["risk_score"],
                "severity": result["severity"],
                "factors": result["factors"]
            })

            if result.get("alerts_count", 0) > 0:
                await ws_hub.broadcast("alert.created", {
                    "location_id": target_location.id,
                    "location_name": target_location.name,
                    "severity": result["severity"],
                    "risk_score": result["risk_score"],
                    "message": f"Critical threshold breach at {target_location.name}"
                })

        finally:
            db.close()

simulator = DemoSimulator()
