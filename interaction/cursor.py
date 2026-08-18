"""
interaction/cursor.py  (V1)

Translates a ScreenPoint (from landmark_processor) + gesture events
(from pinch.py) into actual OS mouse input. This is the ONLY module that
should call PyAutoGUI / Win32 SendInput directly -- keeping it isolated is
what lets you port to macOS/Linux later without touching gesture logic.

TODO(V1): implement move_to() using Win32 SendInput (preferred, lower latency)
          with PyAutoGUI as a cross-platform fallback.
TODO(V1): implement click(), mouse_down()/mouse_up() for drag support.
TODO(V1): implement scroll() for the two-finger scroll gesture.
TODO(V1): implement a kill switch -- e.g. `enabled` flag toggled by a
          dedicated gesture or hotkey, that disables all dispatch below.
"""
from __future__ import annotations

import sys
from tracking.landmark_processor import ScreenPoint

# --- Windows Setup ---
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    # Win32 Consts
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_ABSOLUTE = 0x8000
    
    # C struct definitions
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (("dx",          wintypes.LONG),
                    ("dy",          wintypes.LONG),
                    ("mouseData",   wintypes.DWORD),
                    ("dwFlags",     wintypes.DWORD),
                    ("time",        wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)))

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = (("mi", MOUSEINPUT),)
        _anonymous_ = ("_input",)
        _fields_ = (("type",   wintypes.DWORD),
                    ("_input", _INPUT))
                    
    INPUT_MOUSE = 0
else:
    import pyautogui
    # PyAutoGUI has a built in fail-safe that we want to avoid for cursor tracking
    pyautogui.FAILSAFE = False

class VirtualCursor:
    def __init__(self):
        self.enabled = True
        
        if sys.platform == "win32":
            self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)

    def _send_input(self, dx: int, dy: int, mouseData: int, dwFlags: int):
        if not self.enabled: return
        if sys.platform == "win32":
            # Using c_long handles large 32-bit unsigned constants correctly when passed to DWORD
            x = INPUT(type=INPUT_MOUSE,
                      mi=MOUSEINPUT(dx=dx, dy=dy, mouseData=mouseData,
                                    dwFlags=dwFlags, time=0, dwExtraInfo=None))
            ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def move_to(self, point: ScreenPoint) -> None:
        if not self.enabled: return
        
        if sys.platform == "win32":
            # Absolute coords in Win32 range from 0 to 65535 across primary monitor
            w = max(1, self.screen_width)
            h = max(1, self.screen_height)
            
            # Map pixel coordinates to absolute input coordinates
            abs_x = int((point.x * 65535) / w)
            abs_y = int((point.y * 65535) / h)
            
            # Clamp to max 65535
            abs_x = max(0, min(65535, abs_x))
            abs_y = max(0, min(65535, abs_y))
            
            self._send_input(abs_x, abs_y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)
        else:
            pyautogui.moveTo(point.x, point.y, _pause=False)

    def click(self) -> None:
        if not self.enabled: return
        if sys.platform == "win32":
            self._send_input(0, 0, 0, MOUSEEVENTF_LEFTDOWN)
            self._send_input(0, 0, 0, MOUSEEVENTF_LEFTUP)
        else:
            pyautogui.click()

    def mouse_down(self) -> None:
        if not self.enabled: return
        if sys.platform == "win32":
            self._send_input(0, 0, 0, MOUSEEVENTF_LEFTDOWN)
        else:
            pyautogui.mouseDown()

    def mouse_up(self) -> None:
        if not self.enabled: return
        if sys.platform == "win32":
            self._send_input(0, 0, 0, MOUSEEVENTF_LEFTUP)
        else:
            pyautogui.mouseUp()

    def scroll(self, delta_y: int) -> None:
        if not self.enabled: return
        if sys.platform == "win32":
            # In Windows, positive wheel data scrolls up, negative scrolls down.
            # 120 is one standard click (WHEEL_DELTA).
            self._send_input(0, 0, delta_y, MOUSEEVENTF_WHEEL)
        else:
            pyautogui.scroll(delta_y)

    def set_enabled(self, enabled: bool) -> None:
        """Kill switch: call with False to instantly fall back to the physical mouse."""
        self.enabled = enabled
