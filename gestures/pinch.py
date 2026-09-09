"""
gestures/pinch.py  (V1)

Thumb + index pinch. Used for: left click (tap), drag (pinch + move).

Detection: euclidean distance between thumb_tip and index_tip landmarks,
normalized to hand size (so it works at any distance from camera), compared
against calibration.gesture_thresholds.pinch_distance_threshold.
"""
from __future__ import annotations

import math

from gestures.gesture_state_machine import GestureStateMachine, GestureState
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended_by_curl


class PinchGesture(GestureStateMachine):
    name = "pinch"

    def __init__(self, engage_threshold: float = 0.045, release_threshold: float = 0.065, distance_threshold: float = None, **kwargs):
        super().__init__(**kwargs)
        self.engage_threshold = distance_threshold if distance_threshold is not None else engage_threshold
        self.release_threshold = release_threshold

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        thumb = hand_frame.thumb_tip
        index = hand_frame.index_tip
        wrist = hand_frame.wrist
        middle_knuckle = hand_frame.landmarks[9]
        
        # Calculate 3D distances
        pinch_dist = math.dist((thumb.x, thumb.y, thumb.z), (index.x, index.y, index.z))
        ref_dist = math.dist((wrist.x, wrist.y, wrist.z), (middle_knuckle.x, middle_knuckle.y, middle_knuckle.z))
        
        if ref_dist == 0:
            return False
            
        threshold = self.release_threshold if self._state in (GestureState.HOLD, GestureState.START) else self.engage_threshold
        
        normalized_dist = pinch_dist / ref_dist
        if normalized_dist >= threshold:
            return False
            
        # To avoid confusion with a Fist, at least one other finger (middle, ring, pinky) 
        # or the index finger itself must be somewhat extended. A true fist has all fingers closed.
        index_extended = is_finger_extended_by_curl(hand_frame, 5, 6, 8)
        middle_extended = is_finger_extended_by_curl(hand_frame, 9, 10, 12)
        ring_extended = is_finger_extended_by_curl(hand_frame, 13, 14, 16)
        pinky_extended = is_finger_extended_by_curl(hand_frame, 17, 18, 20)
        
        is_fist = not (index_extended or middle_extended or ring_extended or pinky_extended)
        
        # It's a pinch if distance is small and it's not a fist
        return not is_fist
