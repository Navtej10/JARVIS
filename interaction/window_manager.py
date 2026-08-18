"""
interaction/window_manager.py  (V2)

Small internal API for OS window/desktop control. Gesture logic should
NEVER call OS window APIs directly -- it calls these methods, so porting
to a different OS later only touches this file.

TODO(V2): implement each method using pywin32 (Windows) -- e.g.
          win32gui.SetWindowPos, win32gui.MoveWindow, virtual desktop
          switching via the undocumented IVirtualDesktopManager COM API
          (or a helper library like pyvda).
TODO(V2): add a macOS backend (Quartz / AppleScript) and a Linux backend
          (wmctrl / X11) behind the same interface, selected by platform
          at import time.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WindowHandle:
    id: int
    title: str


class WindowManager:
    def list_windows(self) -> list[WindowHandle]:
        raise NotImplementedError("TODO(V2): enumerate top-level windows")

    def get_focused_window(self) -> WindowHandle | None:
        raise NotImplementedError("TODO(V2): return the currently focused window")

    def move_window(self, window: WindowHandle, dx: int, dy: int) -> None:
        raise NotImplementedError("TODO(V2): move window by (dx, dy) pixels")

    def resize_window(self, window: WindowHandle, dw: int, dh: int) -> None:
        raise NotImplementedError("TODO(V2): resize window by (dw, dh) pixels")

    def snap_window(self, window: WindowHandle, side: str) -> None:
        """side: 'left' | 'right' | 'top' | 'maximize'"""
        raise NotImplementedError("TODO(V2): snap window to screen half/quadrant")

    def minimize(self, window: WindowHandle) -> None:
        raise NotImplementedError("TODO(V2)")

    def close(self, window: WindowHandle) -> None:
        raise NotImplementedError("TODO(V2)")

    def show_desktop(self) -> None:
        raise NotImplementedError("TODO(V2): minimize all windows")

    def switch_desktop(self, direction: str) -> None:
        """direction: 'left' | 'right'"""
        raise NotImplementedError("TODO(V2): switch virtual desktop")
