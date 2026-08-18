# Stark Interface

A gesture- and voice-controlled spatial computing interface, built incrementally.

This scaffold implements the module boundaries for **V1 through V6** of the roadmap:

| Version | What it adds | Primary modules |
|---|---|---|
| V1 | Hand-controlled mouse | `tracking/`, `interaction/cursor.py` |
| V2 | Gesture-controlled desktop | `gestures/`, `interaction/window_manager.py` |
| V3 | Spatial UI / floating panels | `interaction/object_manager.py`, `bridge/`, `ui/` |
| V4 | 3D object manipulation | `ui/src/three/`, `gestures/rotate.py` |
| V5 | Voice + gesture + AI intent | `voice/`, `ai/` |
| V6 | Depth-aware interaction | `tracking/depth_tracker.py` |

V7 (AR/holographic hardware) is intentionally out of scope for this scaffold — it's a
hardware/SDK integration effort that builds on everything here rather than new
software architecture.

## Getting started

```bash
# Python side (tracking, gestures, interaction, voice, ai, bridge)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py

# UI side (V3+, React + Three.js spatial overlay)
cd ui
npm install
npm run dev
```

## Project layout

```
stark-interface/
├── tracking/          # Camera -> hand landmarks -> depth (V1, V6)
├── gestures/           # Landmarks -> classified gesture events (V1, V2, V4)
├── interaction/         # Gesture events -> cursor/window/object actions (V1-V4)
├── voice/                # Microphone -> text (V5)
├── ai/                   # Text + pointing target -> structured intent (V5)
├── bridge/               # Python <-> React WebSocket contract (V3+)
├── ui/                    # React + TypeScript + Three.js spatial overlay (V3+)
├── config/                # Calibration and user settings
├── tests/                 # Unit tests per module
└── main.py                # Entry point / pipeline wiring
```

## Development philosophy

- Don't build ahead of the current version. Each module has `TODO(Vn)` markers
  showing what belongs to which version — resist filling in V5 code while V2 is
  still shaky.
- Every module is independently replaceable. `tracking/hand_tracker.py` should be
  swappable for a different tracker without touching `gestures/` or `interaction/`.
- Keep the physical mouse/keyboard as a working fallback at every stage.

See the full roadmap doc for gesture tables, success criteria, and rationale
behind each design decision.
