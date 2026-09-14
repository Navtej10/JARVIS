import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import cv2
from tracking.hand_tracker import HandTracker, Handedness

def main():
    print("Starting Two-Hand Tracker Debug...")
    print("Press 'q' or 'esc' to quit.")
    
    tracker = HandTracker(camera_index=0, max_hands=2)
    tracker.start()
    
    try:
        while True:
            hands = tracker.read()
            frame = tracker.latest_frame
            
            if frame is not None:
                # Check for same handedness
                if len(hands) == 2:
                    if hands[0].handedness == hands[1].handedness:
                        print(f"WARNING: Both hands detected as {hands[0].handedness.value}!")
                
                # Draw hands
                for hand in hands:
                    # Blue for Left, Green for Right
                    if hand.handedness == Handedness.LEFT:
                        color = (255, 0, 0)  # BGR format: Blue
                    else:
                        color = (0, 255, 0)  # BGR format: Green
                    
                    h, w, _ = frame.shape
                    
                    # Draw landmarks
                    for lm in hand.landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5, color, cv2.FILLED)
                    
                    # Label the hand near the wrist
                    wrist = hand.landmarks[0]
                    wx, wy = int(wrist.x * w), int(wrist.y * h)
                    cv2.putText(frame, hand.handedness.name, (wx, wy + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                cv2.imshow("Two-Hand Tracker Debug", frame)
                
            key = cv2.waitKey(1)
            if key in (27, ord('q')):
                break
                
    finally:
        tracker.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
