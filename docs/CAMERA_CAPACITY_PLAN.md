# AeroMind ClimateGuard — 48-Camera Industrial Scalability & Capacity Plan

## 1. Executive Summary & Deployment Baseline
This capacity plan outlines the architecture, compute, VRAM, storage, and network topology required to run AeroMind ClimateGuard across a full industrial facility featuring **48 Hikvision IP CCTV cameras** streaming 1080p video @ 25 FPS.

---

## 2. Ingestion & Inference Workload Modeling

### A. Raw Video Streams vs Decimated Inference
- **Total Cameras**: 48 physical RTSP cameras
- **Native Resolution**: 1920 x 1080 px (1080p)
- **Native Frame Rate**: 25 FPS per camera (1,200 raw FPS total)
- **Decimation Strategy**:
  - Decode frame rate: 25 FPS (for smooth video stream and tracking update)
  - AI Deep Learning Inference rate: **5 FPS per camera** (sufficient for industrial hazard detection)
  - **Total Aggregate AI Inference Workload**: $48 \times 5 = \mathbf{240\text{ FPS}}$

---

## 3. Hardware Compute & Resource Sizing

### A. Network Bandwidth Requirements
- **Bitrate per Stream (H.265 @ 1080p)**: 3.5 to 4.5 Mbps
- **Total Incoming Network Ingestion**: $48 \times 4.0\text{ Mbps} = \mathbf{192\text{ Mbps}}$ (~24 MB/sec)
- **Recommended Interface**: Dual 10 GbE / 1 GbE dedicated industrial VLAN.

### B. GPU Compute & VRAM Modeling
- **Model**: YOLOv8n / YOLOv8s TensorRT INT8 / FP16 (`~6 MB` footprint)
- **Batch Size**: Dynamic batch size of 8 or 16
- **VRAM Utilization**:
  - Model weights + CUDA context: ~1.2 GB
  - Frame buffers (48 active decoded frame rings): ~3.5 GB
  - PyTorch / TensorRT inference workspace: ~2.5 GB
  - **Total Required GPU VRAM**: **~8.0 GB to 12.0 GB minimum**

### C. Host CPU & Memory Sizing
- **CPU**: 16-Core / 32-Thread Intel Xeon / AMD EPYC or Core i9 (for hardware H.264/H.265 FFmpeg stream decoding)
- **System Memory (RAM)**: **32 GB DDR5** ECC RAM

---

## 4. Architectural Topology Options

### Option A: Central GPU Server (Recommended for On-Premises Control Rooms)
- **Hardware**: 1x Server with **NVIDIA RTX 4090 (24GB)** or **NVIDIA RTX A5000 (24GB)**
- **Advantages**: Single node to maintain, unified database and event hub, zero network hops for AI inference.
- **Inference Capacity**: ~320 FPS TensorRT FP16 $\rightarrow$ Headroom: **+33%**.

### Option B: Distributed Edge Nodes (Recommended for Multi-Building Campuses)
- **Hardware**: 4x **NVIDIA Jetson AGX Orin (32GB / 64GB)** nodes
- **Allocation**: 12 cameras per Jetson unit (60 AI FPS per edge unit)
- **Advantages**: Localized failure containment; if one edge node fails, only 12 cameras are affected.

### Option C: Hybrid Edge-Cloud
- **Edge**: Jetson devices run video decoding, BoT-SORT tracking, and danger zone events.
- **Cloud/Control Room**: Central server receives lightweight typed JSON events (`PhysicalAIEvent`) for correlation and risk engine calculation.

---

## 5. Storage Retention Strategy

- **Continuous 24/7 Raw Video**: 48 cameras $\times$ 4.0 Mbps = ~2.0 TB per day. Recommended 14-day rolling NAS storage: **~30 TB RAID 6**.
- **Incident Snapshots & Video Events**: Extracted JPEG frames only on hazard triggers (~200 KB per event) $\rightarrow$ **< 5 GB / month**.
- **Database Telemetry & Risk History**: PostgreSQL partition pruning with 90-day retention $\rightarrow$ **~15 GB**.
