# JARVIS

A gesture- and voice-controlled spatial computing interface — think Iron Man's holographic UI, but running on a webcam and a laptop.

The idea is to replace the mouse and keyboard with natural hand gestures, voice commands, and AI-driven intent, layered on top of a 3D spatial overlay rendered in the browser. Tracking happens in Python (MediaPipe + OpenCV), and a WebSocket bridge connects it to a React + Three.js frontend that renders floating panels and interactive 3D objects in real time.

## Getting started

```bash
# Python backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# UI (React + Three.js)
cd ui
npm install
npm run dev
```
