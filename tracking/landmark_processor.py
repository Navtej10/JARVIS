"""
tracking/landmark_processor.py

Smoothing, dead-zone, and screen-mapping logic that sits between raw
HandTracker output and the gesture/interaction layers.

Raw MediaPipe landmarks are jittery frame to frame -- this is what makes
the cursor feel "solid" instead of shaky. Do not skip this in V1; it is
one of the highest-leverage pieces of the whole pipeline.

TODO(V1): implement exponential moving average (or Kalman filter) smoothing.
TODO(V1): implement dead-zone (ignore movement below N pixels).
TODO(V1): implement acceleration curve (slow near target, fast for big moves).
TODO(V1): implement calibration mapping (hand-space corners -> screen pixels),
          using config/calibration.json's hand_space_corners.
"""
from __future__ import annotations
import math
import os
import json
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional

from tracking.hand_tracker import Landmark


@dataclass
class ScreenPoint:
    x: int
    y: int


class SpeedAdaptiveSmoother:
    """Speed-adaptive EMA smoother: smooth heavily when slow, track fast when moving."""

    def __init__(self, min_alpha: float = 0.05, max_alpha: float = 0.8, speed_factor: float = 10.0):
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.speed_factor = speed_factor
        self._value: tuple[float, float] | None = None

    def update(self, x: float, y: float) -> tuple[float, float]:
        if self._value is None:
            self._value = (x, y)
        else:
            prev_x, prev_y = self._value
            dist = math.hypot(x - prev_x, y - prev_y)
            # alpha scales with speed (distance between frames)
            alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * min(1.0, dist * self.speed_factor)
            self._value = (
                alpha * x + (1 - alpha) * prev_x,
                alpha * y + (1 - alpha) * prev_y,
            )
        return self._value


