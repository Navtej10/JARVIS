from __future__ import annotations

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended


class OpenPalmGesture(GestureStateMachine):
    name = "open_palm"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        # Check if all 4 main fingers are extended
        index_extended = is_finger_extended(hand_frame, 5, 8)
        middle_extended = is_finger_extended(hand_frame, 9, 12)
        ring_extended = is_finger_extended(hand_frame, 13, 16)
        pinky_extended = is_finger_extended(hand_frame, 17, 20)
        
        return index_extended and middle_extended and ring_extended and pinky_extended
