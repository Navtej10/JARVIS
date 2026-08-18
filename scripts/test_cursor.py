import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tracking.landmark_processor import ScreenPoint
from interaction.cursor import VirtualCursor

def main():
    print("Testing VirtualCursor in isolation...")
    print("WARNING: Hands off the mouse! The cursor will move on its own.")
    
    cursor = VirtualCursor()
    if sys.platform == "win32":
        print("Using Win32 SendInput paths.")
    else:
        print("Using PyAutoGUI fallback.")
        
    time.sleep(2)
    
    # Define a 100x100 square path starting from (500, 500)
    points = [
        ScreenPoint(500, 500),
        ScreenPoint(600, 500),
        ScreenPoint(600, 600),
        ScreenPoint(500, 600),
        ScreenPoint(500, 500)
    ]
    
    print("Tracing a square...")
    for p in points:
        cursor.move_to(p)
        time.sleep(0.5)
        
    print("Dispatching a click at (500, 500)...")
    cursor.click()
    
    print("Done! You should have seen the cursor move in a square and click.")

if __name__ == "__main__":
    main()
