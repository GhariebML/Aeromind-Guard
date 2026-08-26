# AeroMind ClimateGuard — Implementation Plan

## 1. Current Repository Assessment
- **Status**: Clean workspace (`d:\AeroMind ClimateGuard`).
- **Target**: Full-stack Physical AI Intelligence Platform combining Environmental Telemetry, Computer Vision, Correlation, Deterministic Risk Assessment, Decision Layer, Real-time WebSockets, Digital Twin (Three.js), and Operator Console.
- **Key Tenet**: No mockups, no fake data, no superficial dashboards. Deterministic risk engine (LLMs do not calculate numerical risk, they explain decisions grounded in data). Graceful fallback for all external services (FortyGuard API, NVIDIA CUDA, Ollama LLM, PostgreSQL).

---

## 2. Target System Architecture

```
Physical World / Cameras / APIs / Sensors
                 │
                 ▼
     [ Ingestion Pipeline ]
  (FortyGuardProvider / DemoProvider / IoT / Video)
                 │
                 ▼
   [ Normalization & Validation ] (UTC, Pydantic Schema)
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
[ AI Perception Layer ] [ Anomaly Detection Layer ]
(YOLO + BoT-SORT Tracking)  (Rolling Stats, Z-Score, RoC)
      │                     │
      └──────────┬──────────┘
                 ▼
     [ Correlation Engine ]
 (Rule-based Spatial-Temporal Fusion)
                 │
                 ▼
       [ Deterministic Risk Engine ]
    (0-100 Score, Explainable Factor Breakdown)
                 │
                 ▼
      [ Prediction & Decision Layer ]
   (Actionable Prioritized Operational Directives)
                 │
                 ▼
      [ Event & Alert Engine ]
   (Multi-channel: WebSocket, App, Webhook)
                 │
                 ▼
  [ Operator Console (React + Vite + Three.js) ]
  (Overview, Live Intel, Video, Map, 3D Digital Twin,
   Analytics, Alerts, AI Copilot, System Health)
```

---

## 3. Modular Monorepo Layout

