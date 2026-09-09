"""
gestures/grab.py

Closed fist -> grab a window.
Fist + move -> move the grabbed target; release fist -> drop it.
"""
from __future__ import annotations

import math

from gestures.gesture_state_machine import GestureStateMachine, GestureState
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended


class GrabGesture(GestureStateMachine):
    name = "grab"

    def __init__(self, engage_threshold: float = 0.8, release_threshold: float = 1.0, distance_threshold: float = None, **kwargs):
        super().__init__(**kwargs)
        self.engage_threshold = distance_threshold if distance_threshold is not None else engage_threshold
        self.release_threshold = release_threshold

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
        
        threshold = self.release_threshold if self._state in (GestureState.HOLD, GestureState.START) else self.engage_threshold
        
        # An open hand typically has normalized_avg > 2.0
        # A closed fist usually has normalized_avg < 1.2
        if normalized_avg >= threshold:
            return False
            
        # To distinguish from a POINT gesture or PINCH, ensure index finger is not explicitly extended
        if is_finger_extended(hand_frame, 5, 8, threshold=1.2):
            return False
            
        return True
