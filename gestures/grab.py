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


class GrabGesture(GestureStateMachine):
    name = "grab"

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        raise NotImplementedError(
            "TODO(V2): for each of the 4 non-thumb fingers, compare fingertip-to-wrist "
            "distance vs knuckle-to-wrist distance; if fingertip is closer for all 4, "
            "the hand is a closed fist"
        )
