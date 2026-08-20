# JARVIS

> *Because keyboards are for people who haven't seen Iron Man.*

A gesture-controlled spatial computing interface built to answer one question: can you actually replace the mouse with your hands, on commodity hardware, no special gloves, no depth sensors? Just a webcam, Python, and way too much free time.

The short version: point your index finger to move the cursor. Pinch to click. Open your palm to show the desktop. Grab a window and drag it around. Flick your wrist to snap or minimize. Swipe to switch virtual desktops. It actually works.

---

## What it can do right now

| Gesture | What happens |
|---|---|
| **Point** (index finger out) | Moves the cursor |
| **Pinch** (thumb + index) | Left click (hold = hold, release = up) |
| **Open Palm** | Show Desktop (Win+D) |
| **Grab** (closed fist) | Grabs the focused window -- drag it anywhere |
| **Flick** (while grabbing) | Snaps left/right, maximizes up, minimizes down |
| **Swipe** | Switches virtual desktops (left/right) |
| **Two-finger Scroll** | Scrolls the page |
| **Long Fist** (~2s) | Kill switch -- toggles cursor on/off |

The grab + flick interaction is the most satisfying thing I've built so far. Grab a window with your fist, flick it to the side, and it snaps. It feels weirdly good.

---

## How it's built

```
Camera -> HandTracker -> LandmarkProcessor -> Gestures -> ActionExecutor -> OS
                                                  |
                                           (V3+) WebSocket -> React + Three.js UI
                                                  |
                                           (V5) Voice -> Intent -> Action
                                                  |
                                           (V6) Depth tracking
```

- **Tracking** -- MediaPipe Hands + OpenCV. Runs at ~30fps on a regular laptop webcam.
- **Gestures** -- Each gesture is its own state machine (START -> HOLD -> RELEASE), with configurable thresholds and cooldowns. Priority ordering means high-priority gestures (grab, pinch) block lower ones from firing.
- **Interaction** -- `VirtualCursor` wraps `pyautogui` for mouse control. `WindowManager` wraps `pywin32` for native window manipulation -- move, snap, minimize, maximize, switch desktop.
- **Config** -- Calibration is stored in `config/calibration.json`. Run `python main.py` and press `c` to re-run the calibration routine at any time.

### Project layout

```
stark-interface/
|-- main.py                  # entry point, wires everything together
|-- tracking/                # camera, hand detection, landmark math
|   |-- hand_tracker.py
|   `-- landmark_processor.py
|-- gestures/                # one file per gesture
|   |-- grab.py
|   |-- swipe.py
|   |-- open_palm.py
|   |-- pinch.py
|   |-- scroll.py
|   |-- fist.py
|   `-- ...
|-- interaction/             # OS-level actions
|   |-- cursor.py
|   |-- window_manager.py
|   `-- action_executor.py
|-- scripts/                 # debug utilities
|   |-- debug_hand_tracker.py   # shows raw gesture events in the terminal
|   `-- debug_window_manager.py
|-- config/                  # calibration + settings
|   `-- calibration.json
`-- ui/                      # React + Three.js frontend (V3+)
```

---

## Getting started

**Prerequisites:** Python 3.10+, a webcam, Windows (for the window manager; the gesture tracker itself is cross-platform).

```bash
# 1. Clone and set up Python environment
git clone https://github.com/Navtej10/JARVIS.git
cd JARVIS
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy the example config
copy config\calibration.example.json config\calibration.json

# 3. Run -- press 'c' at any time to recalibrate
python main.py

# Optional: test gestures in isolation without moving your actual cursor
python scripts/debug_hand_tracker.py
```

Once running, a small **Stark Status** window will appear. Green = active, Red = paused (kill switch is on). Press `q` to quit, `c` to recalibrate.

> **Tip:** Calibration matters a lot. Hold your index finger at the corners of your working area when prompted. If the cursor feels sluggish or jumpy, re-run calibration.

```bash
# UI (React + Three.js) -- V3+, not wired yet
cd ui
npm install
npm run dev
```

---

## Roadmap

Built in deliberate, working stages. No version N gets wired in until version N-1 is solid.

- [x] **V1** -- Cursor control (point, pinch, scroll, kill-switch fist)
- [x] **V2** -- Window management (grab, drag, flick-snap, swipe desktops, show desktop)
- [ ] **V3** -- WebSocket bridge + React/Three.js spatial overlay (floating panels, 3D objects)
- [ ] **V4** -- Two-hand gestures (scale, rotate)
- [ ] **V5** -- Voice + AI intent (speak a command, point at a target, it figures out what you mean)
- [ ] **V6** -- Depth tracking (real 3D cursor, not just 2D projection)

---

## Development notes

A few things that weren't obvious until I built them:

- **MediaPipe X is mirrored.** In a lot of webcam setups, positive X in landmark space is physical left, not right. The swipe and flick directions account for this, but if things feel backwards, check `calibration.json`.
- **The 5px drag threshold is intentional.** `MoveWindow` on Windows generates a lot of OS noise at sub-pixel deltas. The threshold keeps dragging smooth without hammering the message queue.
- **The gesture priority queue matters.** Without it, trying to grab would also trigger scroll and pinch simultaneously. Higher-priority gestures in HOLD state block everything below them.
- **The kill switch (long fist) is genuinely useful.** When you need to actually use your keyboard or mouse, you don't want the tracker to keep interfering. Two seconds of fist = cursor goes dark, hands free.

---

*Built with MediaPipe, OpenCV, pywin32, pyautogui, and a somewhat unhealthy obsession with sci-fi UIs.*
