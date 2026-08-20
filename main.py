"""
main.py

Entry point that wires the pipeline together. Which pieces are active
depends on which version you're currently building -- see the VERSION
constant below and the comments in run().

Camera -> HandTracker -> LandmarkProcessor -> Gestures -> ActionExecutor -> OS/UI
                                                    |
                                        (V3+) ObjectManager + BridgeServer
                                                    |
                                        (V5) SpeechToText + IntentParser + ActionPlanner
                                                    |
                                        (V6) DepthTracker

Don't wire in a version's modules before that version's predecessor is
solid -- see README.md's development philosophy.
"""
from __future__ import annotations

import logging
import cv2
import time
import numpy as np
from collections import deque

from config.settings import settings
from tracking.hand_tracker import HandTracker
from tracking.landmark_processor import LandmarkProcessor
from gestures.pinch import PinchGesture
from gestures.scroll import ScrollGesture
from gestures.fist import FistGesture
from gestures.point import PointGesture
from gestures.open_palm import OpenPalmGesture
from gestures.swipe import SwipeGesture
from gestures.grab import GrabGesture
from interaction.cursor import VirtualCursor
from interaction.window_manager import WindowManager
from interaction.object_manager import ObjectManager
from interaction.action_executor import ActionExecutor

# V5+
# from voice.speech_to_text import SpeechToText
# from voice.command_parser import clean_transcript
# from ai.intent import IntentParser
# from ai.context import PointingContext
# from ai.planner import ActionPlanner

# V6
# from tracking.depth_tracker import DepthTracker

# V3+ (async, run alongside the main loop)
# from bridge.websocket_server import BridgeServer

VERSION = 1  # bump as you progress through the roadmap; gates which modules get wired in below

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("stark.main")


def build_pipeline():
    """Construct the object graph for the currently-targeted version."""
    hand_tracker = HandTracker(camera_index=settings.camera_index, max_hands=1 if VERSION < 4 else 2)
    landmark_processor = LandmarkProcessor(
        calibration=settings.calibration,
        screen_width=settings.calibration.get("screen", {}).get("width", 1920),
        screen_height=settings.calibration.get("screen", {}).get("height", 1080),
    )
    cursor = VirtualCursor()
    window_manager = WindowManager()
    object_manager = ObjectManager()
    action_executor = ActionExecutor(cursor, window_manager, object_manager)

    pinch = PinchGesture(
        distance_threshold=settings.calibration.get("gesture_thresholds", {}).get("pinch_distance_threshold", 0.20),
        hold_frames_required=settings.calibration.get("gesture_thresholds", {}).get("pinch_hold_frames", 3),
        cooldown_ms=settings.calibration.get("gesture_thresholds", {}).get("gesture_cooldown_ms", 250),
    )
    
    scroll = ScrollGesture(
        distance_threshold=0.3,
        hold_frames_required=3,
        cooldown_ms=100
    )
    
    fist = FistGesture(
        distance_threshold=0.8,
        hold_frames_required=60, # ~2 seconds at 30 fps
        cooldown_ms=1000
    )
    
    point = PointGesture(
        hold_frames_required=3,
        cooldown_ms=250
    )
    
    open_palm = OpenPalmGesture(
        hold_frames_required=6,
        cooldown_ms=250
    )
    
    swipe = SwipeGesture(
        velocity_threshold=settings.calibration.get("gesture_thresholds", {}).get("swipe_velocity_threshold", 0.8)
    )
    
    grab = GrabGesture()

    # Priority order: grab > pinch > open_palm > swipe > (others)
    # TODO(V3): construct BridgeServer(object_manager) and run it on an asyncio task
    #           alongside the synchronous tracking loop (e.g. via a thread or asyncio.run
    #           in a background thread).
    # TODO(V4): add TwoHandScaleGesture, RotateGesture (requires max_hands=2 above).
    # TODO(V5): construct SpeechToText, IntentParser(settings.anthropic_api_key),
    #           PointingContext, ActionPlanner(action_executor); wire push-to-talk
    #           to trigger the voice -> intent -> action flow.
    # TODO(V6): construct DepthTracker(settings.calibration["depth"]) and feed its
    #           readings into landmark_processor / gesture modifiers.

    return {
        "hand_tracker": hand_tracker,
        "landmark_processor": landmark_processor,
        "cursor": cursor,
        "window_manager": window_manager,
        "object_manager": object_manager,
        "action_executor": action_executor,
        "gestures": [grab, pinch, open_palm, swipe, scroll, fist, point],
    }


