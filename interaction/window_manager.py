"""
interaction/window_manager.py  (V2)

Small internal API for OS window/desktop control. Gesture logic should
NEVER call OS window APIs directly -- it calls these methods, so porting
to a different OS later only touches this file.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import win32gui
    import win32api
    import win32con
except ImportError:
    pass


@dataclass
class WindowHandle:
    id: int
    title: str


class WindowManager:
    def list_windows(self) -> list[WindowHandle]:
        windows = []
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append(WindowHandle(hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum_handler, None)
        return windows

    def get_focused_window(self) -> WindowHandle | None:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return WindowHandle(hwnd, win32gui.GetWindowText(hwnd))
        return None

    def move_window(self, window: WindowHandle, dx: int, dy: int) -> None:
        rect = win32gui.GetWindowRect(window.id)
        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        win32gui.MoveWindow(window.id, x + dx, y + dy, w, h, True)

    def resize_window(self, window: WindowHandle, dw: int, dh: int) -> None:
        rect = win32gui.GetWindowRect(window.id)
        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        win32gui.MoveWindow(window.id, x, y, max(1, w + dw), max(1, h + dh), True)

    def snap_window(self, window: WindowHandle, side: str) -> None:
        """side: 'left' | 'right' | 'top' | 'maximize'"""
        sw = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        sh = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        if side == 'left':
            win32gui.MoveWindow(window.id, 0, 0, sw // 2, sh, True)
        elif side == 'right':
            win32gui.MoveWindow(window.id, sw // 2, 0, sw // 2, sh, True)
        elif side == 'top':
            win32gui.MoveWindow(window.id, 0, 0, sw, sh // 2, True)
        elif side == 'maximize':
            win32gui.ShowWindow(window.id, win32con.SW_MAXIMIZE)

    def minimize(self, window: WindowHandle) -> None:
        win32gui.ShowWindow(window.id, win32con.SW_MINIMIZE)

    def close(self, window: WindowHandle) -> None:
        win32gui.PostMessage(window.id, win32con.WM_CLOSE, 0, 0)

    def show_desktop(self) -> None:
        win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
        win32api.keybd_event(ord('D'), 0, 0, 0)
        win32api.keybd_event(ord('D'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)

    def switch_desktop(self, direction: str) -> None:
        """direction: 'left' | 'right'"""
        vk_dir = win32con.VK_RIGHT if direction == 'right' else win32con.VK_LEFT
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        win32api.keybd_event(win32con.VK_LWIN, 0, 0, 0)
        win32api.keybd_event(vk_dir, 0, 0, 0)
        win32api.keybd_event(vk_dir, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_LWIN, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
