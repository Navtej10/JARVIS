"""
gestures/rotate.py  (V4)

Two-hand gesture support:
  - Pinch with both hands, hands moving apart/together -> scale object
  - Pinch + rotate wrist -> rotate object
  - Pinch + orbit hand around object -> orbit camera view

Requires HandTracker configured with max_hands=2 and stable left/right
identity across frames (see tracking/hand_tracker.py TODO).
"""
from __future__ import annotations

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame, Handedness


class TwoHandScaleGesture(GestureStateMachine):
    name = "two_hand_scale"

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        # NOTE: this gesture needs BOTH hands' frames, so the update() call
        # signature in practice differs from single-hand gestures -- see
        # TODO below for how this base class should be extended.
        raise NotImplementedError(
            "TODO(V4): extend GestureStateMachine (or add a TwoHandGestureStateMachine "
            "variant) to accept a pair of HandFrames; condition = both hands pinching "
            "and their inter-hand distance changing beyond a threshold since START"
        )


class RotateGesture(GestureStateMachine):
    name = "rotate"

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        raise NotImplementedError(
            "TODO(V4): condition = pinch held AND wrist roll angle has changed "
            "beyond a threshold since START; estimate roll from the vector between "
            "landmark 5 (index knuckle) and landmark 17 (pinky knuckle)"
        )
