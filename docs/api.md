# AeroMind ClimateGuard — REST & WebSocket API Specification

Base URL: `http://localhost:8000/api/v1`

---

## 1. System & Health Endpoints

### `GET /api/v1/health`
Returns service uptime and operational status.

### `GET /api/v1/system/status`
Returns full hardware telemetry (CPU, RAM, GPU, CUDA, VRAM), database connectivity, and registered provider gateways (FortyGuard connection status and latency).

### `POST /api/v1/system/demo-mode/toggle`
Toggles background deterministic synthetic demonstration stream.

---

## 2. Telemetry & Forecasts

### `GET /api/v1/locations`
Lists all physical monitored sectors with baseline temperatures, risk thresholds, and GPS coordinates.

### `GET /api/v1/temperature/current`
Returns current ambient, surface, and heat index temperatures for all sectors.

### `GET /api/v1/temperature/history?location_id={id}&limit=50`
Returns historical temperature time-series.

### `GET /api/v1/forecast?location_id={id}`
Returns 24-hour predictive thermal trajectory with confidence intervals and predicted risk score.

---

## 3. Alerts & Risk Intelligence

### `GET /api/v1/risk/current`
Returns real-time risk scores (0–100) and factor breakdowns.

### `GET /api/v1/alerts?status={OPEN|ACKNOWLEDGED|RESOLVED}&severity={CRITICAL|HIGH|MEDIUM|LOW}`
Lists filtered alarm queue.

### `POST /api/v1/alerts/{id}/acknowledge`
Acknowledge open alarm with operator name and audit timestamp.

### `POST /api/v1/alerts/{id}/resolve`
Resolve alarm with operator name.

### `GET /api/v1/decisions`
Returns actionable AI decisions and emergency response protocols.

---

## 4. Video & Computer Vision

### `POST /api/v1/video/analyze`
Submits MP4 video for asynchronous YOLO + BoT-SORT object detection, trajectory tracking, and danger zone analysis.

### `GET /api/v1/video/jobs/{job_id}`
Returns video analysis job progress, processed frames, FPS, and detection summaries.

### `GET /api/v1/video/events`
Returns visual hazards identified by computer vision.

---

## 5. Grounded AI Copilot

### `POST /api/v1/copilot/query`
Executes natural language reasoning strictly grounded in database telemetry.

Payload:
```json
{
  "query": "What are the highest risk events today?"
}
```

---

## 6. Reports & Export

### `GET /api/v1/reports/export?format={json|csv}`
Exports complete operational report with incident logs, factor attributions, and AI decisions.

---

## 7. Real-Time WebSocket

### `WS /ws`
Connects to live platform event stream. Dispatches messages:
- `TELEMETRY_UPDATE`
- `ALERT_CREATED`
- `ALERT_ACKNOWLEDGED`
- `ALERT_RESOLVED`
