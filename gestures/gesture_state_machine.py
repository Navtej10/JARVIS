"""
gestures/gesture_state_machine.py

Core abstraction for all gestures in this project. Every gesture (pinch,
swipe, grab, rotate, ...) is modeled as a state machine, NOT a single-frame
classification. This is what eliminates most false triggers and makes
"grab and move" feel intentional rather than twitchy.

States:
    IDLE    -> gesture not currently happening
    START   -> gesture just began this frame
    HOLD    -> gesture is ongoing (e.g. pinch held, fist held)
    RELEASE -> gesture just ended this frame

Every concrete gesture (pinch.py, swipe.py, grab.py, rotate.py) subclasses
GestureStateMachine and implements `_is_condition_met()`.

TODO(V1): use this for Pinch (click/drag) and index-finger move.
TODO(V2): use this for Swipe, OpenPalm, Fist/Grab.
TODO(V2): add per-gesture cooldown timers so e.g. a swipe can't refire
          multiple times within one continuous motion.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from tracking.hand_tracker import HandFrame


class GestureState(Enum):
    IDLE = "idle"
    START = "start"
    HOLD = "hold"
    RELEASE = "release"


@dataclass
class GestureEvent:
    name: str
    state: GestureState
    hand_frame: HandFrame
    timestamp_ms: int
    payload: dict | None = None  # e.g. {"direction": "left"} for swipe


class GestureStateMachine(ABC):
    """
    Base class for all gesture detectors.

    Subclasses implement `_is_condition_met(hand_frame)` -- the raw geometric
    test (e.g. "is thumb tip within pinch_distance_threshold of index tip?").
    This base class handles the START/HOLD/RELEASE bookkeeping, debounce,
    and cooldown so individual gestures stay simple.
    """

    name: str = "unnamed_gesture"

    def __init__(self, hold_frames_required: int = 3, cooldown_ms: int = 250):
        self.hold_frames_required = hold_frames_required
        self.cooldown_ms = cooldown_ms
        self._state = GestureState.IDLE
        self._consecutive_true_frames = 0
        self._last_release_ms: float = -float('inf')

    @abstractmethod
    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        """Raw per-frame geometric test. Implemented by pinch/swipe/grab/rotate."""
        raise NotImplementedError

    def update(self, hand_frame: HandFrame, now_ms: float) -> Optional[GestureEvent]:
        """
        Feed one frame in. Returns a GestureEvent if the state changed,
        otherwise None (most frames should return None once the debounce
        and cooldown logic settles).
        """
        if self._state == GestureState.IDLE and (now_ms - self._last_release_ms < self.cooldown_ms):
            self._consecutive_true_frames = 0
            return None
            
        condition_met = self._is_condition_met(hand_frame)
        
        if condition_met:
            self._consecutive_true_frames += 1
            if self._state == GestureState.IDLE:
                if self._consecutive_true_frames >= self.hold_frames_required:
                    self._state = GestureState.START
                    return GestureEvent(self.name, self._state, hand_frame, now_ms)
            elif self._state == GestureState.START:
                self._state = GestureState.HOLD
                return GestureEvent(self.name, self._state, hand_frame, now_ms)
            elif self._state == GestureState.HOLD:
                return GestureEvent(self.name, self._state, hand_frame, now_ms)
        else:
            self._consecutive_true_frames = 0
            if self._state in (GestureState.START, GestureState.HOLD):
                event = GestureEvent(self.name, GestureState.RELEASE, hand_frame, now_ms)
                self._state = GestureState.IDLE
                self._last_release_ms = now_ms
                return event
                
        return None
