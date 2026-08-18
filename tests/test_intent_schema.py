"""
Unit tests for ai/intent.py's IntentSchema (V5).

This is cheap to test fully right now since it's pure pydantic validation --
no LLM call required. Get this locked down before wiring up the actual API
call, since the schema is the safety boundary between "model said something"
and "we execute an OS action."
"""
import pytest
from pydantic import ValidationError

from ai.intent import IntentSchema


def test_valid_intent_parses():
    intent = IntentSchema(target="vscode", intent="move", direction="left", confidence=0.9)
    assert intent.intent == "move"
    assert intent.requires_confirmation is False  # default


def test_invalid_intent_value_rejected():
    with pytest.raises(ValidationError):
        IntentSchema(target="vscode", intent="delete_everything")  # not in the allowed Literal set


def test_destructive_action_can_require_confirmation():
    intent = IntentSchema(target="vscode", intent="close", requires_confirmation=True)
    assert intent.requires_confirmation is True