```
aeromind-climateguard/
├── apps/
│   ├── backend/               # FastAPI backend + WebSocket Hub + REST APIs
│   │   └── src/
│   ├── frontend/              # React + TypeScript + Vite + TailwindCSS + Three.js
│   │   └── src/
│   ├── ai-engine/             # Perception, Object Detection, Tracking & Video Analytics
│   └── worker/                # Background task processor for video analytics
├── services/
│   ├── ingestion/             # FortyGuard & Environmental Providers
│   ├── analytics/             # Anomaly Detection & Statistical Models
│   ├── correlation/           # Environmental + Visual Correlation Engine
│   ├── risk-engine/           # Deterministic Risk Calculation (0-100)
│   ├── prediction-engine/     # Predictive Trend & Risk Forecasting
│   ├── decision-engine/       # Actionable AI Decisions & Recommendations
│   ├── event-engine/          # Unified Event Generation & Storage
│   ├── alert-engine/          # Severity Triage, Acknowledgement & Dispatch
│   └── copilot/               # Grounded Local LLM Copilot (Ollama interface)
├── database/
│   ├── models/                # SQLAlchemy Models (PostgreSQL / SQLite dual-support)
│   ├── schemas/               # Pydantic validation schemas
│   └── seeds/                 # Realistic seed data & scenario simulations
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/               # Synthetic/sample video assets
├── configs/
│   ├── development/
│   └── production/
├── docs/                      # Full technical documentation suite
├── docker/                    # Dockerfiles & container configs
├── tests/                     # Unit, Integration, and E2E test suite
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Implementation Phases

### Phase 1: Repository Foundation & Core Architecture
- Create monorepo directory layout.
- Configure backend runtime, database configuration (SQLAlchemy + SQLite/PostgreSQL dynamic engine), database models, and schemas.
- Set up FastAPI app structure with health checks, hardware telemetry (CPU, GPU, CUDA, RAM, VRAM detection), and CORS.

### Phase 2: Ingestion Layer & FortyGuard Provider
- Define `EnvironmentalDataProvider` interface.
- Implement `FortyGuardProvider` with authentication, backoff/retry, validation, and structured error reporting.
- Implement `DemoEnvironmentalProvider` for deterministic simulation without API keys.
- Unified ingestion pipeline converting all readings to UTC-standardized records.

### Phase 3: AI Engine, Perception & Tracking
- Implement `BaseDetector` and `YOLODetector` (with fallback lightweight computer vision detector).
- Implement `BaseTracker` and `BoTSORTTracker` (with Euclidean trajectory and velocity estimation).
- Implement `VideoAnalyticsEngine` supporting MP4 video processing, frame sampling, event trigger generation, and snapshot generation.

### Phase 4: Correlation, Anomaly Detection & Risk Engine
- Statistical Anomaly Detector (rolling mean, std dev, z-score, rate of change, persistence).
- Rule-based Spatial-Temporal `CorrelationEngine` fusing visual detections (smoke, fire, perimeter breach) with environmental metrics (heat spikes, humidity drops).
- Deterministic `RiskEngine` calculating 0–100 risk score with full factor attribution and severity classification.
- Predictive Risk & Trend forecasting engine.

### Phase 5: Event, Decision & Alert Engines
- Unified `EventEngine` for `TEMPERATURE_ANOMALY`, `SMOKE_DETECTED`, `FIRE_DETECTED`, `PERSON_IN_DANGER_ZONE`, `CROWD_EVENT`, etc.
- `DecisionEngine` generating explainable operational actions and priority responses.
- `AlertEngine` with state lifecycle (`OPEN`, `ACKNOWLEDGED`, `RESOLVED`) and WebSocket dispatch.

### Phase 6: AI Copilot (Ollama Grounded Engine)
- Grounded query engine: retrieves active alarms, current risk factors, top anomalies, and sensor stats from database.
- Prompts Ollama (or responds with clear diagnostic status if Ollama is not active).
- Never invents sensor values or calculates numeric risk via LLM.

### Phase 7: REST & WebSocket API Suite
- REST Endpoints: `/api/v1/health`, `/api/v1/system/status`, `/api/v1/temperature`, `/api/v1/environment`, `/api/v1/forecast`, `/api/v1/anomalies`, `/api/v1/events`, `/api/v1/alerts`, `/api/v1/risk`, `/api/v1/cameras`, `/api/v1/detections`, `/api/v1/tracks`, `/api/v1/recommendations`, `/api/v1/copilot`, `/api/v1/video/analyze`, `/api/v1/reports/export`.
- Real-time WebSocket hub broadcasting live sensor readings, anomalies, risk updates, and alerts.

### Phase 8: Enterprise Frontend (Operations Center)
- React 19 + TypeScript + Vite + TailwindCSS application.
- Dark enterprise command center design with high information density.
- Modules:
  1. **Overview Dashboard**: System Risk Meter, Status Cards, Live Alerts, Environmental Gauges.
  2. **Live Intelligence**: Real-time streaming events, anomaly telemetry, decision feed.
  3. **Video Intelligence**: Video analysis player, bounding box rendering, tracking paths, video upload/job monitor.
  4. **Spatial Map**: Facility/region layout with camera cones, sensor coordinates, heat zones.
  5. **3D Digital Twin**: Three.js interactive 3D model of monitored facility, real-time risk heat zones and alert anchors.
  6. **Analytics & Correlation**: Historical charts, correlation matrices, multi-variable trend lines.
  7. **Alerts Management**: Acknowledge/resolve workflows, severity filtering, audit logs.
  8. **AI Copilot**: Interactive grounded chat with quick prompt suggestions.
  9. **System Health**: Telemetry, GPU/CUDA stats, FortyGuard connection status, latency metrics.

### Phase 9: Testing, Sample Data & Verification
- Unit tests for risk scoring, anomaly detection, normalization, correlation rules, event creation.
- Integration tests for REST endpoints and WebSocket feeds.
- Sample video generation utility and deterministic demo simulation engine.
- Complete documentation suite (`README.md`, `architecture.md`, `setup.md`, `api.md`, `risk-engine.md`, `video-analytics.md`, `demo.md`, `FINAL_VALIDATION.md`).

---

## 5. Risk Management & Fallbacks
1. **Hardware Fallback**: Automatically detects CPU if CUDA is unavailable; avoids hard crashes.
2. **API Fallback**: If `FORTYGUARD_API_KEY` is not set, system shows `NOT_CONFIGURED` without failing startup.
3. **Database Dual-Engine**: Connects to PostgreSQL if configured, seamlessly uses SQLite if PostgreSQL is absent in local dev.
4. **LLM Fallback**: If Ollama service is not running, Copilot provides structured data summaries and clear offline notification.
