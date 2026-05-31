"""
BorderVision — Frame Capture Module

Handles video acquisition from USB cameras and RTSP streams
in a dedicated thread to prevent frame dropping.
"""

import threading
import time
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FrameCapture:
    """
    Threaded video capture that continuously reads frames
    from a USB camera or RTSP stream.
    """

    def __init__(self, source: str, target_fps: int = 30):
        """
        Args:
            source: USB camera index (e.g., "0") or RTSP URL.
            target_fps: Target frames per second.
        """
        self.source = int(source) if source.isdigit() else source
        self.target_fps = target_fps
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count = 0
        self._reconnect_delay = 5  # seconds

    @property
    def frame(self) -> Optional[np.ndarray]:
        """Get the latest frame (thread-safe)."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Start the capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Frame capture started: source={self.source}")

    def stop(self):
        """Stop the capture thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._cap:
            self._cap.release()
        logger.info("Frame capture stopped")

    def _connect(self) -> bool:
        """Establish connection to the video source."""
        try:
            self._cap = cv2.VideoCapture(self.source)
            if isinstance(self.source, int):
                # USB camera optimizations
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            else:
                # RTSP stream: reduce buffer to minimize latency
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if self._cap.isOpened():
                logger.info(f"Connected to video source: {self.source}")
                return True
            else:
                logger.error(f"Failed to open video source: {self.source}")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def _capture_loop(self):
        """Main capture loop running in a separate thread."""
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                if not self._connect():
                    logger.warning(
                        f"Reconnecting in {self._reconnect_delay}s..."
                    )
                    time.sleep(self._reconnect_delay)
                    continue

            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Frame read failed, reconnecting...")
                self._cap.release()
                self._cap = None
                time.sleep(1)
                continue

            with self._lock:
                self._frame = frame
                self._frame_count += 1

    def get_properties(self) -> dict:
        """Get current capture properties."""
        if self._cap and self._cap.isOpened():
            return {
                "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self._cap.get(cv2.CAP_PROP_FPS),
                "frame_count": self._frame_count,
            }
        return {}
