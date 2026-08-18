"""
voice/command_parser.py  (V5)

Light preprocessing on raw transcribed text before it's handed to the AI
Intent Parser (ai/intent.py) -- e.g. stripping filler words, normalizing
punctuation. This is intentionally NOT where intent understanding happens;
keep the actual "what does the user want" reasoning in ai/intent.py so
there's one place responsible for that decision.

TODO(V5): implement basic text cleanup (lowercase, strip filler words like
          "um"/"uh", trim whitespace).
TODO(V5): optionally detect obviously-invalid/empty transcriptions early
          and short-circuit before calling the LLM.
"""
from __future__ import annotations


def clean_transcript(raw_text: str) -> str:
    raise NotImplementedError("TODO(V5): normalize raw STT output before AI intent parsing")
