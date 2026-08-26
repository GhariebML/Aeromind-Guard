# 48-Camera Capacity Analysis Report
**AeroMind ClimateGuard**

## 1. Baseline Measurements
During runtime validation on local hardware (`Windows 11 (AMD64)`, `Intel64 Family 6 Model 183`, `28 Cores`, `CPU Inference only`):
- **Video Source:** `demo_physical_hazards.mp4` (640x480 @ 24fps)
- **Model Pipeline:** `YOLOv8 + BoT-SORT`
- **Measured Inference Speed:** **~230 FPS** (Frames Per Second) purely on CPU.

## 2. 48-Camera Workload Estimation
Assuming a deployment of 48 RTSP/CCTV cameras processing real-time facility video:
- **Native FPS:** 30 FPS
- **AI Target FPS (Decimated):** 5 FPS (Sufficient for tracking and anomaly detection)
- **Required Total FPS:** 48 cameras * 5 FPS = **240 FPS** aggregate throughput.

## 3. Hardware Architecture Recommendation

### Option A: Centralized Edge Server (1 Node)
A single node equipped with **1x NVIDIA RTX 4090 (24GB VRAM)** or **1x NVIDIA L40S**:
- **Estimated GPU FPS:** 800 - 1,200 FPS (for YOLOv8m + Tracking)
- **Headroom:** ~75% idle capacity.
- **Verdict:** Highly viable. The current Python pipeline must use TensorRT batching to fully saturate the GPU, but even running sequentially, a single GPU can easily meet the 240 FPS requirement given the CPU already achieved 230 FPS.

### Option B: Distributed Edge Compute (3 Nodes)
Deploying **3x NVIDIA Jetson AGX Orin (64GB)** units, distributed across facility sectors:
- **Cameras per Node:** 16 cameras.
- **Required FPS per Node:** 80 FPS.
- **Estimated Orin FPS:** ~150 - 200 FPS per node with TensorRT INT8 optimization.
- **Verdict:** Recommended for industrial sites where pulling 48 high-bandwidth RTSP streams to a single server causes network congestion.

## 4. Conclusion
The measured baseline of **230 FPS on a CPU** confirms the architecture is extremely lightweight and efficient. Supporting 48 cameras is fundamentally achievable with either a single COTS GPU server or a small cluster of Jetson devices. No architectural rewrites are required for inference scaling, though an RTSP stream multiplexer (like NVIDIA DeepStream) may be needed to handle the video decoding bandwidth efficiently at 48 streams.
