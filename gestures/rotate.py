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

from gestures.gesture_state_machine import GestureStateMachine, TwoHandGestureStateMachine, GestureState, TwoHandGestureEvent, GestureEvent
from tracking.hand_tracker import HandFrame, Handedness
from gestures.utils import calculate_normalized_pinch_distance
from typing import Optional
import math


def snap_value(value: float, increment: float) -> float:
    """Rounds value to the nearest increment."""
    if increment <= 0:
        return value
    snapped = round((value / increment) + 1e-9) * increment
    return round(snapped, 5)


class TwoHandScaleGesture(TwoHandGestureStateMachine):
    name = "two_hand_scale"

    def __init__(self, engage_threshold: float = 0.045, release_threshold: float = 0.065, scale_snap_increment: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.engage_threshold = engage_threshold
        self.release_threshold = release_threshold
        self.scale_snap_increment = scale_snap_increment
        self.baseline_distance: float = 1.0

    def _is_condition_met(self, hands: dict[Handedness, HandFrame]) -> bool:
        if Handedness.LEFT not in hands or Handedness.RIGHT not in hands:
            return False
            
        left_dist = calculate_normalized_pinch_distance(hands[Handedness.LEFT])
        right_dist = calculate_normalized_pinch_distance(hands[Handedness.RIGHT])
        
        if left_dist is None or right_dist is None:
            return False
            
        threshold = self.release_threshold if self._state in (GestureState.HOLD, GestureState.START) else self.engage_threshold
        
        return left_dist < threshold and right_dist < threshold

    def _get_inter_hand_distance(self, hands: dict[Handedness, HandFrame]) -> float:
        l_hand = hands[Handedness.LEFT]
        r_hand = hands[Handedness.RIGHT]
        
        l_pinch_pt = (
            (l_hand.thumb_tip.x + l_hand.index_tip.x) / 2,
            (l_hand.thumb_tip.y + l_hand.index_tip.y) / 2,
            (l_hand.thumb_tip.z + l_hand.index_tip.z) / 2
        )
        r_pinch_pt = (
            (r_hand.thumb_tip.x + r_hand.index_tip.x) / 2,
            (r_hand.thumb_tip.y + r_hand.index_tip.y) / 2,
            (r_hand.thumb_tip.z + r_hand.index_tip.z) / 2
        )
        
        return math.dist(l_pinch_pt, r_pinch_pt)

    def update(self, hands: dict[Handedness, HandFrame], now_ms: float) -> Optional[TwoHandGestureEvent]:
        event = super().update(hands, now_ms)
        if event:
            if event.state == GestureState.START:
                self.baseline_distance = self._get_inter_hand_distance(hands)
                if self.baseline_distance == 0:
                    self.baseline_distance = 0.001
                event.payload = {"scale_factor": 1.0}
            elif event.state == GestureState.HOLD:
                current_distance = self._get_inter_hand_distance(hands)
                scale_factor = current_distance / self.baseline_distance
                scale_factor = snap_value(scale_factor, self.scale_snap_increment)
                event.payload = {"scale_factor": scale_factor}
        return event


class RotateGesture(GestureStateMachine):
    name = "rotate"

    def __init__(self, engage_threshold: float = 0.045, release_threshold: float = 0.065, rotate_snap_increment_degrees: float = 15.0, **kwargs):
        super().__init__(**kwargs)
        self.engage_threshold = engage_threshold
        self.release_threshold = release_threshold
        self.rotate_snap_increment_rad = math.radians(rotate_snap_increment_degrees)
        self.baseline_roll: float = 0.0

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        normalized_dist = calculate_normalized_pinch_distance(hand_frame)
        if normalized_dist is None:
            return False
            
        threshold = self.release_threshold if self._state in (GestureState.HOLD, GestureState.START) else self.engage_threshold
        return normalized_dist < threshold

    def _get_roll_angle(self, hand_frame: HandFrame) -> float:
        # landmark 5 = index knuckle, landmark 17 = pinky knuckle
        index_knuckle = hand_frame.landmarks[5]
        pinky_knuckle = hand_frame.landmarks[17]
        
        # Calculate angle of the vector from index to pinky knuckle
        dx = pinky_knuckle.x - index_knuckle.x
        dy = pinky_knuckle.y - index_knuckle.y
        return math.atan2(dy, dx)

    def update(self, hand_frame: HandFrame, now_ms: float) -> Optional[GestureEvent]:
        # Note: RotateGesture is a single-hand gesture (extends GestureStateMachine), 
        # so it receives a HandFrame, not a dict of hands.
        # But wait, GestureStateMachine's update returns a GestureEvent, we can attach payload to it.
        event = super().update(hand_frame, now_ms)
        if event:
            if event.state == GestureState.START:
                self.baseline_roll = self._get_roll_angle(hand_frame)
                event.payload = {"delta_angle": 0.0}
            elif event.state == GestureState.HOLD:
                current_roll = self._get_roll_angle(hand_frame)
                
                # Calculate shortest angular difference (handling -pi to pi wrap around)
                delta_angle = current_roll - self.baseline_roll
                delta_angle = (delta_angle + math.pi) % (2 * math.pi) - math.pi
                
                delta_angle = snap_value(delta_angle, self.rotate_snap_increment_rad)
                event.payload = {"delta_angle": delta_angle}
        return event


class OrbitGesture(GestureStateMachine):
    name = "orbit_camera"

    def __init__(self, engage_threshold: float = 0.045, release_threshold: float = 0.065, **kwargs):
        super().__init__(**kwargs)
        self.engage_threshold = engage_threshold
        self.release_threshold = release_threshold
        self.baseline_angle: float = 0.0

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        normalized_dist = calculate_normalized_pinch_distance(hand_frame)
        if normalized_dist is None:
            return False
            
        threshold = self.release_threshold if self._state in (GestureState.HOLD, GestureState.START) else self.engage_threshold
        return normalized_dist < threshold

    def _get_screen_angle(self, hand_frame: HandFrame) -> float:
        # Use normalized coordinates (0-1) where center is (0.5, 0.5)
        # This matches the angle around the center of the screen
        index_tip = hand_frame.index_tip
        dx = index_tip.x - 0.5
        dy = index_tip.y - 0.5
        return math.atan2(dy, dx)

    def update(self, hand_frame: HandFrame, now_ms: float) -> Optional[GestureEvent]:
        event = super().update(hand_frame, now_ms)
        if event:
            if event.state == GestureState.START:
                self.baseline_angle = self._get_screen_angle(hand_frame)
                event.payload = {"delta_angle": 0.0}
            elif event.state == GestureState.HOLD:
                current_angle = self._get_screen_angle(hand_frame)
                delta_angle = current_angle - self.baseline_angle
                delta_angle = (delta_angle + math.pi) % (2 * math.pi) - math.pi
                event.payload = {"delta_angle": delta_angle}
        return event
