from gestures.gesture_state_machine import GestureStateMachine
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended
from gestures.motion_utils import WristVelocityTracker

class OpenPalmGesture(GestureStateMachine):
    name = "open_palm"

    def __init__(self, hold_frames_required: int = 6, max_velocity: float = 0.3, **kwargs):
        super().__init__(hold_frames_required=hold_frames_required, **kwargs)
        self.max_velocity = max_velocity
        self._velocity = WristVelocityTracker(window_ms=200.0)

    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        # The user requested: fingertip landmark farther from the wrist than the corresponding knuckle landmark.
        # This translates to threshold=1.0 (dist_tip > dist_mcp * 1.0).
        
        # Check thumb (mcp: 2, tip: 4)
        if not is_finger_extended(hand_frame, 2, 4, threshold=1.0):
            return False
        # Check index (mcp: 5, tip: 8)
        if not is_finger_extended(hand_frame, 5, 8, threshold=1.0):
            return False
        # Check middle (mcp: 9, tip: 12)
        if not is_finger_extended(hand_frame, 9, 12, threshold=1.0):
            return False
        # Check ring (mcp: 13, tip: 16)
        if not is_finger_extended(hand_frame, 13, 16, threshold=1.0):
            return False
        # Check pinky (mcp: 17, tip: 20)
        if not is_finger_extended(hand_frame, 17, 20, threshold=1.0):
            return False
            
        v = self._velocity.update(hand_frame.wrist.x, hand_frame.timestamp_ms)
        return abs(v) < self.max_velocity
