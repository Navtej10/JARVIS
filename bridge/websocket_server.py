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
        import websockets
        import asyncio
        logger.info(f"Starting BridgeServer on ws://{self.host}:{self.port}")
        async with websockets.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # run forever

    async def _handle_connection(self, websocket) -> None:
        self._connections.add(websocket)
        logger.info(f"UI client connected. Total connections: {len(self._connections)}")
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "register_object":
                        from interaction.object_manager import SpatialObject, BoundingBox
                        bounds_data = data.get("bounds", {})
                        bounds = BoundingBox(
                            x=bounds_data.get("x", 0),
                            y=bounds_data.get("y", 0),
                            width=bounds_data.get("width", 0),
                            height=bounds_data.get("height", 0)
                        )
                        obj = SpatialObject(
                            id=data["id"],
                            kind=data.get("kind", "panel"),
                            bounds=bounds,
                            z_index=data.get("z_index", 0)
                        )
                        self.object_manager.register_object(obj)
                        logger.debug(f"Registered object: {obj.id}")
                        
                    elif msg_type == "unregister_object":
                        obj_id = data.get("id")
                        if obj_id:
                            self.object_manager.unregister_object(obj_id)
                            logger.debug(f"Unregistered object: {obj_id}")
                            
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode JSON from websocket: {message}")
                except Exception as e:
                    logger.error(f"Error handling websocket message: {e}", exc_info=True)
                    
        except Exception as e:
            logger.warning(f"Connection error or closed: {e}")
        finally:
            self._connections.remove(websocket)
            logger.info(f"UI client disconnected. Total connections: {len(self._connections)}")
            # Do NOT clear object_manager on disconnect -- reconnect tolerance

    async def broadcast_gesture_event(self, event) -> None:
        if not self._connections:
            return
            
        import asyncio
        payload = {
            "type": "gesture",
            "name": event.name,
            "state": event.state.name.lower(),
            "target": getattr(event, "target_id", None),
            "screen_point": getattr(event, "screen_point_dict", None),
            "timestamp_ms": event.timestamp_ms
        }
        
        message = json.dumps(payload)
        
        # Send to all connected clients, swallow errors
        aws = [websocket.send(message) for websocket in self._connections]
        if aws:
            await asyncio.gather(*aws, return_exceptions=True)

    async def broadcast_action(self, action) -> None:
        if not self._connections:
            return
            
        import asyncio
        # Minimal V5 stub, will be expanded later
        payload = {
            "type": "action",
            "target": action.get("target"),
            "intent": action.get("intent"),
            "params": action.get("params", {})
        }
        message = json.dumps(payload)
        aws = [websocket.send(message) for websocket in self._connections]
        if aws:
            await asyncio.gather(*aws, return_exceptions=True)
