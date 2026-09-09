import pytest
from tracking.hand_tracker import HandTracker, Landmark

def test_hallucination_filter():
    # We will test the logic used inside HandTracker.read()
    # To do this cleanly, we can mock the MediaPipe results, 
    # but the easiest way is to extract the filter into a standalone 
    # function, or simply mock the `process` method of `_hands`.
    # Let's mock `_hands.process` and `_cap.read`.

    class MockHandednessClass:
        def __init__(self, label, score):
            self.label = label
            self.score = score

    class MockHandedness:
        def __init__(self, label, score):
            self.classification = [MockHandednessClass(label, score)]

    class MockLandmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    class MockHandLandmarks:
        def __init__(self, landmarks):
            self.landmark = landmarks

    class MockResults:
        def __init__(self, landmarks_list, handedness_list):
            self.multi_hand_landmarks = landmarks_list
            self.multi_handedness = handedness_list

    tracker = HandTracker()
    tracker._hands = type('obj', (object,), {
        'process': lambda img: MockResults(
            [MockHandLandmarks([MockLandmark(0,0,0) for _ in range(21)])], 
            [MockHandedness('Right', 0.9)]
        )
    })
    import numpy as np
    tracker._cap = type('obj', (object,), {
        'read': lambda: (True, np.zeros((10,10,3), dtype=np.uint8)) 
    })

    # Since we set image_rgb, we must patch cv2.cvtColor to not fail
    import cv2
    import numpy as np
    original_cvt = cv2.cvtColor
    cv2.cvtColor = lambda *args, **kwargs: np.zeros((10,10,3), dtype=np.uint8)

    try:
        # Case 1: Valid hand shape
        # wrist = (0, 0, 0), middle_mcp = (0, 10, 0) -> span = 10
        # index_mcp = (-2, 5, 0), pinky_mcp = (3, 5, 0) -> width = 5
        # aspect = 2.0 (Valid)
        valid_lms = [MockLandmark(0,0,0) for _ in range(21)]
        valid_lms[0] = MockLandmark(0, 0, 0) # wrist
        valid_lms[9] = MockLandmark(0, 10, 0) # middle mcp
        valid_lms[5] = MockLandmark(-2, 5, 0) # index mcp
        valid_lms[17] = MockLandmark(3, 5, 0) # pinky mcp
        
        tracker._hands.process = lambda img: MockResults(
            [MockHandLandmarks(valid_lms)], 
            [MockHandedness('Right', 0.9)]
        )
        
        frames = tracker.read()
        assert len(frames) == 1
        
        # Case 2: Degenerate stretched hand shape (aspect > 6)
        # wrist = (0, 0, 0), middle_mcp = (0, 20, 0) -> span = 20
        # index_mcp = (0, 10, 0), pinky_mcp = (2, 10, 0) -> width = 2
        # aspect = 10.0 (Invalid)
        invalid_stretched_lms = [MockLandmark(0,0,0) for _ in range(21)]
        invalid_stretched_lms[0] = MockLandmark(0, 0, 0) # wrist
        invalid_stretched_lms[9] = MockLandmark(0, 20, 0) # middle mcp
        invalid_stretched_lms[5] = MockLandmark(0, 10, 0) # index mcp
        invalid_stretched_lms[17] = MockLandmark(2, 10, 0) # pinky mcp
        
        tracker._hands.process = lambda img: MockResults(
            [MockHandLandmarks(invalid_stretched_lms)], 
            [MockHandedness('Right', 0.9)]
        )
        
        frames = tracker.read()
        assert len(frames) == 0
        
        # Case 3: Degenerate flat hand shape (aspect < 0.5)
        # wrist = (0, 0, 0), middle_mcp = (0, 2, 0) -> span = 2
        # index_mcp = (-5, 1, 0), pinky_mcp = (5, 1, 0) -> width = 10
        # aspect = 0.2 (Invalid)
        invalid_flat_lms = [MockLandmark(0,0,0) for _ in range(21)]
        invalid_flat_lms[0] = MockLandmark(0, 0, 0) # wrist
        invalid_flat_lms[9] = MockLandmark(0, 2, 0) # middle mcp
        invalid_flat_lms[5] = MockLandmark(-5, 1, 0) # index mcp
        invalid_flat_lms[17] = MockLandmark(5, 1, 0) # pinky mcp
        
        tracker._hands.process = lambda img: MockResults(
            [MockHandLandmarks(invalid_flat_lms)], 
            [MockHandedness('Right', 0.9)]
        )
        
        frames = tracker.read()
        assert len(frames) == 0
        
    finally:
        cv2.cvtColor = original_cvt
