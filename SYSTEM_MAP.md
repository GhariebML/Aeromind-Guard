# AeroMind ClimateGuard — System Architecture Map

## 1. Top-Level Monorepo Map

```
aeromind-climateguard/
├── apps/
│   ├── ai_engine/               # Computer Vision, Object Detection & Tracking Subsystem
│   │   ├── detector.py          # BaseDetector & YOLODetector (Neural + Resilient Fallback)
│   │   ├── tracker.py           # BaseTracker & BoTSORTTracker (Trajectories, Velocity, Zones)
│   │   ├── video_sources.py     # VideoSource Abstraction (FileVideoSource, RTSPVideoSource)
│   │   └── video_analytics.py   # VideoAnalyticsEngine Pipeline
│   ├── backend/                 # FastAPI Application & Operations Engine
│   │   └── src/
│   │       ├── hardware.py      # Telemetry: CPU, GPU, CUDA, VRAM, RAM detection
│   │       ├── websocket_hub.py # Real-Time Event Hub (telemetry.updated, risk.updated, etc.)
│   │       ├── demo_simulator.py# Deterministic Simulator (active only in DEMO mode)
│   │       ├── main.py          # Lifespan, Routing, CORS, Middleware & Error Handlers
│   │       └── routes/          # REST Endpoint Controllers (System, Env, Video, Copilot, Reports)
│   └── frontend/                # React 19 + TypeScript + Vite + TailwindCSS + Three.js
│       └── src/
│           ├── components/      # Operations Console, Digital Twin, Analytics, Alerts, Copilot
│           ├── services/api.ts  # Typed API & WebSocket Client
│           ├── types/index.ts   # Domain Schemas & Type Contracts
│           └── App.tsx          # Root State Orchestration & WebSocket Dispatcher
├── services/
│   ├── ingestion/               # Provider Abstractions (FortyGuard, DemoProvider, Pipeline)
│   ├── analytics/               # Statistical Anomaly Detection (Z-Score, Rate-of-Change)
│   ├── correlation/             # Multi-Modal Spatial-Temporal Threat Correlation Engine
│   ├── risk_engine/             # Deterministic Explainable 0-100 Risk Engine
│   ├── decision_engine/         # Actionable AI Operational Directives Engine
│   ├── event_engine/            # Unified Physical AI Event Bus & Normalizer
│   ├── alert_engine/            # Alert Lifecycle (OPEN, ACKNOWLEDGED, RESOLVED) & Audit Engine
│   ├── prediction_engine/       # Predictive Thermal & Risk Trajectory Forecaster
│   └── copilot/                 # Grounded AI Copilot (Ollama LLM + SQL Context Grounding)
├── database/
│   ├── connection.py            # SQLAlchemy Multi-Engine (PostgreSQL / SQLite Dual Engine)
│   ├── models.py                # Normalized Relational Models
│   ├── schemas.py               # Pydantic Request/Response Contracts
│   └── seeds/seed_data.py       # Deterministic Seeder for Monitored Zones & Models
├── data/
│   ├── raw/uploads/             # Video uploads
│   ├── processed/snapshots/     # Incident snapshots & frames
│   └── samples/                 # Test MP4 video assets
├── docker/                      # Dockerfiles & Nginx Configurations
├── docs/                        # Complete Technical & Operational Documentation
└── tests/                       # Unit, Integration, AI, Realtime, Security & E2E Suites
```

---

## 2. End-to-End Data & Event Flow

```
[ Physical Sensors / RTSP Streams / FortyGuard API ]
                       │
                       ▼
      [ Ingestion Layer & Normalization ]
    (Schema validation, UTC timestamping, Quality check)
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
 [ AI Perception & Tracking ] [ Statistical Anomaly Engine ]
 (YOLOv8 + BoT-SORT Tracking) (Rolling mean, std, Z-score, RoC)
            │                     │
            └──────────┬──────────┘
                       ▼
        [ Multi-Modal Correlation Engine ]
  (Spatial-temporal windowing & deduplication)
                       │
                       ▼
        [ Deterministic Risk Engine ]
    (0-100 score with exact factor weights)
                       │
                       ▼
       [ Decision & Alert Engines ]
  (Prioritized directives + OPEN/ACK/RESOLVED lifecycle)
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   [ PostgreSQL / SQLite ]   [ WebSocket Hub ]
(Persistent audit trail)  (Event taxonomy stream)
                                    │
                                    ▼
                     [ Operations Console (React + Three.js) ]
                                    │
                                    ▼
                          [ Grounded AI Copilot ]
```

---

## 3. Communication & Contract Interfaces

- **REST API**: HTTP JSON with explicit Pydantic request/response schemas and standardized error envelopes.
- **WebSocket Protocol**: JSON stream adhering to strict event taxonomy:
  - `telemetry.updated`
  - `detection.created`
  - `hazard.detected`
  - `risk.updated`
  - `alert.created`
  - `alert.updated`
  - `camera.status`
  - `system.status`
- **Database Model Sync**: Relational persistence of all critical metrics ensuring restart durability.
