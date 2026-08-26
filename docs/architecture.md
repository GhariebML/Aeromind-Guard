# AeroMind ClimateGuard — Architectural Specification

## 1. Executive Summary
AeroMind ClimateGuard is a modular Physical AI intelligence platform uniting environmental sensor telemetry, thermal forecasting, and real-time computer vision tracking into an autonomous, explainable situational operations center.

## 2. Layered Architecture

### 2.1 Ingestion & Normalization Layer (`services/ingestion`)
- **`EnvironmentalDataProvider`**: Abstract interface decoupling physical sensor gateways and API providers from business logic.
- **`FortyGuardProvider`**: Enterprise client featuring exponential backoff, rate limit backoff (HTTP 429), and non-blocking initialization when unconfigured (`ProviderStatus.NOT_CONFIGURED`).
- **`DemoEnvironmentalProvider`**: Deterministic synthetic diurnal cycle simulation for zero-dependency local runs.
- **Unified UTC Data Schema**: Standardizes ambient temperature, surface temperature, relative humidity, particulate air quality ($PM_{2.5}$), and wind velocity.

### 2.2 Anomaly Detection Layer (`services/analytics`)
- Rolling Gaussian statistical windows.
- Z-Score divergence estimation: $Z = \frac{x - \mu}{\sigma}$.
- Discrete first-derivative rate-of-change computation ($\Delta T / \Delta t$ per hour).
- Persistence tracking to eliminate transient noise.

### 2.3 Computer Vision & Perception (`apps/ai_engine`)
- **`YOLODetector`**: Ultralytics YOLOv8 inference with resilient HSV color-space & motion contour fallback.
- **`BoTSORTTracker`**: Multi-object tracker preserving object identities across frames, calculating velocity vectors and evaluating point-in-polygon danger zone intrusions.

### 2.4 Correlation Engine (`services/correlation`)
- Evaluates composite risk rules combining environmental sensor spikes with optical evidence (e.g. Temperature $>34^\circ\text{C}$ + Smoke Detection $\rightarrow$ Emergency Suppression Trigger).

### 2.5 Deterministic Risk Engine (`services/risk_engine`)
- Computes bounded 0–100 risk score based on weighted, explainable factors.
- Guaranteed zero numerical hallucinations (deterministic code calculates risk; LLMs only summarize and explain).

### 2.6 Decision & Alert Engines (`services/decision_engine`, `services/alert_engine`)
- Emits prioritized operational directives with exact recommended protocol steps.
- Manages complete alarm lifecycle: `OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`.

### 2.7 AI Copilot (`services/copilot`)
- Grounded in real-time SQL queries. Uses Ollama local LLMs (`llama3`) for conversational natural language explanations with deterministic telemetry grounding.

### 2.8 Operations Center Console (`apps/frontend`)
- High-density React 19 + TailwindCSS + Lucide Icons + Three.js 3D Digital Twin + Recharts charts + Real-time WebSockets.
