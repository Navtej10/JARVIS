"""
ai/context.py  (V5)

Deixis resolution: turning "this" / "that" / "it" in a voice command into
a concrete target object, using the currently pointed-at SpatialObject
(from interaction/object_manager.py) or focused window as grounding.

This is called out explicitly in the roadmap as the single most important
design decision in V5 -- it's what makes the system feel like it
understands intent rather than being a voice command list. Get this
wrong and every voice command needs the object named explicitly, which
defeats the point of combining gesture + voice.

TODO(V5): implement PointingContext.current_target(), populated continuously
          from the gesture/object_manager pipeline (whatever the hand is
          pointing at right now, or was pointing at in the last N ms).
TODO(V5): implement resolve_deixis(), which the AI Intent Parser prompt
          uses to substitute "this"/"that" with a concrete object id/title
          before (or as part of) constructing the LLM prompt.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class PointingContext:
    """Rolling record of what the hand is currently/recently pointing at."""
    target_id: str | None = None
    target_kind: str | None = None   # "window", "panel", "3d_object"
    updated_at_ms: float = 0.0
    grace_period_ms: float = 1500.0  # how long a pointed-at target stays "current" after hand moves away

    def update(self, target_id: str | None, target_kind: str | None) -> None:
        raise NotImplementedError(
            "TODO(V5): update target_id/target_kind + updated_at_ms; called every "
            "frame from the interaction layer with the current object_manager.resolve_target() result"
        )

    def current_target(self) -> str | None:
        """Return the target id if it's still within the grace period, else None."""
        raise NotImplementedError(
            "TODO(V5): return self.target_id if (now - self.updated_at_ms) < self.grace_period_ms else None"
        )
