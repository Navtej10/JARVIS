"""
gestures/point.py

Detects a pointing gesture (index finger extended, other fingers closed).
"""
from __future__ import annotations

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended_by_curl


class PointGesture(GestureStateMachine):
    name = "point"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        # Index is extended
        index_extended = is_finger_extended_by_curl(hand_frame, 5, 6, 8)
        
        # Middle, Ring, Pinky are closed
        middle_extended = is_finger_extended_by_curl(hand_frame, 9, 10, 12)
        ring_extended = is_finger_extended_by_curl(hand_frame, 13, 14, 16)
        pinky_extended = is_finger_extended_by_curl(hand_frame, 17, 18, 20)
        
        return index_extended and not (middle_extended or ring_extended or pinky_extended)
