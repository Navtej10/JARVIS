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
from typing import Optional

from gestures.gesture_state_machine import GestureStateMachine, GestureEvent, GestureState
from tracking.hand_tracker import HandFrame


class SwipeGesture(GestureStateMachine):
    name = "swipe"

    def __init__(self, velocity_threshold: float = 0.8, window_size: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.velocity_threshold = velocity_threshold
        self._history: deque[tuple[float, float]] = deque(maxlen=window_size)  # (x, timestamp_ms)
        self._recent_velocity = 0.0

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        wrist_x = hand_frame.wrist.x
        ts = hand_frame.timestamp_ms
        self._history.append((wrist_x, ts))
        
        if len(self._history) < self._history.maxlen:
            return False
            
        dx = self._history[-1][0] - self._history[0][0]
        dt = (self._history[-1][1] - self._history[0][1]) / 1000.0  # seconds
        
        if dt <= 0:
            return False
            
        velocity = dx / dt
        if abs(velocity) > self.velocity_threshold:
            self._recent_velocity = velocity
            return True
            
        return False

    def direction(self) -> str:
        """Returns 'left' or 'right' based on the sign of the recent velocity."""
        return "left" if self._recent_velocity < 0 else "right"

    def update(self, hand_frame: HandFrame, now_ms: float) -> Optional[GestureEvent]:
        if now_ms - self._last_release_ms < self.cooldown_ms:
            return None
            
        if self._is_condition_met(hand_frame):
            self._last_release_ms = now_ms
            self._history.clear()
            return GestureEvent(
                self.name, 
                GestureState.START, 
                hand_frame, 
                now_ms, 
                payload={"direction": self.direction()}
            )
            
        return None
