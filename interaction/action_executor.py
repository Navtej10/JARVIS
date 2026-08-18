"""
interaction/action_executor.py  (V2/V3, consumed heavily by V5)

Final dispatch layer: takes a resolved (target, action, params) triple and
executes it against the right subsystem (cursor, window_manager, or the
UI bridge for spatial objects). This is the single place where gesture
intent turns into a side effect -- useful for logging/auditing every
action, which becomes important once the AI Intent Parser (V5) starts
generating actions from natural language instead of raw gestures.

TODO(V2): route window-level actions (move/resize/snap/close/...) to
          WindowManager.
TODO(V3): route spatial-object actions (select/move/drag) to ObjectManager
          + bridge/websocket_server.py so the UI updates.
TODO(V5): accept validated Action objects from ai/planner.py (see
          ai/intent.py for the schema) in addition to raw gesture-driven
          actions -- both should funnel through this same executor and
          logging path.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("stark.action_executor")


@dataclass
class Action:
    target: str          # object id, window title, or "cursor"
    intent: str           # e.g. "move", "resize", "select", "click", "open"
    params: dict[str, Any] | None = None


class ActionExecutor:
    def __init__(self, cursor, window_manager, object_manager):
        self.cursor = cursor
        self.window_manager = window_manager
        self.object_manager = object_manager

    def execute(self, action: Action) -> None:
        """
        Route an Action to the correct subsystem and log it.
        Every executed action should be logged with target/intent/params
        (per the roadmap's "auditable action planner" guidance) so gesture
        and AI-driven misfires can be debugged after the fact.
        """
        logger.info("action: target=%s intent=%s params=%s",
                    action.target, action.intent, action.params)
        raise NotImplementedError(
            "TODO(V2/V3): dispatch based on action.target/action.intent to "
            "self.cursor, self.window_manager, or self.object_manager"
        )
