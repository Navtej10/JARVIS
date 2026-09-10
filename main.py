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
from tracking.one_euro_filter import LandmarkFilter
from tracking.landmark_processor import LandmarkProcessor
from gestures.pinch import PinchGesture
from gestures.scroll import ScrollGesture
from gestures.point import PointGesture
from gestures.open_palm import OpenPalmGesture
from gestures.swipe import SwipeGesture
from gestures.grab import GrabGesture
from interaction.cursor import VirtualCursor
from interaction.window_manager import WindowManager
from interaction.object_manager import ObjectManager
from interaction.action_executor import ActionExecutor
from interaction.keyboard import VirtualKeyboard
from gestures.double_pinch_controller import DoublePinchAltTabController

# V5+
# from voice.speech_to_text import SpeechToText
# from voice.command_parser import clean_transcript
# from ai.intent import IntentParser
# from ai.context import PointingContext
# from ai.planner import ActionPlanner

# V6
# from tracking.depth_tracker import DepthTracker

import threading
import asyncio

# V3+ (async, run alongside the main loop)
from bridge.websocket_server import BridgeServer

class GestureArbiter:
    """Cross-gesture conflict suppression. Lives here, not inside the gesture
    classes, so each GestureStateMachine stays simple and independently
    testable — only the orchestrator needs to know these two conflict."""
    def __init__(self, conflicts: dict[str, list[str]], cooldown_ms: float = 600.0):
        self.conflicts = conflicts
        self.cooldown_ms = cooldown_ms
        self._last_fired: dict[str, float] = {}

    def allow(self, gesture_name: str, now_ms: float) -> bool:
        for other in self.conflicts.get(gesture_name, []):
            last = self._last_fired.get(other)
            if last is not None and (now_ms - last) < self.cooldown_ms:
                return False
        return True

    def record_fired(self, gesture_name: str, now_ms: float) -> None:
        self._last_fired[gesture_name] = now_ms

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
    virtual_keyboard = VirtualKeyboard()
    window_manager = WindowManager()
    object_manager = ObjectManager()
    action_executor = ActionExecutor(cursor, window_manager, object_manager)
    gesture_thresholds = settings.calibration.get("gesture_thresholds", {})
    
    double_pinch_controller = DoublePinchAltTabController(
        cursor, virtual_keyboard, 
        double_pinch_window_ms=400.0,
        drag_threshold_px=gesture_thresholds.get("drag_threshold_px", 15.0),
        pinch_max_click_duration_ms=gesture_thresholds.get("pinch_max_click_duration_ms", 500.0)
    )

    pinch = PinchGesture(
        engage_threshold=gesture_thresholds.get("pinch_engage_threshold", gesture_thresholds.get("pinch_distance_threshold", 0.20)),
        release_threshold=gesture_thresholds.get("pinch_release_threshold", 0.25),
        hold_frames_required=gesture_thresholds.get("pinch_hold_frames", 3),
        cooldown_ms=0,  # 0ms so rapid double-pinches aren't ignored by the state machine
    )
    
    scroll = ScrollGesture(
        distance_threshold=0.3,
        hold_frames_required=3,
        cooldown_ms=100
    )
    
    point = PointGesture(
        hold_frames_required=3,
        cooldown_ms=250
    )
    
    open_palm = OpenPalmGesture(
        hold_frames_required=20,
        cooldown_ms=250
    )
    
    swipe = SwipeGesture(
        velocity_threshold=settings.calibration.get("gesture_thresholds", {}).get("swipe_velocity_threshold", 0.7),
        window_ms=250.0
    )
    
    grab = GrabGesture(
        engage_threshold=0.8,
        release_threshold=1.0,
        hold_frames_required=8, # ~250ms debounce
        cooldown_ms=250
    )

    # Priority order: grab > pinch > open_palm > swipe > (others)
    bridge_server = BridgeServer(object_manager)
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
        "bridge_server": bridge_server,
        "action_executor": action_executor,
        "gestures": [grab, pinch, swipe, open_palm, scroll, point],
        "virtual_keyboard": virtual_keyboard,
        "double_pinch_controller": double_pinch_controller,
    }


