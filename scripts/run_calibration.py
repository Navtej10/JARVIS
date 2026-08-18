import os
import sys
import json

# Add parent directory to path to allow importing from tracking
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tracking.hand_tracker import HandTracker
from tracking.landmark_processor import LandmarkProcessor

def load_calibration():
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
    calib_file = os.path.join(config_dir, 'calibration.json')
    example_file = os.path.join(config_dir, 'calibration.example.json')
    
    if os.path.exists(calib_file):
        with open(calib_file, 'r') as f:
            return json.load(f)
            
    with open(example_file, 'r') as f:
        return json.load(f)

def main():
    print("Loading calibration configuration...")
    calib_data = load_calibration()
    
    # Read screen config or fallback
    screen_width = calib_data.get("screen", {}).get("width", 1920)
    screen_height = calib_data.get("screen", {}).get("height", 1080)
    
    print("Starting hand tracker...")
    tracker = HandTracker(camera_index=calib_data.get("camera", {}).get("index", 0), max_hands=1)
    processor = LandmarkProcessor(calibration=calib_data, screen_width=screen_width, screen_height=screen_height)
    
    print("\nStarting calibration routine...")
    print("Please stand where you intend to use the interface.")
    print("Point steadily at each red dot until it flashes green.")
    
    # Run calibration
    new_calibration = processor.run_calibration_routine(tracker)
    
    print("\nCalibration routine finished!")
    print("You can now run 'python scripts/debug_hand_tracker.py' to test the mapped tracking.")

if __name__ == "__main__":
    main()
