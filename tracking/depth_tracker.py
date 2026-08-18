"""
tracking/depth_tracker.py

V6 module. Wraps a depth camera (Intel RealSense or similar) to add a Z axis
to hand tracking, enabling push/pull gestures and precision-mode switching
by distance from the screen.

Deliberately NOT implemented until V1-V5 are solid -- monocular depth
estimation from a single RGB webcam is not reliable enough for this, so
this module assumes real depth-camera hardware.

TODO(V6): initialize pyrealsense2 pipeline (or equivalent SDK).
TODO(V6): align depth frame to color frame so landmark (x,y) from
          hand_tracker.py can be looked up directly in the depth map.
TODO(V6): implement DepthZone classification with hysteresis so hovering
          near a zone boundary doesn't flicker between precision modes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DepthZone(Enum):
    NEAR = "near"    # precision mode
    MID = "mid"       # normal mode
    FAR = "far"        # coarse / window-level mode


@dataclass
class DepthReading:
    z_mm: float
    zone: DepthZone


class DepthTracker:
    """
    Adds Z-axis awareness on top of the 2D HandTracker output.

    Usage (V6+):
        depth_tracker = DepthTracker(calibration["depth"])
        reading = depth_tracker.get_depth(landmark_x_px, landmark_y_px)
    """

    def __init__(self, depth_config: dict):
        self.near_zone_mm = depth_config.get("near_zone_mm", 300)
        self.mid_zone_mm = depth_config.get("mid_zone_mm", 600)
        self.far_zone_mm = depth_config.get("far_zone_mm", 900)
        self.hysteresis_mm = depth_config.get("hysteresis_mm", 40)
        self._pipeline = None  # TODO(V6): pyrealsense2.pipeline()
        self._last_zone: DepthZone | None = None

    def start(self) -> None:
        raise NotImplementedError("TODO(V6): start RealSense pipeline, enable depth + color streams")

    def get_depth(self, pixel_x: int, pixel_y: int) -> DepthReading:
        """Look up depth (mm) at a given color-frame pixel and classify into a zone."""
        raise NotImplementedError("TODO(V6): query aligned depth frame, apply hysteresis, classify zone")

    def stop(self) -> None:
        raise NotImplementedError("TODO(V6): stop pipeline")
