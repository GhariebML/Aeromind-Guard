<div align="center">

# 🌍 AeroMind ClimateGuard

**Physical AI Operations Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-cyan.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg?style=for-the-badge&logo=react)](https://react.dev)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL_2.0-000000.svg?style=for-the-badge&logo=three.js)](https://threejs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python)](https://www.python.org)

<img src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop" alt="AeroMind ClimateGuard Hero" width="100%" style="border-radius: 10px; margin-top: 20px; margin-bottom: 20px;"/>

**AeroMind ClimateGuard** is an enterprise-grade Physical AI intelligence platform that transforms multi-modal environmental telemetry, meteorological forecasts, and visual computer vision signals into actionable situational awareness, deterministic risk assessment, autonomous operational decision protocols, and 3D digital twin spatial intelligence.

</div>

---

## 🚀 Key Capabilities

| Capability | Description |
| :--- | :--- |
| 🛡️ **Deterministic Physical AI Risk Engine** | Computes continuous 0–100 risk scores with transparent factor attribution (temperature elevation, rate-of-change spikes, optical fire/smoke confirmation, danger zone proximity). Zero LLM hallucination in mathematical calculations. |
| 🔗 **Multi-Modal Correlation Engine** | Evaluates spatial-temporal rules fusing visual hazards (smoke/flame) with thermal telemetry and personnel tracking. |
| 👁️ **Computer Vision & Tracking Pipeline** | YOLOv8 object detection paired with BoT-SORT multi-object trajectory tracking and perimeter danger zone breach detection. |
| 🌐 **FortyGuard & Multi-Provider Ingestion** | Resilient provider abstraction with exponential backoff, rate limiting, and zero-crash initialization (`NOT_CONFIGURED` graceful fallback). |
| 🗺️ **Interactive 3D Digital Twin** | WebGL Three.js spatial visualization of monitored zones, heat halos, and animated camera frustum cones. |
| 🤖 **Grounded AI Copilot** | Local Ollama LLM integration strictly grounded in real database context with deterministic fallback when offline. |
| ⚡ **Real-Time WebSocket Hub** | Low-latency live stream dispatching telemetry updates, anomaly triggers, and alarm lifecycle changes. |

---

## 🧠 System Architecture

```mermaid
flowchart TD
    subgraph PhysicalWorld [Physical World]
        Sensors[Sensors / CCTV / Thermal / APIs]
    end

    subgraph Ingestion [Ingestion Layer]
        FG[FortyGuard / DemoProvider]
    end

    subgraph Core [Core Platform]
        Norm[Normalization & Validation Layer]
        Perception[AI Perception: YOLO + BoT-SORT]
        Anomaly[Statistical Anomaly Engine]
        Fusion[Correlation Engine: Threat Fusion]
        Risk[Deterministic Risk Engine]
        Decision[Decision & Alert Engines]
    end

    subgraph UI [Operator Operations Center]
        Dashboard[Live Intel, Video AI, Digital Twin]
    end

    PhysicalWorld --> Ingestion
    Ingestion --> Norm
    Norm --> Perception
    Norm --> Anomaly
    Perception --> Fusion
    Anomaly --> Fusion
    Fusion --> Risk
    Risk --> Decision
    Decision --> UI
```

---

## 💻 Quick Start (Local Development)

### 1. Prerequisites
- **Python:** 3.11+
- **Node.js:** 18+ and npm
- **Optional:** Docker & Docker Compose
- **Optional:** Ollama with `llama3` installed

### 2. Backend Setup
```bash
# Clone and enter workspace
git clone https://github.com/aeromind/climateguard.git
cd aeromind-climateguard

# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Start backend server with automatic seeder and simulator
uvicorn apps.backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd apps/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
> **Note:** Open **http://localhost:5173** to access the operations center.

---

## 🐳 Docker Compose Deployment

```bash
# Copy and configure environment variables (optional FortyGuard key)
cp .env.example .env

# Build and start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build -d
```
- **Operations Center Dashboard**: `http://localhost:3000`
- **FastAPI REST API Docs**: `http://localhost:8000/docs`

---

## 🧪 Running Automated Tests

```bash
$env:PYTHONPATH="."
pytest -v
```

---

## 📚 Documentation Directory

Explore the complete documentation for an in-depth understanding of the platform:

- 🏗️ [`docs/architecture.md`](docs/architecture.md) — Comprehensive technical architecture
- ⚙️ [`docs/setup.md`](docs/setup.md) — Installation and environment guide
- 🔌 [`docs/api.md`](docs/api.md) — REST & WebSocket API specification
- 🧮 [`docs/risk-engine.md`](docs/risk-engine.md) — Deterministic risk calculation formulation
- 🎥 [`docs/video-analytics.md`](docs/video-analytics.md) — Computer vision and BoT-SORT tracking
- 🎤 [`docs/demo.md`](docs/demo.md) — Hackathon and demonstration guide
- ✅ [`docs/FINAL_VALIDATION.md`](docs/FINAL_VALIDATION.md) — Feature verification and test results
