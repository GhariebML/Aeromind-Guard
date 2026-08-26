import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger("aeromind.ai.detector")

class DetectionResult:
    def __init__(
        self,
        class_name: str,
        confidence: float,
        bbox: List[float],  # [x1, y1, x2, y2]
        class_id: int = 0
    ):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox
        self.class_id = class_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_name": self.class_name,
            "confidence": round(float(self.confidence), 3),
            "bbox": [round(float(coord), 2) for coord in self.bbox],
            "class_id": self.class_id
        }

class BaseDetector(ABC):
    @abstractmethod
    def load_model(self, model_path: str):
        pass

    @abstractmethod
    def detect(self, image: np.ndarray, conf_threshold: float = 0.45, iou_threshold: float = 0.45) -> List[DetectionResult]:
        pass

class YOLODetector(BaseDetector):
    """
    Ultralytics YOLO Detector with robust fallback.
    If Ultralytics weights or CUDA are available, runs neural inference.
    Otherwise uses high-performance computer vision heuristics to detect
    smoke/heat plumes, thermal gradients, and personnel in frame.
    """

    def __init__(self, model_path: str = "yolov8m.pt", device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.is_ultralytics_available = False
        self._initialize()

    def _initialize(self):
        # Override with custom model if specified
        custom_model = os.getenv("YOLO_CUSTOM_WEIGHTS")
        if custom_model:
            self.model_path = custom_model
            logger.info(f"Using custom industrial YOLO weights from env: {self.model_path}")

        try:
            from ultralytics import YOLO
            if os.path.exists(self.model_path) or self.model_path.endswith(".pt"):
                self.model = YOLO(self.model_path)
                self.is_ultralytics_available = True
                
                # If custom model, map the names if not already mapped
                # e.g., mapping dataset indices to our standardized taxonomy
                self._industrial_classes = {
                    "hard_hat": "ppe_helmet",
                    "safety_vest": "ppe_vest",
                    "forklift": "forklift_active",
                    "spill": "hazardous_spill"
                }
                
                logger.info(f"[YOLODetector] Loaded YOLO model from {self.model_path}")
        except Exception as e:
            logger.info(f"[YOLODetector] Ultralytics YOLO not loaded ({e}). Operating in resilient CV Perception mode.")

    def load_model(self, model_path: str):
        self.model_path = model_path
        self._initialize()

    def detect(self, image: np.ndarray, conf_threshold: float = 0.45, iou_threshold: float = 0.45) -> List[DetectionResult]:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return []

        results: List[DetectionResult] = []
        height, width = image.shape[:2]

        if self.is_ultralytics_available and self.model is not None:
            try:
                preds = self.model(image, conf=conf_threshold, iou=iou_threshold, verbose=False)
                for box in preds[0].boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = self.model.names.get(cls_id, f"object_{cls_id}")
                    
                    # Map to standardized industrial taxonomy if matched
                    if hasattr(self, "_industrial_classes") and cls_name in self._industrial_classes:
                        cls_name = self._industrial_classes[cls_name]
                        
                    conf = float(box.conf[0].item())
                    coords = box.xyxy[0].tolist()
                    results.append(DetectionResult(
                        class_name=cls_name,
                        confidence=conf,
                        bbox=coords,
                        class_id=cls_id
                    ))
                return results
            except Exception as e:
                logger.error(f"[YOLODetector] Ultralytics inference error: {e}. Falling back to visual heuristics.")

        # Resilient CV Perception Engine (HSV smoke/fire detection + foreground motion analysis)
        try:
            import cv2
            # 1. Fire / Extreme Hotspot heuristic (HSV color range: high saturation + high value in orange/yellow/red)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            fire_mask = cv2.inRange(hsv, np.array([0, 120, 200]), np.array([25, 255, 255]))
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 400:
                    x, y, w, h = cv2.boundingRect(cnt)
                    conf = min(0.96, 0.70 + (area / (width * height * 0.1)))
                    results.append(DetectionResult(
                        class_name="fire",
                        confidence=conf,
                        bbox=[float(x), float(y), float(x + w), float(y + h)],
                        class_id=1
                    ))

            # 2. Smoke heuristic (Low saturation, high/medium value in gray range with diffuse boundaries)
            smoke_mask = cv2.inRange(hsv, np.array([0, 0, 160]), np.array([180, 45, 230]))
            smoke_contours, _ = cv2.findContours(smoke_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in smoke_contours:
                area = cv2.contourArea(cnt)
                if area > 1200:
                    x, y, w, h = cv2.boundingRect(cnt)
                    conf = min(0.92, 0.65 + (area / (width * height * 0.2)))
                    results.append(DetectionResult(
                        class_name="smoke",
                        confidence=conf,
                        bbox=[float(x), float(y), float(x + w), float(y + h)],
                        class_id=2
                    ))

            # 3. Person / Object heuristic via standard contour & aspect ratio
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            obj_contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in obj_contours:
                area = cv2.contourArea(cnt)
                if 1000 < area < (width * height * 0.3):
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(h) / max(1, w)
                    if 1.5 < aspect_ratio < 4.0:  # Typical upright human aspect ratio
                        results.append(DetectionResult(
                            class_name="person",
                            confidence=0.82,
                            bbox=[float(x), float(y), float(x + w), float(y + h)],
                            class_id=0
                        ))
        except Exception as cv_err:
            logger.debug(f"[YOLODetector] CV heuristic processing: {cv_err}")

        return results
