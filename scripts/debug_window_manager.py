import sys
import os

# Add parent directory to path so we can import interaction
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interaction.window_manager import WindowManager, WindowHandle

def main():
    wm = WindowManager()
    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
            
            action = cmd[0].lower()
            args = cmd[1:]

            if action == "list":
                windows = wm.list_windows()
                for w in windows:
                    print(f"[{w.id}] {w.title}")
            
            elif action == "focus":
                w = wm.get_focused_window()
                if w:
                    print(f"Focused: [{w.id}] {w.title}")
                else:
                    print("No focused window.")
            
            elif action == "move":
                if len(args) != 2:
                    print("Usage: move <dx> <dy>")
                    continue
                dx, dy = int(args[0]), int(args[1])
                w = wm.get_focused_window()
                if w:
                    wm.move_window(w, dx, dy)
                    print(f"Moved {w.title} by {dx}, {dy}")
                else:
                    print("No focused window to move.")
            
            elif action == "resize":
                if len(args) != 2:
                    print("Usage: resize <dw> <dh>")
                    continue
                dw, dh = int(args[0]), int(args[1])
                w = wm.get_focused_window()
                if w:
                    wm.resize_window(w, dw, dh)
                    print(f"Resized {w.title} by {dw}, {dh}")
                else:
                    print("No focused window to resize.")
            
            elif action == "snap":
                if len(args) != 1 or args[0] not in ["left", "right", "top", "maximize"]:
                    print("Usage: snap <left|right|top|maximize>")
                    continue
                side = args[0]
                w = wm.get_focused_window()
                if w:
                    wm.snap_window(w, side)
                    print(f"Snapped {w.title} to {side}")
                else:
                    print("No focused window to snap.")
            
            elif action == "minimize":
                w = wm.get_focused_window()
                if w:
                    wm.minimize(w)
                    print(f"Minimized {w.title}")
                else:
                    print("No focused window to minimize.")
            
            elif action == "close":
                w = wm.get_focused_window()
                if w:
                    wm.close(w)
                    print(f"Closed {w.title}")
                else:
                    print("No focused window to close.")
            
            elif action == "desktop":
                wm.show_desktop()
                print("Showed desktop")
            
            elif action == "switchleft":
                wm.switch_desktop("left")
                print("Switched desktop left")
                
            elif action == "switchright":
                wm.switch_desktop("right")
                print("Switched desktop right")
                
            elif action == "exit" or action == "quit":
                break
                
            else:
                print(f"Unknown command: {action}")
                
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
