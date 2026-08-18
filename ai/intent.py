"""
ai/intent.py  (V5)

Sends the cleaned voice transcript + current pointing context to the LLM
(Anthropic API) and gets back a STRICT, schema-validated action.

Critical rule from the roadmap: never execute free-text LLM output
directly against the OS. The model must return JSON matching the Action
schema below, and malformed/unparseable responses must be rejected
(and probably retried or surfaced as "I didn't catch that") rather than
executed.

TODO(V5): write the system prompt: instruct the model to return ONLY JSON
          matching IntentSchema, given {transcript, pointed_at_target}.
TODO(V5): call the Anthropic API (see ai/planner.py for how this feeds
          into Action creation).
TODO(V5): validate the response against IntentSchema (pydantic) and reject/
          retry on failure -- never pass unvalidated output to the executor.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


class IntentSchema(BaseModel):
    """
    Strict schema the LLM's response must match. Pydantic validation here
    is what stands between "the model said something" and "we execute an
    OS-level action" -- do not relax this.
    """
    target: str                                   # resolved object id / window title / "cursor"
    intent: Literal["move", "resize", "select", "open", "close", "scale", "rotate", "unknown"]
    direction: Optional[str] = None                 # "left" | "right" | "up" | "down"
    scale_delta: Optional[float] = None              # e.g. +0.3 for "30% bigger"
    confidence: float = 0.0
    requires_confirmation: bool = False               # True for destructive actions (close, delete)


class IntentParser:
    def __init__(self, anthropic_api_key: str, model: str = "claude-sonnet-5"):
        self.anthropic_api_key = anthropic_api_key
        self.model = model

    def parse(self, transcript: str, pointed_at_target: str | None) -> IntentSchema:
        """
        Build the prompt (transcript + pointed_at_target for deixis grounding),
        call the Anthropic API, validate the JSON response against IntentSchema,
        and return it. Raises on invalid/malformed model output rather than
        guessing.
        """
        raise NotImplementedError(
            "TODO(V5): construct system+user prompt, call Anthropic API with "
            "response format constrained to JSON, parse + validate with IntentSchema"
        )