class LandmarkProcessor:
    """
    Converts a raw index-fingertip Landmark into a stable ScreenPoint,
    applying smoothing, dead-zone, acceleration, and the calibration mapping.
    """

    def __init__(self, calibration: dict, screen_width: int, screen_height: int):
        self.calibration = calibration
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.smoother = SpeedAdaptiveSmoother()
        self._last_emitted_norm: tuple[float, float] | None = None
        self._last_screen_point: ScreenPoint | None = None
        self._transform_matrix: np.ndarray | None = None
        self._init_transform_matrix()

    def _init_transform_matrix(self):
        corners = self.calibration.get("hand_space_corners", {})
        tl = corners.get("top_left", [0.0, 0.0])
        tr = corners.get("top_right", [0.0, 0.0])
        bl = corners.get("bottom_left", [0.0, 0.0])
        br = corners.get("bottom_right", [0.0, 0.0])
        
        # Uncalibrated if they are all 0
        if sum(tl + tr + bl + br) == 0.0:
            self._transform_matrix = None
            return
            
        src_points = np.array([tl, tr, bl, br], dtype=np.float32)
        dst_points = np.array([
            [0.0, 0.0], # top-left
            [1.0, 0.0], # top-right
            [0.0, 1.0], # bottom-left
            [1.0, 1.0]  # bottom-right
        ], dtype=np.float32)
        
        self._transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    def to_screen_point(self, landmark: Landmark) -> ScreenPoint:
        """
        Full pipeline: smooth -> map hand-space to screen-space via calibration
        corners -> apply dead-zone -> apply acceleration curve.
        """
        cursor_calib = self.calibration.get("cursor", {})
        dead_zone_px = cursor_calib.get("dead_zone_px", 2.0)
        accel_curve = cursor_calib.get("acceleration_curve", "quadratic")
        
        # 1. Smooth
        smooth_x, smooth_y = self.smoother.update(landmark.x, landmark.y)
        
        # 2. Transform using calibration matrix
        if self._transform_matrix is not None:
            pt = np.array([[[smooth_x, smooth_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(pt, self._transform_matrix)
            target_nx = float(transformed[0][0][0])
            target_ny = float(transformed[0][0][1])
        else:
            target_nx = smooth_x
            target_ny = smooth_y
            
        # Clamp mapped point immediately to prevent corner flicker
        target_nx = max(0.0, min(1.0, target_nx))
        target_ny = max(0.0, min(1.0, target_ny))
        
        # Base case
        if self._last_emitted_norm is None:
            self._last_emitted_norm = (target_nx, target_ny)
            sp = ScreenPoint(int(target_nx * self.screen_width), int(target_ny * self.screen_height))
            self._last_screen_point = sp
            return sp
            
        last_nx, last_ny = self._last_emitted_norm
        
        dx = target_nx - last_nx
        dy = target_ny - last_ny
        
        # 3. Check Dead-zone in pixel space
        px_dx = dx * self.screen_width
        px_dy = dy * self.screen_height
        dist_px = math.hypot(px_dx, px_dy)
        
        if dist_px < dead_zone_px:
            return self._last_screen_point
            
        # 4. Apply Acceleration
        if accel_curve == "quadratic":
            accel_factor = 1.0 + (dist_px / 150.0)
            dx *= accel_factor
            dy *= accel_factor
            
        new_nx = last_nx + dx
        new_ny = last_ny + dy
        
        # Clamp to [0, 1] normalized space
        new_nx = max(0.0, min(1.0, new_nx))
        new_ny = max(0.0, min(1.0, new_ny))
        self._last_emitted_norm = (new_nx, new_ny)
        
        # 5. Map to screen
        sp = ScreenPoint(int(new_nx * self.screen_width), int(new_ny * self.screen_height))
        self._last_screen_point = sp
        return sp

    def run_calibration_routine(self, hand_tracker) -> dict:
        """
        Interactive 4-corner calibration: prompt the user to point at each
        screen corner in turn, record the normalized hand position, and
        write the result to config/calibration.json.
        """
        window_name = "Calibration (Press 'q' to cancel)"
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # The 4 corners in screen pixel coordinates
        corners = [
            ("top_left", (0, 0)),
            ("top_right", (self.screen_width - 1, 0)),
            ("bottom_left", (0, self.screen_height - 1)),
            ("bottom_right", (self.screen_width - 1, self.screen_height - 1))
        ]
        
        history_len = 30
        variance_threshold = 0.0001
        
        recorded_corners = {}
        
        for corner_name, (cx, cy) in corners:
            history = []
            recorded = False
            
            for hand_frames in hand_tracker.stream():
                img = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
                
                # Offset circle slightly so it's fully visible at the absolute edges
                draw_x = max(30, min(self.screen_width - 30, cx))
                draw_y = max(30, min(self.screen_height - 30, cy))
                
                cv2.circle(img, (draw_x, draw_y), 30, (0, 0, 255), -1)
                
                text = f"Point steadily at the RED circle for {corner_name.replace('_', ' ').title()}"
                cv2.putText(img, text, (self.screen_width // 2 - 400, self.screen_height // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                            
                cv2.imshow(window_name, img)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    cv2.destroyWindow(window_name)
                    print("Calibration cancelled.")
                    return self.calibration
                
                if not hand_frames:
                    history.clear()
                    continue
                    
                hand = hand_frames[0]
                idx = hand.index_tip
                
                history.append((idx.x, idx.y))
                if len(history) > history_len:
                    history.pop(0)
                    
                    xs = [p[0] for p in history]
                    ys = [p[1] for p in history]
                    
                    if np.var(xs) < variance_threshold and np.var(ys) < variance_threshold:
                        avg_x = sum(xs) / len(xs)
                        avg_y = sum(ys) / len(ys)
                        recorded_corners[corner_name] = [avg_x, avg_y]
                        recorded = True
                        
                        # Flash green
                        cv2.circle(img, (draw_x, draw_y), 30, (0, 255, 0), -1)
                        cv2.imshow(window_name, img)
                        cv2.waitKey(500)
                        break
                        
            if not recorded:
                break
                
        cv2.destroyWindow(window_name)
        
        if len(recorded_corners) == 4:
            print("Calibration complete. Saving to config/calibration.json")
            
            # The config directory is one level up from tracking
            config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
            calib_file = os.path.join(config_dir, 'calibration.json')
            example_file = os.path.join(config_dir, 'calibration.example.json')
            
            if os.path.exists(calib_file):
                with open(calib_file, 'r') as f:
                    calib_data = json.load(f)
            else:
                with open(example_file, 'r') as f:
                    calib_data = json.load(f)
                    
            if 'hand_space_corners' not in calib_data:
                calib_data['hand_space_corners'] = {}
                
            calib_data['hand_space_corners'].update(recorded_corners)
            
            with open(calib_file, 'w') as f:
                json.dump(calib_data, f, indent=2)
                
            self.calibration = calib_data
            self._init_transform_matrix()
            
        return self.calibration
