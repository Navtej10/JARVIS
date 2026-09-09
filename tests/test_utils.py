import pytest
import math
from tracking.hand_tracker import HandFrame
from gestures.utils import is_finger_extended, is_finger_extended_by_curl, finger_curl

class DummyLandmark:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

def test_finger_extension_comparison():
    # Synthetic hand rotated 45 degrees
    # We want a situation where the distance from wrist to tip is ambiguous (ratio-based fails), 
    # but the angle is clearly bent or straight.
    
    # Let's say wrist is at origin.
    wrist = DummyLandmark(0, 0, 0)
    
    # Straight finger tilted 45 degrees forward
    # MCP is at (0, 10, 0).
    # PIP is at (0, 15, 5).
    # TIP is at (0, 20, 10).
    landmarks = [DummyLandmark(0, 0, 0) for _ in range(21)]
    landmarks[0] = wrist
    landmarks[5] = DummyLandmark(0, 10, 0)
    landmarks[6] = DummyLandmark(0, 15, 5)
    landmarks[8] = DummyLandmark(0, 20, 10)
    
    hand_frame_straight = HandFrame(landmarks=landmarks, handedness="Right", detection_confidence=1.0, timestamp_ms=0)
    
    # Both methods should say extended for straight finger
    assert is_finger_extended(hand_frame_straight, 5, 8) == True
    assert is_finger_extended_by_curl(hand_frame_straight, 5, 6, 8) == True

    # Curled finger, tilted such that distance to tip is still large
    # MCP is at (0, 10, 0)
    # PIP is at (0, 15, 0)
    # TIP is curled back: TIP at (0, 15, -5)
    # Distance wrist to TIP = sqrt(15^2 + (-5)^2) = sqrt(250) ≈ 15.8
    # Ratio = 15.8 / 10 = 1.58 > 1.2. Old method says it is extended.
    landmarks_curled = [DummyLandmark(0, 0, 0) for _ in range(21)]
    landmarks_curled[0] = wrist
    landmarks_curled[5] = DummyLandmark(0, 10, 0)
    landmarks_curled[6] = DummyLandmark(0, 15, 0)
    landmarks_curled[8] = DummyLandmark(0, 15, -5)
    
    hand_frame_curled = HandFrame(landmarks=landmarks_curled, handedness="Right", detection_confidence=1.0, timestamp_ms=0)
    
    # Old method fails (says extended when it shouldn't)
    assert is_finger_extended(hand_frame_curled, 5, 8) == True
    
    # New method succeeds (says not extended because angle is 90 degrees, curl=0.0)
    assert is_finger_extended_by_curl(hand_frame_curled, 5, 6, 8) == False