def run() -> None:
    logger.info("Starting Stark Interface (target version: V%d)", VERSION)
    pipeline = build_pipeline()
    cursor = pipeline["cursor"]
    processor = pipeline["landmark_processor"]
    
    last_scroll_y = 0
    is_scrolling = False
    is_palm_open = False
    
    # Drag state
    held_window = None
    drag_anchor = None
    palm_fired_this_hold = False
    
    # Flick state
    grab_history = deque(maxlen=5)
    flick_triggered = False
    
    # Telemetry state
    last_tracking_time = time.time()
    tracking_dropped = False

    cv2.namedWindow("Stark Status", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Stark Status", 400, 150)

    try:
        for hand_frames in pipeline["hand_tracker"].stream():
            
            # --- Status Window & Recalibration ---
            # Create a blank black image for the status window
            status_img = np.zeros((150, 400, 3), dtype=np.uint8)
            
            if cursor.enabled:
                cv2.putText(status_img, "ACTIVE", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(status_img, "PAUSED (Kill Switch)", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
            cv2.putText(status_img, "Press 'c' to recalibrate", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
            cv2.putText(status_img, "Press 'q' to quit", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
            
            cv2.imshow("Stark Status", status_img)
            key = cv2.waitKey(1)
            
            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord('c'):
                logger.info("Manual recalibration triggered.")
                cursor.set_enabled(False)
                # Hide the status window so it doesn't block calibration
                cv2.destroyWindow("Stark Status")
                pipeline["landmark_processor"].run_calibration_routine(pipeline["hand_tracker"])
                # Re-create the status window
                cv2.namedWindow("Stark Status", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Stark Status", 400, 150)
                cursor.set_enabled(True)
                continue
                
            # --- Telemetry: Dropped Tracking ---
            now = time.time()
            if not hand_frames:
                if not tracking_dropped and (now - last_tracking_time) > 0.15:
                    logger.warning("[TRACKING DROPPED] Hand lost for > 150ms")
                    tracking_dropped = True
                continue
            
            last_tracking_time = now
            tracking_dropped = False
                
            hand = hand_frames[0]
            
            # 1. Update Cursor Position
            screen_point = processor.to_screen_point(hand.index_tip)
            if not is_scrolling and not is_palm_open:
                cursor.move_to(screen_point)
            
            # 2. Process Gestures
            higher_priority_held = False
            for gesture in pipeline["gestures"]:
                if higher_priority_held:
                    continue
                    
                event = gesture.update(hand, hand.timestamp_ms)
                
                # Check if this gesture is currently holding to skip lower-priority ones
                if gesture._state.name == "HOLD":
                    higher_priority_held = True
                    
                if event:
                    if event.name == "swipe":
                        if event.state.name == "START":
                            window_manager = pipeline["window_manager"]
                            window_manager.switch_desktop(event.payload["direction"])
                            
                    elif event.name == "grab":
                        window_manager = pipeline["window_manager"]
                        if event.state.name == "START":
                            held_window = window_manager.get_focused_window()
                            if held_window:
                                drag_anchor = processor.to_screen_point(hand.index_tip)
                                logger.info(f"Grabbed window: {held_window.title}")
                                grab_history.clear()
                                flick_triggered = False
                        elif event.state.name == "HOLD" and held_window:
                            # 1. Flick Detection
                            if not flick_triggered:
                                grab_history.append((hand.wrist.x, hand.wrist.y, hand.timestamp_ms))
                                if len(grab_history) == grab_history.maxlen:
                                    dt = (grab_history[-1][2] - grab_history[0][2]) / 1000.0
                                    if dt > 0:
                                        vx = (grab_history[-1][0] - grab_history[0][0]) / dt
                                        vy = (grab_history[-1][1] - grab_history[0][1]) / dt
                                        
                                        if abs(vx) > 0.8 or abs(vy) > 0.8:
                                            logger.info(f"Flick detected! vx={vx:.2f}, vy={vy:.2f}")
                                            flick_triggered = True
                                            drag_anchor = None  # Stop dragging after a flick
                                            
                                            if abs(vx) > abs(vy):
                                                # MediaPipe X is mirrored by default in many setups, so vx > 0 is often physical Left.
                                                # If it feels backwards, we can swap these.
                                                if vx < 0:
                                                    logger.info("Flick Right -> Snap Right")
                                                    window_manager.snap_window(held_window, 'right')
                                                else:
                                                    logger.info("Flick Left -> Snap Left")
                                                    window_manager.snap_window(held_window, 'left')
                                            else:
                                                if vy < 0: # Y decreases upwards
                                                    logger.info("Flick Up -> Maximize")
                                                    window_manager.snap_window(held_window, 'maximize')
                                                else:
                                                    logger.info("Flick Down -> Minimize")
                                                    window_manager.minimize(held_window)
                                            continue
                            
                            # 2. Drag Logic
                            if drag_anchor:
                                current_pt = processor.to_screen_point(hand.index_tip)
                                dx = int(current_pt.x - drag_anchor.x)
                                dy = int(current_pt.y - drag_anchor.y)
                                
                                # Distance threshold (5px) to prevent lag from OS-level MoveWindow spam
                                if abs(dx) > 5 or abs(dy) > 5:
                                    window_manager.move_window(held_window, dx, dy)
                                    drag_anchor = current_pt
                        elif event.state.name == "RELEASE":
                            if held_window:
                                logger.info(f"Released window: {held_window.title}")
                                held_window = None
                                drag_anchor = None
                                flick_triggered = False
                                
                    elif event.name == "open_palm":
                        window_manager = pipeline["window_manager"]
                        if event.state.name == "START":
                            palm_fired_this_hold = False
                            logger.info("[PALM] Open palm started, pausing cursor")
                            is_palm_open = True
                        elif event.state.name == "HOLD" and not palm_fired_this_hold:
                            window_manager.show_desktop()
                            palm_fired_this_hold = True
                        elif event.state.name == "RELEASE":
                            logger.info("[PALM] Open palm ended, resuming cursor")
                            is_palm_open = False
                            
                    elif event.name == "fist":
                        if event.state.name == "START":
                            cursor.set_enabled(not cursor.enabled)
                            logger.info("Kill Switch Toggled. Cursor Enabled: %s", cursor.enabled)
                            
                    elif event.name == "pinch":
                        if event.state.name == "START":
                            logger.info("[CLICK EVENT] Pinch START at (%d, %d)", screen_point.x, screen_point.y)
                            cursor.mouse_down()
                        elif event.state.name == "RELEASE":
                            cursor.mouse_up()
                            
                    elif event.name == "scroll":
                        if event.state.name == "START":
                            last_scroll_y = screen_point.y
                            is_scrolling = True
                        elif event.state.name == "HOLD":
                            delta_y = last_scroll_y - screen_point.y
                            if abs(delta_y) > 0:
                                cursor.scroll(delta_y * 2)
                                last_scroll_y = screen_point.y
                        elif event.state.name == "RELEASE":
                            is_scrolling = False
                                
                    elif event.name == "point":
                        if event.state.name == "START":
                            logger.info("[POINT] Pointing started")
                        elif event.state.name == "RELEASE":
                            logger.info("[POINT] Pointing ended")
                                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    finally:
        logger.info("Emergency disabling virtual cursor.")
        cursor.set_enabled(False)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
