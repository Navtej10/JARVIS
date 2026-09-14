import pytest
from tracking.hand_tracker import HandFrame, Handedness, Landmark
from gestures.gesture_state_machine import TwoHandGestureStateMachine, GestureState, TwoHandGestureEvent

class BothHandsGesture(TwoHandGestureStateMachine):
    name = "both_hands"
    
    def _is_condition_met(self, hands: dict[Handedness, HandFrame]) -> bool:
        return Handedness.LEFT in hands and Handedness.RIGHT in hands

def make_hand(handedness: Handedness) -> HandFrame:
    return HandFrame(
        handedness=handedness,
        landmarks=[Landmark(x=0, y=0, z=0) for _ in range(21)],
        detection_confidence=0.9,
        timestamp_ms=0
    )

def test_two_hand_gesture_state_transitions():
    gesture = BothHandsGesture(hold_frames_required=3, cooldown_ms=250)
    
    left_hand = make_hand(Handedness.LEFT)
    right_hand = make_hand(Handedness.RIGHT)
    
    both_hands = {Handedness.LEFT: left_hand, Handedness.RIGHT: right_hand}
    one_hand = {Handedness.LEFT: left_hand}
    no_hands = {}
    
    now = 1000.0
    
    # Frame 1: Only one hand. Should be None.
    assert gesture.update(one_hand, now) is None
    
    # Frame 2: Both hands. 1 frame of hold.
    now += 16
    assert gesture.update(both_hands, now) is None
    
    # Frame 3: Both hands. 2 frames of hold.
    now += 16
    assert gesture.update(both_hands, now) is None
    
    # Frame 4: Both hands. 3 frames of hold. START!
    now += 16
    event = gesture.update(both_hands, now)
    assert event is not None
    assert event.state == GestureState.START
    assert event.name == "both_hands"
    
    # Frame 5: Both hands. HOLD!
    now += 16
    event = gesture.update(both_hands, now)
    assert event is not None
    assert event.state == GestureState.HOLD
    
    # Frame 6: Right hand disappears. RELEASE!
    now += 16
    event = gesture.update(one_hand, now)
    assert event is not None
    assert event.state == GestureState.RELEASE
    
    # Frame 7: Both hands come back immediately, but cooldown prevents refire.
    now += 16
    assert gesture.update(both_hands, now) is None
    
    # Frame 8-10: Cooldown still active, wait out the 250ms cooldown.
    now += 250
    assert gesture.update(both_hands, now) is None
    now += 16
    assert gesture.update(both_hands, now) is None
    now += 16
    event = gesture.update(both_hands, now)
    assert event is not None
    assert event.state == GestureState.START
