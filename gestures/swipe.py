"""
gestures/swipe.py  (V2)

Horizontal swipe of the whole hand -> previous/next virtual desktop.

Detection is velocity-based, not position-based: track wrist x-position
over a short rolling window and detect a fast, sustained motion in one
direction, then classify direction and emit a single event (respecting
the gesture's cooldown so one swipe doesn't refire mid-motion).
"""
from __future__ import annotations

from collections import deque

from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame


class SwipeGesture(GestureStateMachine):
    name = "swipe"

    def __init__(self, velocity_threshold: float = 0.8, window_size: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.velocity_threshold = velocity_threshold
        self._history: deque[tuple[float, float]] = deque(maxlen=window_size)  # (x, timestamp_ms)

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        raise NotImplementedError(
            "TODO(V2): push (wrist.x, timestamp) into self._history, compute "
            "velocity across the window, return True if it exceeds "
            "self.velocity_threshold in either direction"
        )

    def direction(self) -> str:
        """Returns 'left' or 'right' based on the sign of the recent velocity."""
        raise NotImplementedError("TODO(V2): derive direction from self._history")
