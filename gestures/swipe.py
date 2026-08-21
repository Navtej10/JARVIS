"""
gestures/swipe.py  (V2)

Horizontal swipe of the whole hand -> previous/next virtual desktop.

Detection is velocity-based, not position-based: track wrist x-position
over a short rolling window and detect a fast, sustained motion in one
direction, then classify direction and emit a single event (respecting
the gesture's cooldown so one swipe doesn't refire mid-motion).
"""
from __future__ import annotations

from typing import Optional

from gestures.gesture_state_machine import GestureStateMachine, GestureEvent, GestureState
from tracking.hand_tracker import HandFrame
from gestures.motion_utils import WristVelocityTracker


class SwipeGesture(GestureStateMachine):
    name = "swipe"

    def __init__(self, velocity_threshold: float = 0.5, window_ms: float = 100.0, **kwargs):
        super().__init__(**kwargs)
        self.velocity_threshold = velocity_threshold
        self._velocity = WristVelocityTracker(window_ms=window_ms)
        self._last_velocity = 0.0

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        from gestures.utils import is_finger_extended
        
        # Require hand to be a full open palm (all fingers extended) to avoid false swipes
        if not is_finger_extended(hand_frame, 2, 4, threshold=1.0) or \
           not is_finger_extended(hand_frame, 5, 8, threshold=1.0) or \
           not is_finger_extended(hand_frame, 9, 12, threshold=1.0) or \
           not is_finger_extended(hand_frame, 13, 16, threshold=1.0) or \
           not is_finger_extended(hand_frame, 17, 20, threshold=1.0):
            self._velocity.update(hand_frame.wrist.x, hand_frame.timestamp_ms)
            return False

        self._last_velocity = self._velocity.update(hand_frame.wrist.x, hand_frame.timestamp_ms)
        return abs(self._last_velocity) > self.velocity_threshold

    def direction(self) -> str:
        """Returns 'left' or 'right' based on the sign of the recent velocity."""
        return "left" if self._last_velocity < 0 else "right"

    def update(self, hand_frame: HandFrame, now_ms: float) -> Optional[GestureEvent]:
        if now_ms - self._last_release_ms < self.cooldown_ms:
            self._velocity.update(hand_frame.wrist.x, hand_frame.timestamp_ms)
            return None
            
        if self._is_condition_met(hand_frame):
            self._last_release_ms = now_ms
            return GestureEvent(
                self.name, 
                GestureState.START, 
                hand_frame, 
                now_ms, 
                payload={"direction": self.direction()}
            )
            
        return None
