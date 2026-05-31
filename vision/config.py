"""
BorderVision — Vision Pipeline Configuration

Centralized settings for the computer vision pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class VisionConfig:
    """Configuration for the vision processing pipeline."""

    # ─── Camera Source ─────────────────────────────────────────
    source: str = "0"  # USB camera index or RTSP URL

    # ─── Detection ─────────────────────────────────────────────
    detection_model: str = "yolov8x.pt"
    segmentation_model: str = "yolov8x-seg.pt"
    pose_model: str = "yolov8x-pose.pt"
    detection_confidence: float = 0.5
    detection_iou: float = 0.5

    # Person COCO class ID
    person_class_id: int = 0

    # Bag COCO class IDs: backpack=24, handbag=26, suitcase=28
    bag_class_ids: Tuple[int, ...] = (24, 26, 28)
    bag_class_names: dict = field(default_factory=lambda: {
        24: "backpack",
        26: "handbag",
        28: "suitcase",
    })

    # ─── Tracking ──────────────────────────────────────────────
    tracker_config: str = "botsort.yaml"

    # ─── Crossing Detection ────────────────────────────────────
    hysteresis_frames: int = 5  # Consecutive frames on new side required

    # ─── Staggered Inference ───────────────────────────────────
    pose_frame_interval: int = 3       # Pose runs every Nth frame
    appearance_interval_sec: float = 1.0  # FastReID extraction rate
    gait_sequence_length: int = 25     # Frames needed for gait embedding

    # ─── Frame Processing ──────────────────────────────────────
    target_fps: int = 30
    frame_width: int = 1920
    frame_height: int = 1080
    jpeg_quality: int = 80

    # ─── Display ───────────────────────────────────────────────
    show_bboxes: bool = True
    show_track_ids: bool = True
    show_boundary: bool = True
    bbox_thickness: int = 2
    text_scale: float = 0.6
    boundary_color: Tuple[int, int, int] = (0, 255, 255)  # Cyan
    person_color: Tuple[int, int, int] = (0, 255, 0)      # Green
    bag_color: Tuple[int, int, int] = (255, 165, 0)        # Orange
