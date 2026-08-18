"""
ai/planner.py  (V5)

Converts a validated IntentSchema into an interaction.action_executor.Action,
adding any destructive-action confirmation flow before it's dispatched.

TODO(V5): implement build_action(), mapping IntentSchema fields onto Action
          (target, intent, params).
TODO(V5): implement confirmation flow -- if requires_confirmation is True,
          surface a brief visual confirm state (via the UI bridge) and wait
          for a confirming gesture/voice response before calling
          ActionExecutor.execute().
"""
from __future__ import annotations

from ai.intent import IntentSchema
from interaction.action_executor import Action


class ActionPlanner:
    def __init__(self, action_executor):
        self.action_executor = action_executor

    def build_action(self, intent: IntentSchema) -> Action:
        raise NotImplementedError("TODO(V5): map IntentSchema -> Action")

    def plan_and_execute(self, intent: IntentSchema) -> None:
        raise NotImplementedError(
            "TODO(V5): build Action; if intent.requires_confirmation, request "
            "confirmation via the UI bridge before calling "
            "self.action_executor.execute(action)"
        )
