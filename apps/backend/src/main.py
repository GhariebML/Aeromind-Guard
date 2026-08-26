import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import init_db, SessionLocal
from database.seeds.seed_data import seed_database
from apps.backend.src.websocket_hub import ws_hub
from apps.backend.src.demo_simulator import simulator

# Import Routers
from apps.backend.src.routes.system import router as system_router
from apps.backend.src.routes.environmental import router as env_router
from apps.backend.src.routes.video import router as video_router
from apps.backend.src.routes.copilot import router as copilot_router
from apps.backend.src.routes.reports import router as reports_router

# Configure Structured Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":"%(message)s"}'
)
logger = logging.getLogger("aeromind.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] Initializing AeroMind ClimateGuard Physical AI System...")
    init_db()
    
    # Run database seed to ensure clean physical locations and baseline models exist
    db = SessionLocal()
    try:
        seed_database(db)
        logger.info("[STARTUP] Database schema and baseline facility seeds initialized.")
    except Exception as e:
        logger.error(f"[STARTUP] Seed initialization error: {e}")
    finally:
        db.close()

    # Start demo simulator only if in demo mode
    app_mode = os.getenv("APP_MODE", "demo").lower()
    if app_mode != "production" or os.getenv("FORCE_DEMO"):
        simulator.start()
        logger.info("[STARTUP] Real-time Demo Simulator active.")
    else:
        logger.info("[STARTUP] Running in PRODUCTION mode (Demo simulator disabled).")

    yield

    logger.info("[SHUTDOWN] Shutting down AeroMind ClimateGuard...")
    simulator.stop()

app = FastAPI(
    title="AeroMind ClimateGuard — Physical AI Operations Platform",
    description="Transforms environmental and visual signals into real-time situational awareness, risk assessment, and autonomous response.",
    version="1.0.0",
    lifespan=lifespan
)

# Request ID & Observability Middleware
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    response: Response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    # Log requests with structured JSON
    if not request.url.path.startswith("/health"):
        logger.info(f'{{"request_id":"{request_id}", "method":"{request.method}", "path":"{request.url.path}", "status":{response.status_code}, "latency_ms":{process_time:.2f}}}')
    
    return response

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(system_router)
app.include_router(env_router)
app.include_router(video_router)
app.include_router(copilot_router)
app.include_router(reports_router)

# Mount static files for snapshots
os.makedirs("data/processed/snapshots", exist_ok=True)
app.mount("/snapshots", StaticFiles(directory="data/processed/snapshots"), name="snapshots")

# Real-Time WebSocket Endpoint with Heartbeat Support
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_hub.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            # Heartbeat ping/pong handling
            if msg == "ping" or '"type":"ping"' in msg or '"event_type":"ping"' in msg:
                await websocket.send_text('{"event_type":"pong","timestamp":"' + time.strftime("%Y-%m-%dT%H:%M:%SZ") + '"}')
            else:
                await websocket.send_text(f'{{"event_type":"ack","received_bytes":{len(msg)}}}')
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as e:
        logger.warning(f"[WebSocket] Disconnected with error: {e}")
        ws_hub.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.backend.src.main:app", host="0.0.0.0", port=8000, reload=True)
