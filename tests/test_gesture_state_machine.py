"""
Unit tests for gestures/gesture_state_machine.py.

Keep these fast and hardware-free: construct fake HandFrame objects rather
than touching the camera or MediaPipe. This is what lets you validate the
debounce/cooldown logic in isolation before ever picking up the webcam.

TODO(V1): once GestureStateMachine.update() is implemented, add cases for:
  - condition true for < hold_frames_required frames -> no START emitted (debounce works)
  - condition true for >= hold_frames_required frames -> START then HOLD events
  - condition goes false -> RELEASE event emitted exactly once
  - a second gesture within cooldown_ms of a RELEASE -> suppressed until cooldown elapses
"""
from gestures.gesture_state_machine import GestureStateMachine, GestureState
from tracking.hand_tracker import HandFrame, Landmark, Handedness

class DummyGesture(GestureStateMachine):
    name = "dummy"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condition = False
        
    def _is_condition_met(self, hand_frame: HandFrame) -> bool:
        return self.condition

def create_dummy_hand() -> HandFrame:
    # 21 empty landmarks
    landmarks = [Landmark(0,0,0) for _ in range(21)]
    return HandFrame(Handedness.RIGHT, landmarks, 1.0, 0)

def test_gesture_debounce_and_transitions():
    gesture = DummyGesture(hold_frames_required=3, cooldown_ms=100)
    hand = create_dummy_hand()
    
    # 1. Condition true but less than hold_frames_required -> no event
    gesture.condition = True
    assert gesture.update(hand, 10.0) is None
    assert gesture.update(hand, 20.0) is None
    
    # 2. Reaches hold_frames_required -> START event
    evt = gesture.update(hand, 30.0)
    assert evt is not None
    assert evt.state == GestureState.START
    assert evt.name == "dummy"
    
    # 3. Subsequent true frames -> HOLD event
    evt = gesture.update(hand, 40.0)
    assert evt is not None
    assert evt.state == GestureState.HOLD
    
    evt = gesture.update(hand, 50.0)
    assert evt is not None
    assert evt.state == GestureState.HOLD
    
    # 4. Condition goes false -> RELEASE event
    gesture.condition = False
    evt = gesture.update(hand, 60.0)
    assert evt is not None
    assert evt.state == GestureState.RELEASE
    
    # 5. False again -> None
    assert gesture.update(hand, 70.0) is None

def test_gesture_cooldown():
    gesture = DummyGesture(hold_frames_required=2, cooldown_ms=100)
    hand = create_dummy_hand()
    
    # Trigger first gesture
    gesture.condition = True
    assert gesture.update(hand, 10.0) is None
    evt = gesture.update(hand, 20.0)
    assert evt.state == GestureState.START
    
    # Release it at 30.0ms
    gesture.condition = False
    evt = gesture.update(hand, 30.0)
    assert evt.state == GestureState.RELEASE
    
    # Try to trigger again at 50.0ms (during 100ms cooldown)
    gesture.condition = True
    assert gesture.update(hand, 50.0) is None
    assert gesture.update(hand, 60.0) is None
    assert gesture.update(hand, 70.0) is None
    
    # Cooldown ends at 130.0ms (30 + 100)
    # Re-trigger after cooldown
    assert gesture.update(hand, 140.0) is None # Frame 1
    evt = gesture.update(hand, 150.0) # Frame 2
    assert evt is not None
    assert evt.state == GestureState.START
