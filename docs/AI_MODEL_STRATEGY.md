# AeroMind ClimateGuard — Industrial Safety AI Model Strategy & Capabilities Matrix

## 1. Executive Strategy
The AeroMind ClimateGuard platform employs a modular perception pipeline. Generic pretrained models (e.g. YOLOv8 COCO) provide baseline object classes (people, vehicles), while domain-specific safety hazards require fine-tuned custom vision models or heuristic computer vision algorithms.

We explicitly differentiate between **out-of-the-box supported classes**, **algorithmic heuristic detections**, and **custom industrial model weights**.

---

## 2. Industrial Safety AI Capabilities Matrix

| Safety Category | Target Class / Behavior | Primary Detection Mechanism | Capability Status | Dataset / Fine-Tuning Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Fire & Combustion** | Flame / Fire | YOLO + HSV Color Space Heuristics | **SUPPORTED** | Pre-trained flame detector with contour & color-space fallback. |
| **Fire & Combustion** | Smoke Plume | YOLO + Spatial Motion Dynamics | **SUPPORTED** | Optical density and upward diffusion tracking. |
| **Personnel Safety** | Person Tracking | YOLOv8 + BoT-SORT Tracker | **SUPPORTED** | Pretrained COCO person class with velocity and trajectory estimation. |
| **Personnel Safety** | Hardhat / Helmet | Custom YOLOv8-PPE Weights | **REQUIRES_CUSTOM_MODEL** | Fine-tuned on Roboflow PPE / SHWD Hardhat Dataset (15k annotated images). |
| **Personnel Safety** | High-Visibility Vest | Custom YOLOv8-PPE Weights | **REQUIRES_CUSTOM_MODEL** | Fine-tuned on Roboflow Worker Safety Vest dataset. |
| **Personnel Safety** | Safety Gloves / Shoes | Custom Micro-Vision Model | **REQUIRES_CUSTOM_MODEL** | High-resolution crop inference (<10m camera distance required). |
| **Heavy Machinery** | Forklift Detection | YOLOv8 Vehicle Weights | **PARTIALLY_SUPPORTED** | Maps to generic `truck`/`car` class or dedicated industrial vehicle weights. |
| **Heavy Machinery** | Forklift-Person Proximity | Spatial Distance Tracker | **SUPPORTED** | Calculated in real-time via Euclidean centroid tracking in `BoTSORTTracker`. |
| **Spatial Containment** | Restricted Zone Intrusion | Point-in-Polygon Engine | **SUPPORTED** | Real-time raycasting against user-defined polygon perimeters. |
| **Spatial Containment** | Danger Zone Dwell Time | Temporal Dwell Counter | **SUPPORTED** | Tracks entry timestamp, active dwell seconds, and exit transitions. |
| **Tank Farm Hazards** | Liquid Spill / Leakage | Texture / Specular Anomaly | **REQUIRES_CUSTOM_MODEL** | Supervised semantic segmentation on industrial chemical pools. |
| **Tank Farm Hazards** | Tank Level Overflow | Thermal Hotspot / Anomaly | **SUPPORTED (THERMAL)** | Correlated with thermal rate-of-change and FortyGuard surface temperature. |
| **Human Behavior** | Cellphone Usage | Keypoint Pose / Micro-YOLO | **REQUIRES_CUSTOM_MODEL** | Pose estimation tracking hand-to-ear / hand-to-chest orientation. |
| **Human Behavior** | Smoking in Zone | Flame Detection + Pose | **PARTIALLY_SUPPORTED** | Micro-flame point detection correlated with person face keypoints. |
| **Human Behavior** | Worker Inactivity / Sleeping | Dwell Time + Pose Geometry | **SUPPORTED** | Static bounding box velocity (< 2 px/s for > 10 minutes) in active shift. |

---

## 3. Custom Model Pluggability Architecture

The `BaseDetector` interface allows dropping in custom `.pt` or TensorRT `.engine` models without modifying the backend or pipeline logic:

```python
class BaseDetector(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray, conf_threshold: float, iou_threshold: float) -> List[DetectionResult]:
        pass
```

### Loading Custom Trained Weights
To activate a custom model for PPE or Forklifts:
```bash
# Set model path in environment
export YOLO_MODEL_PATH="/opt/models/aeromind_ppe_forklift_v2.pt"
```
The detector automatically loads the specified weights and applies appropriate class mappings.
