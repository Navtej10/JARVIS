"""
gestures/grab.py  (V2, extended in V3)

Closed fist -> grab a window (V2) or a spatial UI panel (V3).
Fist + move -> move the grabbed target; release fist -> drop it.

Detection: all four non-thumb fingertips curled toward the palm (fingertip
landmarks closer to the wrist than their corresponding knuckle landmarks).
"""
from __future__ import annotations

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended


class GrabGesture(GestureStateMachine):
    name = "grab"

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        # Check index (mcp: 5, tip: 8)
        if is_finger_extended(hand_frame, 5, 8, threshold=1.0):
            return False
        # Check middle (mcp: 9, tip: 12)
        if is_finger_extended(hand_frame, 9, 12, threshold=1.0):
            return False
        # Check ring (mcp: 13, tip: 16)
        if is_finger_extended(hand_frame, 13, 16, threshold=1.0):
            return False
        # Check pinky (mcp: 17, tip: 20)
        if is_finger_extended(hand_frame, 17, 20, threshold=1.0):
            return False
            
        return True
