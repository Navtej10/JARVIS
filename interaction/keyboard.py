"""
Low-level keyboard event dispatch. Uses raw key events (not posted window
messages) since Windows' Alt-Tab switcher reads physical key state directly.
"""
import ctypes

VK_MENU = 0x12
VK_TAB = 0x09
VK_SHIFT = 0x10
KEYEVENTF_KEYUP = 0x0002


def _key_event(vk_code: int, key_up: bool = False) -> None:
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP if key_up else 0, 0)


class VirtualKeyboard:
    def __init__(self):
        self._alt_held = False

    def start_alt_tab_cycle(self) -> None:
        if not self._alt_held:
            _key_event(VK_MENU, key_up=False)
            self._alt_held = True
        self.tab(forward=True)

    def tab(self, forward: bool) -> None:
        if not self._alt_held:
            return
        if not forward:
            _key_event(VK_SHIFT, key_up=False)
        _key_event(VK_TAB, key_up=False)
        _key_event(VK_TAB, key_up=True)
        if not forward:
            _key_event(VK_SHIFT, key_up=True)

    def commit_alt_tab_cycle(self) -> None:
        if self._alt_held:
            _key_event(VK_MENU, key_up=True)
            self._alt_held = False

    def force_release_all(self) -> None:
        if self._alt_held:
            _key_event(VK_MENU, key_up=True)
            self._alt_held = False
