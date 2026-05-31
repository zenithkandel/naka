"""
BorderVision — Camera Calibration Module

Handles camera intrinsic/extrinsic parameters and ground-plane
homography for height estimation and coordinate mapping.
"""

import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class CameraCalibration:
    """
    Manages camera calibration for pixel-to-world coordinate mapping.

    Uses camera intrinsics (focal length, principal point), extrinsics
    (camera height, tilt angle), and ground-plane homography to project
    pixel measurements into real-world values.
    """

    def __init__(
        self,
        intrinsic_matrix: Optional[np.ndarray] = None,
        camera_height_m: float = 4.0,
        tilt_deg: float = 25.0,
        focal_length_px: Optional[float] = None,
        principal_point: Optional[Tuple[float, float]] = None,
        homography_matrix: Optional[np.ndarray] = None,
    ):
        self.camera_height_m = camera_height_m
        self.tilt_deg = tilt_deg
        self.tilt_rad = np.radians(tilt_deg)

        if intrinsic_matrix is not None:
            self.intrinsic = np.array(intrinsic_matrix, dtype=np.float64)
            self.focal_length = self.intrinsic[0, 0]
            self.principal_point = (self.intrinsic[0, 2], self.intrinsic[1, 2])
        else:
            self.focal_length = focal_length_px or 1000.0
            self.principal_point = principal_point or (960.0, 540.0)
            self.intrinsic = np.array([
                [self.focal_length, 0, self.principal_point[0]],
                [0, self.focal_length, self.principal_point[1]],
                [0, 0, 1],
            ], dtype=np.float64)

        self.homography = (
            np.array(homography_matrix, dtype=np.float64)
            if homography_matrix is not None
            else None
        )

    def estimate_height_cm(
        self,
        bbox_top_y: int,
        bbox_bottom_y: int,
        frame_height: int,
    ) -> Tuple[float, float]:
        """
        Estimate a person's real-world height from their bounding box.

        Uses the pinhole camera model with known camera height and tilt.

        Args:
            bbox_top_y: Y-coordinate of the top of the person bbox.
            bbox_bottom_y: Y-coordinate of the bottom of the person bbox.
            frame_height: Total frame height in pixels.

        Returns:
            (estimated_height_cm, confidence)
        """
        # Pixel height of person
        pixel_height = bbox_bottom_y - bbox_top_y
        if pixel_height <= 0:
            return 0.0, 0.0

        # Distance estimation via ground-plane geometry
        cy = self.principal_point[1]
        foot_offset = bbox_bottom_y - cy

        # Angular offset from principal axis to foot position
        foot_angle = np.arctan2(foot_offset, self.focal_length)

        # Distance from camera to person's feet on ground plane
        ground_angle = self.tilt_rad + foot_angle
        if ground_angle <= 0 or ground_angle >= np.pi / 2:
            return 0.0, 0.0

        distance_to_feet = self.camera_height_m / np.tan(ground_angle)

        # Real-world height from pixel height
        height_m = (pixel_height * distance_to_feet) / self.focal_length
        height_cm = height_m * 100.0

        # Clamp to reasonable range
        height_cm = max(50.0, min(250.0, height_cm))

        # Confidence based on bbox size relative to frame
        size_ratio = pixel_height / frame_height
        confidence = min(1.0, size_ratio * 3.0)  # Full confidence at ~33% of frame

        return round(height_cm, 1), round(confidence, 3)

    def pixel_to_ground(self, point: Tuple[int, int]) -> Optional[Tuple[float, float]]:
        """
        Project a pixel coordinate to ground-plane world coordinates.

        Requires a calibrated homography matrix.
        """
        if self.homography is None:
            return None

        p = np.array([point[0], point[1], 1.0])
        world = self.homography @ p
        if abs(world[2]) < 1e-8:
            return None
        return (world[0] / world[2], world[1] / world[2])

    def to_dict(self) -> dict:
        return {
            "intrinsic_matrix": self.intrinsic.tolist(),
            "camera_height_m": self.camera_height_m,
            "tilt_deg": self.tilt_deg,
            "focal_length_px": self.focal_length,
            "principal_point": list(self.principal_point),
            "homography_matrix": self.homography.tolist() if self.homography is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CameraCalibration":
        return cls(
            intrinsic_matrix=data.get("intrinsic_matrix"),
            camera_height_m=data.get("camera_height_m", 4.0),
            tilt_deg=data.get("tilt_deg", 25.0),
            focal_length_px=data.get("focal_length_px"),
            principal_point=tuple(data["principal_point"]) if data.get("principal_point") else None,
            homography_matrix=data.get("homography_matrix"),
        )
