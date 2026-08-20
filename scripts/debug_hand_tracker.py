import cv2
import mediapipe as mp
import os
import sys

# Add parent directory to path to allow importing from tracking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tracking.hand_tracker import HandTracker
from tracking.landmark_processor import LandmarkProcessor
from gestures.pinch import PinchGesture
from gestures.swipe import SwipeGesture
from gestures.open_palm import OpenPalmGesture
from gestures.grab import GrabGesture
from interaction.window_manager import WindowManager

import json

def load_calibration():
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    calib_file = os.path.join(config_dir, 'calibration.json')
    if os.path.exists(calib_file):
        with open(calib_file, 'r') as f:
            return json.load(f)
    return {}

def main():
    calib = load_calibration()
    tracker = HandTracker(camera_index=calib.get("camera", {}).get("index", 0), max_hands=2)
    
    screen_width = calib.get("screen", {}).get("width", 1920)
    screen_height = calib.get("screen", {}).get("height", 1080)
    processor = LandmarkProcessor(calibration=calib, screen_width=screen_width, screen_height=screen_height)
    
    pinch_detector = PinchGesture(distance_threshold=calib.get("gesture_thresholds", {}).get("pinch_distance_threshold", 0.045))
    swipe_detector = SwipeGesture(velocity_threshold=calib.get("gesture_thresholds", {}).get("swipe_velocity_threshold", 0.8))
    open_palm_detector = OpenPalmGesture(hold_frames_required=20)
    grab_detector = GrabGesture()
    
    wm = WindowManager()
    palm_fired_this_hold = False
    
    # State for window dragging
    held_window = None
    drag_anchor = None
    
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    mp_drawing_styles = mp.solutions.drawing_styles

    print("Starting video feed. Press 'q' to quit.")
    
    for hand_frames in tracker.stream():
        frame = tracker.latest_frame
        if frame is None:
            continue
            
        # We can use MediaPipe's drawing_utils by creating our own NormalizedLandmarkList, 
        # or we can draw manually, but since we are using MediaPipe's drawing utils, we can just 
        # create the protobuf object or just run MP again? No, we shouldn't run MP again.
        # It's easier to create a landmark protobuf list or just draw circles manually, but the user asked
        # to "use cv2.imshow + MediaPipe's drawing_utils".
        
        # Let's rebuild the protobuf message for drawing
        from mediapipe.framework.formats import landmark_pb2
        
        for hf in hand_frames:
            # Process the index tip into a smoothed ScreenPoint
            screen_point = processor.to_screen_point(hf.index_tip)
            
            # --- TEST GESTURE STATE MACHINE ---
            event = pinch_detector.update(hf, hf.timestamp_ms)
            if event:
                print(f"\n---> GESTURE EVENT: {event.name.upper()} | State: {event.state.name} <---")
                
            swipe_event = swipe_detector.update(hf, hf.timestamp_ms)
            if swipe_event:
                dir_str = swipe_event.payload.get('direction')
                print(f"\n---> GESTURE EVENT: {swipe_event.name.upper()} | State: {swipe_event.state.name} | Dir: {dir_str} <---")
                if swipe_event.state.name == "START":
                    wm.switch_desktop(dir_str)

            palm_event = open_palm_detector.update(hf, hf.timestamp_ms)
            if palm_event:
                print(f"\n---> GESTURE EVENT: {palm_event.name.upper()} | State: {palm_event.state.name} <---")
                if palm_event.state.name == "START":
                    palm_fired_this_hold = False
                elif palm_event.state.name == "HOLD" and not palm_fired_this_hold:
                    print("Show Desktop triggered!")
                    wm.show_desktop()
                    palm_fired_this_hold = True

            grab_event = grab_detector.update(hf, hf.timestamp_ms)
            if grab_event:
                print(f"\n---> GESTURE EVENT: {grab_event.name.upper()} | State: {grab_event.state.name} <---")
                if grab_event.state.name == "START":
                    held_window = wm.get_focused_window()
                    if held_window:
                        drag_anchor = processor.to_screen_point(hf.index_tip)
                        print(f"Grabbed window: {held_window.title}")
                elif grab_event.state.name == "HOLD" and held_window and drag_anchor:
                    current_pt = processor.to_screen_point(hf.index_tip)
                    dx = int(current_pt.x - drag_anchor.x)
                    dy = int(current_pt.y - drag_anchor.y)
                    # Only move if there is a delta to avoid spamming the OS
                    if dx != 0 or dy != 0:
                        wm.move_window(held_window, dx, dy)
                        drag_anchor = current_pt
                elif grab_event.state.name == "RELEASE":
                    if held_window:
                        print(f"Released window: {held_window.title}")
                        held_window = None
                        drag_anchor = None
            
            # Optional: draw the smoothed screen point as a distinct circle on the frame
            # (Mapping back to frame coordinates to visualize the cursor position)
            h, w, _ = frame.shape
            cursor_x = int((screen_point.x / processor.screen_width) * w)
            cursor_y = int((screen_point.y / processor.screen_height) * h)
            cv2.circle(frame, (cursor_x, cursor_y), 10, (0, 255, 0), -1)

            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z) 
                for lm in hf.landmarks
            ])
            
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks_proto,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
        
        cv2.imshow("Debug Hand Tracker", frame)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

if __name__ == "__main__":
    main()
