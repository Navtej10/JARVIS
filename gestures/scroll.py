"""
gestures/scroll.py

Two-finger scroll. Used for vertical scrolling.

Detection:
1. Index and Middle fingertips are close together.
2. The gesture state machine handles the duration/debounce.
The delta scrolling amount is handled externally when the HOLD event is emitted.
"""
from __future__ import annotations

import math

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame


class ScrollGesture(GestureStateMachine):
    name = "scroll"

    def __init__(self, distance_threshold: float = 0.25, **kwargs):
        super().__init__(**kwargs)
        self.distance_threshold = distance_threshold

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        index = hand_frame.index_tip
        middle = hand_frame.landmarks[12]
        wrist = hand_frame.wrist
        middle_knuckle = hand_frame.landmarks[9]
        
        # Calculate 3D distances
        fingers_dist = math.dist((index.x, index.y, index.z), (middle.x, middle.y, middle.z))
        ref_dist = math.dist((wrist.x, wrist.y, wrist.z), (middle_knuckle.x, middle_knuckle.y, middle_knuckle.z))
        
        if ref_dist == 0:
            return False
            
        normalized_dist = fingers_dist / ref_dist
        
        # We also want to ensure fingers are extended, not curled.
        # Simple check: index tip y should be above (numerically less than) the PIP joints (landmarks 6 and 10)
        # assuming hand is mostly upright. 
        # A more robust check might compare distance from wrist to tip vs wrist to knuckle.
        dist_wrist_index = math.dist((wrist.x, wrist.y, wrist.z), (index.x, index.y, index.z))
        dist_wrist_middle = math.dist((wrist.x, wrist.y, wrist.z), (middle.x, middle.y, middle.z))
        
        # If the distance from wrist to fingertip is smaller than wrist to knuckle, they are curled.
        # But wrist to knuckle is ref_dist. 
        if dist_wrist_index < ref_dist * 1.2 or dist_wrist_middle < ref_dist * 1.2:
            return False

        return normalized_dist < self.distance_threshold
