# AeroMind ClimateGuard — API Architecture & Contracts

## 1. Overview
The AeroMind ClimateGuard platform exposes REST APIs and real-time WebSockets built on FastAPI.

- **Base URL**: `http://<host>:8000/api/v1`
- **WebSocket URL**: `ws://<host>:8000/ws`
- **Interactive Documentation**: `http://<host>:8000/docs` (Swagger UI)

---

## 2. Core REST Endpoints

### System & Diagnostics
- `GET /api/v1/health`: Lightweight health check for load balancers.
- `GET /api/v1/system/status`: Detailed telemetry, CPU/GPU/CUDA status, active WebSocket clients, FortyGuard provider status.
- `POST /api/v1/system/demo-mode/toggle`: Explicitly toggles synthetic simulator (allowed in demo mode).

### Environmental & Physical Locations
- `GET /api/v1/locations`: List all registered monitored physical zones and baseline temperatures.
- `POST /api/v1/locations`: Register a new physical sector.
- `GET /api/v1/temperature/current`: Latest temperature telemetry per sector.
- `GET /api/v1/temperature/history`: Historical telemetry filtered by time window.
- `GET /api/v1/forecast`: 24-hour predictive thermal & risk projections.

### Risk, Incidents & Alerts
- `GET /api/v1/risk/current`: Current deterministic 0–100 risk score and factor breakdown per location.
- `GET /api/v1/events`: Chronological feed of visual and environmental physical events.
- `GET /api/v1/alerts`: Active and historical alarms.
- `POST /api/v1/alerts/{id}/acknowledge`: Mark alert as ACKNOWLEDGED with operator audit note.
- `POST /api/v1/alerts/{id}/resolve`: Mark alert as RESOLVED with operator audit note.
- `GET /api/v1/decisions`: Prioritized emergency response directives.

### Computer Vision & Video Analytics
- `POST /api/v1/video/analyze`: Submit video file, sample, or RTSP stream for asynchronous perception and tracking.
- `GET /api/v1/video/jobs/{id}`: Poll status, progress percentage, effective FPS, and detection summaries.
- `GET /api/v1/video/events`: Feed of visual hazard events and optical snapshot references.
- `GET /api/v1/video/samples`: List pre-packaged synthetic validation videos.

### AI Copilot & Incident Export
- `POST /api/v1/copilot/query`: Ask grounded operational questions backed by live SQL context.
- `GET /api/v1/reports/export`: Download comprehensive incident data in `json` or `csv` format.

---

## 3. Real-Time WebSocket Protocol (`/ws`)

### Event Taxonomy
All WebSocket payloads adhere to the standard envelope:
```json
{
  "event_type": "telemetry.updated",
  "event_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "correlation_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "timestamp": "2026-08-25T14:00:00Z",
  "data": { ... }
}
```

### Supported Event Types:
1. `telemetry.updated`: Ingested sensor metrics & rate-of-change updates.
2. `risk.updated`: Updated deterministic risk score and factor contributions.
3. `alert.created`: New alarm triggered.
4. `alert.updated`: Status change on existing alarm (ACKNOWLEDGED / RESOLVED / REOPENED).
5. `camera.status`: Stream health, FPS, and dropped frames telemetry.
6. `video.event`: Live visual hazard extraction (flame, smoke, intrusion).
7. `system.status`: Hardware telemetry update.
8. `ping` / `pong`: 15-second bidirectional heartbeat.
