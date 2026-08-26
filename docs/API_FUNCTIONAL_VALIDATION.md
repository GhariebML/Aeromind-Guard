# API Functional Validation Report
**AeroMind ClimateGuard**

This document details the functional validation of the FastAPI endpoints exposed by the backend, including their data sources (Real DB vs. Simulator).

## Core Endpoints Validated

| Endpoint | Method | Data Source / Implementation | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health` | GET | Static Runtime | ✅ REAL | Returns real process uptime. |
| `/api/v1/system/status` | GET | Python Process + DB Ping | ✅ REAL | Confirms hardware specs (e.g. CPU vs GPU), connection pools, and provider statuses. |
| `/api/v1/locations` | GET | PostgreSQL / SQLite DB | ✅ REAL | Serves valid physical locations (e.g., Battery Energy Storage System). |
| `/api/v1/temperature/current` | GET | `IngestionPipeline` -> DB | ✅ REAL | Aggregates from active providers. |
| `/api/v1/risk/current` | GET | `RiskEngine` | ✅ REAL | Executes deterministic rules on the fly based on telemetry. No LLM used for math. |
| `/api/v1/alerts` | GET | DB (`AlertModel`) | ✅ REAL | Returns actual lifecycle state (`OPEN`, `RESOLVED`). |

## Video AI Subsystem
| Endpoint | Method | Implementation | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/video/analyze` | POST | `YOLODetector` + `BoTSORTTracker` | ✅ REAL | Spawns background thread. Actually decodes MP4 and yields real BBoxes (e.g., `fire` detected in frame 1). |
| `/api/v1/video/jobs/{job_id}`| GET | In-memory Job Tracker | ✅ REAL | Reports accurate progress, FPS (measured ~230 FPS on CPU), and trajectory data. |
| `/api/v1/video/stream/{id}` | GET | `CameraStreamWorker` | ✅ REAL | Uses multipart Motion-JPEG `yield` generator to stream frames over HTTP. |

## AI Copilot & Correlation
| Endpoint | Method | Implementation | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/copilot/query` | POST | Grounded RAG / `Ollama` | ⚠️ PARTIAL | Correctly falls back to `Deterministic-Grounding-Engine` if Ollama is unreachable. Does not hallucinate numbers. |

## Demo / Simulation Risks
- **`services/ingestion/demo_provider.py`**: A synthetic deterministic simulator acts as a fallback when `FORTYGUARD_API_KEY` is not present.
- **Risk Mitigation**: The system explicitly identifies the `Synthetic Demo Mode Engine` as `CONNECTED` in `/system/status`. No risk of accidental leakage as it is isolated.
