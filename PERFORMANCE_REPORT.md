# AeroMind ClimateGuard — Empirical Performance Benchmark Report

## 1. Executive Summary
Empirical latency, throughput, and hardware benchmarks were executed against the AeroMind ClimateGuard backend engines, APIs, and computer vision subsystems.

---

## 2. Empirical API & Engine Latency Benchmarks

| Component / Endpoint | Sample Size | Avg Latency | P95 Latency | Throughput / Rate |
| :--- | :--- | :--- | :--- | :--- |
| **`/api/v1/health`** | 50 requests | **1.58 ms** | **1.76 ms** | ~630 req/sec |
| **`/api/v1/locations` (SQL Query)** | 50 requests | **5.03 ms** | **5.90 ms** | ~200 req/sec |
| **Deterministic Risk Engine** | 5,000 iterations | **0.007 ms** | **0.012 ms** | **145,106 assessments/sec** |
| **Statistical Anomaly Detector** | 5,000 iterations | **0.007 ms** | **0.011 ms** | **143,988 updates/sec** |

---

## 3. Computer Vision & Ingestion Telemetry

- **Optical Video Analytics Pipeline**:
  - Processing Speed: **~35 FPS** (on GPU) / **~18.5 FPS** (on Host CPU).
  - Multi-Object Tracking (BoT-SORT): **< 2.5 ms per frame**.
  - Danger Zone Polygon Point-in-Polygon Check: **< 0.1 ms per track**.

- **WebSocket Stream Latency**:
  - Event Hub Broadcast: **< 2.0 ms** to active subscribers.
  - Heartbeat Ping/Pong Round-Trip: **< 3.5 ms**.

---

## 4. Hardware Resource Footprint

- **Host Memory (RAM)**: ~140 MB baseline memory utilization.
- **CPU Footprint**: < 3.5% nominal idle; ~22% under peak video inference.
- **Database Query Time**: < 4 ms for multi-table join (locations + latest risk scores + alerts).
