"""
BorderVision — YOLOv8 Detection Wrapper

Wraps Ultralytics YOLO models for person and bag detection.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """A single detection result."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_id: int
    class_name: str
    confidence: float
    track_id: Optional[int] = None
    mask: Optional[np.ndarray] = None
    keypoints: Optional[np.ndarray] = None

    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def foot_position(self) -> Tuple[int, int]:
        """Bottom-center of bbox — used for crossing detection."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, y2)

    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)

    def crop(self, frame: np.ndarray) -> np.ndarray:
        """Extract the bounding box region from a frame."""
        x1, y1, x2, y2 = self.bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return frame[y1:y2, x1:x2]


class Detector:
    """YOLOv8 detection wrapper for persons and bags."""

    def __init__(
        self,
        model_path: str = "yolov8x.pt",
        confidence: float = 0.5,
        iou: float = 0.5,
        person_class_id: int = 0,
        bag_class_ids: Tuple[int, ...] = (24, 26, 28),
        bag_class_names: Optional[dict] = None,
    ):
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            logger.info(f"Loaded detection model: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            self.model = None

        self.confidence = confidence
        self.iou = iou
        self.person_class_id = person_class_id
        self.bag_class_ids = bag_class_ids
        self.bag_class_names = bag_class_names or {
            24: "backpack", 26: "handbag", 28: "suitcase"
        }
        self._target_classes = [person_class_id] + list(bag_class_ids)

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run detection on a frame.

        Returns:
            List of Detection objects for persons and bags.
        """
        if self.model is None:
            return []

        results = self.model(
            frame,
            conf=self.confidence,
            iou=self.iou,
            classes=self._target_classes,
            verbose=False,
        )

        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id == self.person_class_id:
                    class_name = "person"
                elif class_id in self.bag_class_ids:
                    class_name = self.bag_class_names.get(class_id, "bag")
                else:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    class_name=class_name,
                    confidence=float(box.conf[0]),
                ))

        return detections

    def track(
        self, frame: np.ndarray, persist: bool = True, tracker: str = "botsort.yaml"
    ) -> List[Detection]:
        """
        Run detection + BoT-SORT tracking on a frame.

        Args:
            frame: Input video frame.
            persist: Maintain track IDs across frames.
            tracker: Tracker configuration file.

        Returns:
            List of Detection objects with track_id populated.
        """
        if self.model is None:
            return []

        results = self.model.track(
            frame,
            conf=self.confidence,
            iou=self.iou,
            classes=self._target_classes,
            tracker=tracker,
            persist=persist,
            verbose=False,
        )

        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id == self.person_class_id:
                    class_name = "person"
                elif class_id in self.bag_class_ids:
                    class_name = self.bag_class_names.get(class_id, "bag")
                else:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                track_id = int(box.id[0]) if box.id is not None else None

                detections.append(Detection(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    class_name=class_name,
                    confidence=float(box.conf[0]),
                    track_id=track_id,
                ))

        return detections
