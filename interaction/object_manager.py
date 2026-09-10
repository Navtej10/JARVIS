"""
interaction/object_manager.py  (V3)

This is the module that implements the key V3 architectural shift:
moving from raw coordinates ("cursor = (642, 381)") to semantic objects
("user is pointing at ProjectPanel").

Spatial UI panels (rendered in ui/, React + Three.js) register their
screen-space bounding regions here. Gesture events are resolved against
these registered objects via hit-testing, with a z-order/focus model so
only the top-most panel under the hand responds to a gesture -- exactly
like window focus in a normal OS.

TODO(V3): implement register_object() / unregister_object(), called by the
          UI layer over the bridge (see bridge/websocket_server.py) whenever
          a panel mounts/unmounts/moves.
TODO(V3): implement hit_test() with z-order (topmost registered object wins).
TODO(V3): implement resolve_target(), the main entry point gestures call
          into: given a ScreenPoint, return the focused SpatialObject or None.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


@dataclass
class SpatialObject:
    id: str
    kind: str          # e.g. "panel", "widget", "3d_object" (V4)
    bounds: BoundingBox
    z_index: int = 0


class ObjectManager:
    def __init__(self):
        self._objects: dict[str, SpatialObject] = {}

    def register_object(self, obj: SpatialObject) -> None:
        self._objects[obj.id] = obj

    def unregister_object(self, object_id: str) -> None:
        self._objects.pop(object_id, None)

    def hit_test(self, x: int, y: int) -> SpatialObject | None:
        topmost = None
        for obj in self._objects.values():
            if obj.bounds.contains(x, y):
                if topmost is None or obj.z_index > topmost.z_index:
                    topmost = obj
        return topmost

    def resolve_target(self, x: int, y: int) -> SpatialObject | None:
        """Main entry point: gestures call this to find what the hand is pointing at."""
        return self.hit_test(x, y)
