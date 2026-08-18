"""
gestures/fist.py

Detects a closed fist. Used for the global kill-switch.
"""
from __future__ import annotations

import math

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame


class FistGesture(GestureStateMachine):
    name = "fist"

    def __init__(self, distance_threshold: float = 0.8, **kwargs):
        super().__init__(**kwargs)
        self.distance_threshold = distance_threshold

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        wrist = hand_frame.wrist
        middle_knuckle = hand_frame.landmarks[9]
        
        # Calculate reference distance (wrist to middle knuckle)
        ref_dist = math.dist((wrist.x, wrist.y, wrist.z), (middle_knuckle.x, middle_knuckle.y, middle_knuckle.z))
        if ref_dist == 0:
            return False
            
        # Get fingertips
        index_tip = hand_frame.index_tip
        middle_tip = hand_frame.landmarks[12]
        ring_tip = hand_frame.landmarks[16]
        pinky_tip = hand_frame.landmarks[20]
        
        # Calculate distances from wrist to fingertips
        d1 = math.dist((wrist.x, wrist.y, wrist.z), (index_tip.x, index_tip.y, index_tip.z))
        d2 = math.dist((wrist.x, wrist.y, wrist.z), (middle_tip.x, middle_tip.y, middle_tip.z))
        d3 = math.dist((wrist.x, wrist.y, wrist.z), (ring_tip.x, ring_tip.y, ring_tip.z))
        d4 = math.dist((wrist.x, wrist.y, wrist.z), (pinky_tip.x, pinky_tip.y, pinky_tip.z))
        
        avg_dist = (d1 + d2 + d3 + d4) / 4.0
        normalized_avg = avg_dist / ref_dist
        
        # An open hand typically has normalized_avg > 2.0
        # A closed fist usually has normalized_avg < 1.2
        return normalized_avg < self.distance_threshold
