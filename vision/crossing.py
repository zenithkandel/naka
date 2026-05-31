"""
BorderVision — Boundary Line Crossing Detection

Determines when a tracked person crosses the virtual boundary line,
with temporal hysteresis to prevent flickering.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class Side(str, Enum):
    """Which side of the boundary line a person is on."""
    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    ON_LINE = "ON_LINE"


@dataclass
class CrossingEvent:
    """A detected boundary crossing event."""
    track_id: int
    direction: str  # "IN" or "OUT"
    timestamp: float
    foot_position: Tuple[int, int]
    frame_number: int


class BoundaryLine:
    """
    Defines a virtual boundary line between two points.
    Uses the cross-product method to determine which side of the line a point is on.
    """

    def __init__(self, start: Tuple[float, float], end: Tuple[float, float]):
        """
        Args:
            start: (x, y) of line start point.
            end: (x, y) of line end point.
        """
        self.start = np.array(start, dtype=np.float64)
        self.end = np.array(end, dtype=np.float64)
        self._direction = self.end - self.start
        self._length = np.linalg.norm(self._direction)

    def get_side(self, point: Tuple[int, int]) -> Side:
        """
        Determine which side of the line a point is on.

        Uses the cross product of the line direction vector and the vector
        from line start to the point. Positive = INSIDE, Negative = OUTSIDE.
        """
        p = np.array(point, dtype=np.float64)
        cross = np.cross(self._direction, p - self.start)

        if abs(cross) < self._length * 2:  # Close to the line
            return Side.ON_LINE
        return Side.INSIDE if cross > 0 else Side.OUTSIDE

    def distance_to_point(self, point: Tuple[int, int]) -> float:
        """Calculate perpendicular distance from a point to the line."""
        p = np.array(point, dtype=np.float64)
        return abs(np.cross(self._direction, p - self.start)) / self._length

    def to_dict(self) -> dict:
        return {
            "start": self.start.tolist(),
            "end": self.end.tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoundaryLine":
        return cls(start=tuple(data["start"]), end=tuple(data["end"]))


class CrossingDetector:
    """
    Monitors tracked persons' foot positions relative to the boundary line.
    Applies temporal hysteresis to prevent false triggers.
    """

    def __init__(self, boundary: BoundaryLine, hysteresis_frames: int = 5):
        """
        Args:
            boundary: The virtual boundary line.
            hysteresis_frames: Number of consecutive frames a person must be
                               on the new side before a crossing is confirmed.
        """
        self.boundary = boundary
        self.hysteresis_frames = hysteresis_frames

        # Per-track state: {track_id: {"established_side": Side, "pending_side": Side, "count": int}}
        self._track_state: Dict[int, dict] = {}

    def update(
        self,
        track_id: int,
        foot_position: Tuple[int, int],
        timestamp: float,
        frame_number: int,
    ) -> Optional[CrossingEvent]:
        """
        Update a track's position and check for crossing events.

        Args:
            track_id: BoT-SORT track ID.
            foot_position: Bottom-center of person bounding box.
            timestamp: Current frame timestamp.
            frame_number: Current frame number.

        Returns:
            CrossingEvent if a crossing is confirmed, None otherwise.
        """
        current_side = self.boundary.get_side(foot_position)

        if current_side == Side.ON_LINE:
            return None  # Ignore points right on the line

        if track_id not in self._track_state:
            # First observation — establish initial side
            self._track_state[track_id] = {
                "established_side": current_side,
                "pending_side": None,
                "count": 0,
            }
            return None

        state = self._track_state[track_id]

        if current_side == state["established_side"]:
            # Still on the same side — reset any pending crossing
            state["pending_side"] = None
            state["count"] = 0
            return None

        # On a different side — accumulate hysteresis
        if state["pending_side"] == current_side:
            state["count"] += 1
        else:
            state["pending_side"] = current_side
            state["count"] = 1

        if state["count"] >= self.hysteresis_frames:
            # Crossing confirmed!
            old_side = state["established_side"]
            new_side = current_side

            # Determine direction
            direction = "IN" if new_side == Side.INSIDE else "OUT"

            # Update state
            state["established_side"] = new_side
            state["pending_side"] = None
            state["count"] = 0

            event = CrossingEvent(
                track_id=track_id,
                direction=direction,
                timestamp=timestamp,
                foot_position=foot_position,
                frame_number=frame_number,
            )
            logger.info(
                f"Crossing detected: Track {track_id} → {direction} "
                f"at frame {frame_number}"
            )
            return event

        return None

    def remove_track(self, track_id: int):
        """Clean up state for a lost track."""
        self._track_state.pop(track_id, None)

    def reset(self):
        """Clear all tracking state."""
        self._track_state.clear()

    @property
    def active_tracks(self) -> int:
        return len(self._track_state)
