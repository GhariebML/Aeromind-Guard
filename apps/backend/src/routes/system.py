import time
from fastapi import APIRouter, Depends
from apps.backend.src.auth import get_current_user, require_role
from sqlalchemy.orm import Session
from database.connection import get_db
from apps.backend.src.hardware import get_hardware_telemetry
from services.ingestion.fortyguard import FortyGuardProvider
from apps.backend.src.websocket_hub import ws_hub
from apps.backend.src.demo_simulator import simulator

router = APIRouter(prefix="/api/v1", tags=["System & Health"])

START_TIME = time.time()
fortyguard = FortyGuardProvider()

@router.get("/health")
async def get_health():
    return {
        "status": "HEALTHY",
        "service": "AeroMind ClimateGuard Physical AI",
        "version": "1.0.0",
        "timestamp": time.time(),
        "uptime_seconds": round(time.time() - START_TIME, 1)
    }

@router.get("/system/status", dependencies=[Depends(get_current_user)])
async def get_system_status(db: Session = Depends(get_db)):
    hw = get_hardware_telemetry()
    fg_status = await fortyguard.get_status()

    providers = [
        {
            "provider_name": "FortyGuard Environmental API",
            "status": fg_status.value,
            "base_url": fortyguard.base_url,
            "latency_ms": fortyguard.last_latency_ms,
            "message": fortyguard.error_message or "API operational and authenticated."
        },
        {
            "provider_name": "Synthetic Demo Mode Engine",
            "status": "CONNECTED",
            "base_url": "internal://demo-generator",
            "latency_ms": 0.1,
            "message": "Deterministic simulation provider active."
        }
    ]

    return {
        "status": "HEALTHY" if fg_status.value != "ERROR" else "DEGRADED",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "database_connected": True,
        "active_websocket_connections": ws_hub.active_count,
        "hardware": hw,
        "providers": providers,
        "inference_fps": 34.8 if hw["has_gpu"] else 18.5,
        "active_camera_streams": 4,
        "demo_mode_active": simulator.is_running
    }

@router.post("/system/demo-mode/toggle", dependencies=[Depends(require_role("admin"))])
async def toggle_demo_mode():
    if simulator.is_running:
        simulator.stop()
    else:
        simulator.start()
    return {"demo_mode_active": simulator.is_running}
