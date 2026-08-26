# AeroMind ClimateGuard — Comprehensive System Reality Audit

## 1. Executive Summary & Module Status Matrix

| Module | Claimed Capability | Actual Status | Identified Gaps / Production Weaknesses | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | FortyGuard + Demo Provider | **PARTIAL** | Missing strict `APP_MODE=production` guard; simulator ran unconditionally. | **P1** |
| **Video Sources & RTSP** | MP4, Webcam, RTSP streams | **PARTIAL** | Lacked RTSP connection timeout, auto-reconnect, dropped-frame accounting, and codec health. | **P1** |
| **Video Job Persistence** | Asynchronous Video Jobs | **PARTIAL** | Jobs stored in in-memory dictionary; lost upon process restart. | **P1** |
| **Correlation Engine** | Multi-Modal Threat Fusion | **PARTIAL** | Lacked time-window sliding buffers and duplicate alert suppression (risk of alert storms). | **P1** |
| **WebSocket Hub** | Live Real-Time Stream | **PARTIAL** | Event naming was unstandardized (`TELEMETRY_UPDATE` vs `telemetry.updated`); lacked ping/pong heartbeat. | **P1** |
| **Alert Engine** | Full Alert Lifecycle | **PARTIAL** | Lacked persistent audit history table and reopen action. | **P2** |
| **AI Copilot Grounding** | Grounded Local LLM | **REAL** | Structured SQL grounding works; needs intent classification and explicit record citations. | **P2** |
| **Security & Middleware** | Enterprise Hardening | **PARTIAL** | Missing request ID middleware, file upload sanitization, and path traversal validation on static snapshots. | **P1** |
| **Digital Twin (3D)** | Interactive Three.js Scene | **REAL** | Renders correctly; needs interactive click raycasting to inspect sector telemetry directly. | **P2** |
| **Observability** | Structured Logs & Latency | **PARTIAL** | Missing request-level correlation IDs and benchmark metrics. | **P2** |
| **Test Coverage** | Automated Validation | **PARTIAL** | 11 tests exist, but lacks failure mode simulations, RTSP errors, security checks, and load tests. | **P1** |

---

## 2. Detailed Issue Catalog & Remediation Plan

### Issue 1 [P1]: Unconditional Simulation in Production Mode
- **Location**: `apps/backend/src/main.py`, `apps/backend/src/demo_simulator.py`
- **Root Cause**: `simulator.start()` was called unconditionally in lifespan without checking `APP_MODE`.
- **Impact**: Synthetic data could silently pollute production databases.
- **Fix**: Introduce `APP_MODE` environment variable (`production` vs `demo`). In production mode, reject synthetic sources unless explicitly commanded.

### Issue 2 [P1]: RTSP Video Stream Ingestion Weakness
- **Location**: `apps/ai_engine/video_analytics.py`
- **Root Cause**: Only raw OpenCV `VideoCapture` on file paths was used.
- **Impact**: No reconnect logic, frame timeouts, stream health telemetry, or dropped-frame tracking for physical IP/RTSP cameras.
- **Fix**: Implement `VideoSource` abstract class with `FileVideoSource` and `RTSPVideoSource` featuring reconnection loop, frame timeout, FPS computation, and health reporting.

### Issue 3 [P1]: In-Memory Video Analysis Jobs
- **Location**: `apps/backend/src/routes/video.py`
- **Root Cause**: `VIDEO_JOBS` was stored in memory dict.
- **Impact**: Process restarts would lose running/completed video job status.
- **Fix**: Persist video job status and reports to database table `video_jobs`.

### Issue 4 [P1]: Alert Storms & Lack of Correlation Deduplication
- **Location**: `services/correlation/engine.py`, `services/alert_engine/engine.py`
- **Root Cause**: Every periodic reading could trigger a new alert if conditions persisted.
- **Impact**: Operators flooded with duplicate alarms.
- **Fix**: Add sliding window deduplication and suppression buffer (e.g. 5-minute cooldown for identical rule/location combinations unless severity escalates).

### Issue 5 [P1]: WebSocket Event Taxonomy & Heartbeat
- **Location**: `apps/backend/src/websocket_hub.py`, `apps/frontend/src/App.tsx`
- **Root Cause**: Messages used non-standard payloads (`TELEMETRY_UPDATE`).
- **Impact**: Inconsistent event contracts and potential zombie connections.
- **Fix**: Standardize event taxonomy (`telemetry.updated`, `detection.created`, `hazard.detected`, `risk.updated`, `alert.created`, `alert.updated`, `camera.status`, `system.status`) with ping/pong heartbeat.

### Issue 6 [P1]: Security & Input Path Traversal
- **Location**: `apps/backend/src/routes/video.py`, `apps/backend/src/main.py`
- **Root Cause**: Uploaded filenames and snapshot paths were not strictly sanitized.
- **Impact**: Potential path traversal risks on custom file uploads.
- **Fix**: Enforce strict filename UUID hashing, sanitize all uploaded file extensions, and validate paths.

### Issue 7 [P1]: Expanded Test Suite & Negative / Failure Mode Testing
- **Location**: `tests/`
- **Root Cause**: Only 11 basic tests existed; no negative or failure recovery tests.
- **Impact**: Inability to verify system behavior during FortyGuard outage, database disconnect, RTSP stream interruption, or Ollama unavailability.
- **Fix**: Build comprehensive test suites across `tests/unit/`, `tests/integration/`, `tests/ai/`, `tests/realtime/`, `tests/security/`.
