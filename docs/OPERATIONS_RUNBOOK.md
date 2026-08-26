# AeroMind ClimateGuard — Operator Runbook & Incident Protocols

## 1. Operator Command Center Workflow
The AeroMind ClimateGuard platform operates as an autonomous, multi-modal situational intelligence hub. Operators monitor facility risk, triage alarms, and coordinate field teams using the following standard operating procedures (SOPs).

---

## 2. Alarm Severity & Response Directives

### A. CRITICAL (Risk Score 80.0 – 100.0)
- **Indicators**: Verified active flame, smoke plume combined with high temperature, or personnel in high-voltage / thermal hazard zone.
- **Protocol**:
  1. Automated sirens / audio cues triggered.
  2. Click alarm card in **Alerts Console** and press **Acknowledge**.
  3. Verify optical snapshot in **Live Intelligence** or **Video AI** tab.
  4. Dispatch Emergency Containment Team to indicated Sector.
  5. Once extinguished or cleared, enter operator resolution note and click **Resolve**.

### B. HIGH (Risk Score 60.0 – 79.9)
- **Indicators**: Rapid thermal rate-of-change (> 3.0°C/hr), single visual smoke detection, or worker approaching forklift boundary.
- **Protocol**:
  1. Inspect 3D Digital Twin or Spatial Map for affected camera FOV.
  2. Acknowledge alert and notify sector supervisor via radio.
  3. Verify ventilation / cooling status.

### C. MEDIUM (Risk Score 30.0 – 59.9)
- **Indicators**: Minor temperature elevation (> 2.0°C above baseline) or slight anomaly score.
- **Protocol**:
  1. Monitor Recharts trend line in **Analytics** tab.
  2. If trend stabilizes, no physical intervention required.

---

## 3. Subsystem Failure & Recovery SOPs

### 1. FortyGuard Environmental API Unreachable
- **Behavior**: Backend logs warning and switches to `NOT_CONFIGURED` without crashing. Internal on-site sensors continue operating.
- **Resolution**: Verify outbound internet connectivity and ensure `FORTYGUARD_API_KEY` is valid.

### 2. CCTV / RTSP Camera Stream Loss
- **Behavior**: `RTSPVideoSource` flags status as `DISCONNECTED` and initiates automatic 5-attempt exponential reconnect loop.
- **Resolution**: Check IP network switch and camera power over Ethernet (PoE).

### 3. Local Ollama AI Copilot Offline
- **Behavior**: Copilot automatically detects connection failure and delivers deterministic structured summaries directly from the SQL database.
- **Resolution**: Restart Ollama service (`ollama serve` or `docker restart ollama`).
