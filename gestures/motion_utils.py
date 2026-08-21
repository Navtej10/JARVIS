"""
Shared wrist-velocity tracking. SwipeGesture wants HIGH velocity,
OpenPalmGesture wants LOW velocity — both must read from the exact same
tracker so a fast swipe and a still open palm can never both read as "true"
from inconsistent velocity math.

Velocity is computed from real elapsed time (HandFrame.timestamp_ms), never
frame count — see the main.py diagnostic notes below for why that matters.
"""
from __future__ import annotations
from collections import deque


class WristVelocityTracker:
    def __init__(self, window_ms: float = 200.0):
        self.window_ms = window_ms
        self._history: deque[tuple[float, float]] = deque()  # (x, timestamp_ms)

    def update(self, x: float, timestamp_ms: float) -> float:
        self._history.append((x, timestamp_ms))
        while self._history and (timestamp_ms - self._history[0][1]) > self.window_ms:
            self._history.popleft()
        if len(self._history) < 2:
            return 0.0
        (x0, t0), (x1, t1) = self._history[0], self._history[-1]
        dt = (t1 - t0) / 1000.0
        return (x1 - x0) / dt if dt > 0 else 0.0
