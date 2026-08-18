"""
bridge/websocket_server.py  (V3+)

Clean, language-agnostic contract between the Python CV/gesture/AI engine
and the React + Three.js spatial UI. This is what keeps the two halves of
the system independently replaceable -- the UI never needs to know
MediaPipe exists, and the Python side never needs to know React exists;
they only need to agree on this message schema.

Message schema (JSON over WebSocket):

    Python -> UI (gesture/state events):
        {
          "type": "gesture",
          "name": "pinch",
          "state": "start" | "hold" | "release",
          "target": "<object_id or null>",
          "screen_point": {"x": int, "y": int},
          "timestamp_ms": int
        }

    Python -> UI (AI-planned actions, V5+):
        {
          "type": "action",
          "target": "<object_id>",
          "intent": "move" | "resize" | "select" | ...,
          "params": {...}
        }

    UI -> Python (object registration, V3+):
        {
          "type": "register_object",
          "id": "<object_id>",
          "kind": "panel" | "widget" | "3d_object",
          "bounds": {"x": int, "y": int, "width": int, "height": int},
          "z_index": int
        }

    UI -> Python (object removed, V3+):
        {"type": "unregister_object", "id": "<object_id>"}

TODO(V3): implement the websockets server, one connection expected (the
          local Electron/browser UI process).
TODO(V3): route incoming "register_object"/"unregister_object" messages to
          interaction.object_manager.ObjectManager.
TODO(V3): implement broadcast_gesture_event() called from main.py's
          pipeline loop whenever a GestureEvent fires.
TODO(V5): implement broadcast_action() for AI-planned actions, so the UI
          can show a confirmation state before/while an action executes.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger("stark.bridge")


class BridgeServer:
    def __init__(self, object_manager, host: str = "localhost", port: int = 8765):
        self.object_manager = object_manager
        self.host = host
        self.port = port
        self._connections = set()

    async def start(self) -> None:
        raise NotImplementedError("TODO(V3): start websockets.serve(self._handle_connection, host, port)")

    async def _handle_connection(self, websocket) -> None:
        raise NotImplementedError(
            "TODO(V3): register connection, loop over incoming messages, dispatch "
            "by 'type' field (register_object / unregister_object) to self.object_manager"
        )

    async def broadcast_gesture_event(self, event) -> None:
        raise NotImplementedError("TODO(V3): serialize GestureEvent per the schema above and send to all connections")

    async def broadcast_action(self, action) -> None:
        raise NotImplementedError("TODO(V5): serialize Action per the schema above and send to all connections")