def run() -> None:
    logger.info("Starting Stark Interface (target version: V%d)", VERSION)
    pipeline = build_pipeline()
    cursor = pipeline["cursor"]
    processor = pipeline["landmark_processor"]
    virtual_keyboard = pipeline["virtual_keyboard"]
    double_pinch_controller = pipeline["double_pinch_controller"]
    bridge_server = pipeline.get("bridge_server")
    bridge_loop = None
    
    if bridge_server:
        bridge_loop = asyncio.new_event_loop()
        def run_bridge():
            asyncio.set_event_loop(bridge_loop)
            bridge_loop.run_until_complete(bridge_server.start())
            
        t = threading.Thread(target=run_bridge, daemon=True)
        t.start()
        
    smoothing_config = settings.calibration.get("smoothing", {})
    use_one_euro = smoothing_config.get("use_one_euro", False)
    euro_config = smoothing_config.get("one_euro", {})
    cursor_euro = euro_config.get("cursor", {"mincutoff": 1.0, "beta": 0.7})
    gestures_euro = euro_config.get("gestures", {"mincutoff": 0.5, "beta": 0.1})
    
    cursor_filter = LandmarkFilter(num_landmarks=1, freq=30.0, mincutoff=cursor_euro["mincutoff"], beta=cursor_euro["beta"])
    gesture_filter = LandmarkFilter(num_landmarks=21, freq=30.0, mincutoff=gestures_euro["mincutoff"], beta=gestures_euro["beta"])
    
    last_scroll_y = 0
    is_scrolling = False
    is_palm_open = False
    is_grabbing = False
    
    # Drag state
    held_window = None
    held_panel = None
    pinched_panel = None
    drag_anchor = None
    palm_fired_this_hold = False
    
    # Flick state
    grab_history = deque(maxlen=5)
    flick_triggered = False
    
    # Telemetry state
    last_tracking_time = time.time()
    tracking_dropped = False

    arbiter = GestureArbiter(conflicts={"open_palm": ["swipe"], "swipe": ["open_palm"]})

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
            current_time_ms = now * 1000.0
            double_pinch_controller.tick(current_time_ms)
            
            if not hand_frames:
                if not tracking_dropped and (now - last_tracking_time) > 0.15:
                    logger.warning("[TRACKING DROPPED] Hand lost for > 150ms")
                    tracking_dropped = True
                    cursor_filter.reset()
                    gesture_filter.reset()
                continue
            
            last_tracking_time = now
            tracking_dropped = False
                
            hand = hand_frames[0]
            timestamp_sec = hand.timestamp_ms / 1000.0
            
            apply_internal_smoothing = True
            cursor_lm = hand.index_tip
            
            if use_one_euro:
                raw_lms = [(lm.x, lm.y) for lm in hand.landmarks]
                
                # Filter cursor (index tip = landmark 8)
                smoothed_cursor = cursor_filter.filter([raw_lms[8]], t=timestamp_sec)[0]
                import copy
                cursor_lm = copy.copy(hand.index_tip)
                cursor_lm.x, cursor_lm.y = smoothed_cursor
                
                # Filter all for gestures
                smoothed_all = gesture_filter.filter(raw_lms, t=timestamp_sec)
                for i, (sx, sy) in enumerate(smoothed_all):
                    hand.landmarks[i].x = sx
                    hand.landmarks[i].y = sy
                    
                apply_internal_smoothing = False
            
            # 1. Update Cursor Position
            screen_point = processor.to_screen_point(cursor_lm, apply_internal_smoothing=apply_internal_smoothing)
            
            # Allow pinch controller to lock the cursor to the pinch anchor
            effective_screen_point = double_pinch_controller.get_effective_cursor_position(screen_point)
            
            if not is_scrolling and not is_palm_open and not is_grabbing:
                cursor.move_to(effective_screen_point)
                
            # Trigger hit-testing log for the checkpoint
            pipeline["object_manager"].resolve_target(int(effective_screen_point.x), int(effective_screen_point.y))
            
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
                if event:
                        
                    if event.name == "swipe":
                        if event.state.name == "START":
                            if not arbiter.allow(event.name, hand.timestamp_ms):
                                continue
                            arbiter.record_fired(event.name, hand.timestamp_ms)
                            
                            window_manager = pipeline["window_manager"]
                            window_manager.switch_desktop(event.payload["direction"])
                            
                    elif event.name == "grab":
                        window_manager = pipeline["window_manager"]
                        if event.state.name == "START":
                            is_grabbing = True
                            target = pipeline["object_manager"].resolve_target(int(screen_point.x), int(screen_point.y))
                            
                            if target:
                                held_panel = target
                                event.target_id = held_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                                logger.info(f"Grabbed panel: {held_panel.id}")
                            else:
                                held_window = window_manager.get_focused_window()
                                if held_window:
                                    drag_anchor = processor.to_screen_point(hand.wrist)
                                    logger.info(f"Grabbed window: {held_window.title}")
                                    grab_history.clear()
                                    flick_triggered = False
                                    
                        elif event.state.name == "HOLD":
                            if held_panel:
                                event.target_id = held_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                            elif held_window:
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
                                    current_pt = processor.to_screen_point(hand.wrist)
                                    dx = int(current_pt.x - drag_anchor.x)
                                    dy = int(current_pt.y - drag_anchor.y)
                                    
                                    # Distance threshold (5px) to prevent lag from OS-level MoveWindow spam
                                    if abs(dx) > 5 or abs(dy) > 5:
                                        window_manager.move_window(held_window, dx, dy)
                                        drag_anchor = current_pt
                                        
                        elif event.state.name == "RELEASE":
                            is_grabbing = False
                            if held_panel:
                                event.target_id = held_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                                logger.info(f"Released panel: {held_panel.id}")
                                held_panel = None
                            elif held_window:
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
                            if not arbiter.allow(event.name, hand.timestamp_ms):
                                continue
                            arbiter.record_fired(event.name, hand.timestamp_ms)
                            
                            window_manager.show_desktop()
                            palm_fired_this_hold = True
                        elif event.state.name == "RELEASE":
                            logger.info("[PALM] Open palm ended, resuming cursor")
                            is_palm_open = False
                            
                    elif event.name == "pinch":
                        if event.state.name == "START":
                            target = pipeline["object_manager"].resolve_target(int(screen_point.x), int(screen_point.y))
                            if target:
                                pinched_panel = target
                                event.target_id = pinched_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                                logger.info(f"Pinched panel: {pinched_panel.id}")
                            else:
                                double_pinch_controller.handle_pinch_event(event, screen_point)
                        elif event.state.name == "HOLD":
                            if pinched_panel:
                                event.target_id = pinched_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                            else:
                                double_pinch_controller.handle_pinch_event(event, screen_point)
                        elif event.state.name == "RELEASE":
                            if pinched_panel:
                                event.target_id = pinched_panel.id
                                event.screen_point_dict = {"x": screen_point.x, "y": screen_point.y}
                                pinched_panel = None
                            else:
                                double_pinch_controller.handle_pinch_event(event, screen_point)
                            
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
                            
                    # Post-process: Broadcast the gesture event now that it might be enriched with panel info
                    if bridge_server and bridge_loop:
                        asyncio.run_coroutine_threadsafe(
                            bridge_server.broadcast_gesture_event(event), bridge_loop
                        )
                                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    finally:
        logger.info("Emergency disabling virtual cursor.")
        virtual_keyboard.force_release_all()
        cursor.set_enabled(False)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
