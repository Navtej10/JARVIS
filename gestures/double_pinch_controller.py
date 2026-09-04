"""
Orchestrates double-pinch -> Alt-Tab on top of the EXISTING PinchGesture
events. This is not a new GestureStateMachine -- it's a look-back
consumer of PinchGesture's own START/HOLD/RELEASE events, so no new
finger-shape detection is added at all.

Key design decision: detection is retrospective (was the PREVIOUS pinch's
RELEASE recent?), not anticipatory (wait to see if ANOTHER pinch comes).
Retrospective means a normal single pinch is dispatched immediately with
zero added latency -- only a pinch that arrives suspiciously soon after
the last one gets rerouted into Alt-Tab instead of a click/drag.
"""
from __future__ import annotations

from gestures.gesture_state_machine import GestureEvent, GestureState
from interaction.cursor import VirtualCursor
from interaction.keyboard import VirtualKeyboard
import math
from tracking.landmark_processor import ScreenPoint


class DoublePinchAltTabController:
    def __init__(
        self,
        cursor: VirtualCursor,
        virtual_keyboard: VirtualKeyboard,
        double_pinch_window_ms: float = 200.0,
        px_per_tab_step: float = 60.0,
        hold_timeout_ms: float = 5000.0,
        drag_threshold_px: float = 15.0,
        pinch_max_click_duration_ms: float = 500.0,
    ):
        self.cursor = cursor
        self.virtual_keyboard = virtual_keyboard
        self.double_pinch_window_ms = double_pinch_window_ms
        self.px_per_tab_step = px_per_tab_step
        self.hold_timeout_ms = hold_timeout_ms
        self.drag_threshold_px = drag_threshold_px
        self.pinch_max_click_duration_ms = pinch_max_click_duration_ms

        self._last_release_ms: float | None = None
        self._alt_tab_active = False
        self._anchor_x: float | None = None
        self._alt_tab_started_ms: float | None = None
        
        self.pinch_active = False
        self.drag_active = False
        self.pinch_anchor_position: ScreenPoint | None = None
        self.pinch_start_time_ms: float | None = None

    def get_effective_cursor_position(self, current_point: ScreenPoint) -> ScreenPoint:
        if self.pinch_active and not self.drag_active and self.pinch_anchor_position is not None:
            return self.pinch_anchor_position
        return current_point

    def handle_pinch_event(self, event: GestureEvent, screen_point) -> None:
        if event.state == GestureState.START:
            if (
                not self._alt_tab_active
                and self._last_release_ms is not None
                and (event.timestamp_ms - self._last_release_ms) <= self.double_pinch_window_ms
            ):
                # Second pinch arrived quickly -> reroute to Alt-Tab, skip
                # mouse_down() entirely so no real click/drag is generated.
                self._alt_tab_active = True
                self._anchor_x = screen_point.x
                self._alt_tab_started_ms = event.timestamp_ms
                self.virtual_keyboard.start_alt_tab_cycle()
                self._last_release_ms = None
            else:
                # Normal pinch start -> Lock cursor, prepare for click or drag
                self.pinch_active = True
                self.drag_active = False
                self.pinch_anchor_position = screen_point
                self.pinch_start_time_ms = event.timestamp_ms

        elif event.state == GestureState.HOLD:
            if self._alt_tab_active:
                assert self._anchor_x is not None
                delta = screen_point.x - self._anchor_x
                if abs(delta) > self.px_per_tab_step:
                    self.virtual_keyboard.tab(forward=(delta > 0))
                    self._anchor_x = screen_point.x  # incremental, like grab-drag
            elif self.pinch_active and not self.drag_active:
                # Check for drag threshold or click duration timeout
                assert self.pinch_anchor_position is not None
                assert self.pinch_start_time_ms is not None
                
                dx = screen_point.x - self.pinch_anchor_position.x
                dy = screen_point.y - self.pinch_anchor_position.y
                distance = math.hypot(dx, dy)
                
                duration = event.timestamp_ms - self.pinch_start_time_ms
                
                if distance > self.drag_threshold_px or duration > self.pinch_max_click_duration_ms:
                    self.drag_active = True
                    self.cursor.move_to(self.pinch_anchor_position)
                    self.cursor.mouse_down()

        elif event.state == GestureState.RELEASE:
            if self._alt_tab_active:
                self.virtual_keyboard.commit_alt_tab_cycle()
                self._alt_tab_active = False
                self._anchor_x = None
                self._alt_tab_started_ms = None
                self._last_release_ms = None  # avoid chaining into a spurious third-pinch match
            else:
                if self.pinch_active:
                    if self.drag_active:
                        self.cursor.mouse_up()
                    else:
                        # Brief pinch without much movement -> Click at anchor
                        self.cursor.move_to(self.pinch_anchor_position)
                        self.cursor.click()
                        
                    self.pinch_active = False
                    self.drag_active = False
                    self.pinch_anchor_position = None
                    self.pinch_start_time_ms = None
                    
                self._last_release_ms = event.timestamp_ms

    def tick(self, now_ms: float) -> None:
        """Call every frame regardless of gesture events. Safety net: if
        tracking is lost mid-cycle (hand leaves frame) and RELEASE never
        arrives, force-release Alt after hold_timeout_ms rather than
        leaving it stuck system-wide."""
        if self._alt_tab_active and self._alt_tab_started_ms is not None:
            if (now_ms - self._alt_tab_started_ms) > self.hold_timeout_ms:
                self.virtual_keyboard.force_release_all()
                self._alt_tab_active = False
                self._anchor_x = None
                self._alt_tab_started_ms = None
                
        if self.pinch_active and self.pinch_start_time_ms is not None:
            if (now_ms - self.pinch_start_time_ms) > self.hold_timeout_ms:
                if self.drag_active:
                    self.cursor.mouse_up()
                self.pinch_active = False
                self.drag_active = False
                self.pinch_anchor_position = None
                self.pinch_start_time_ms = None
