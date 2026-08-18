"""
voice/speech_to_text.py  (V5)

Microphone -> text. Default to a local model (Whisper) to avoid the
latency and privacy cost of round-tripping audio to a cloud API, with
push-to-talk (or a wake word) rather than always-listening.

TODO(V5): implement push-to-talk capture (record while a hotkey/gesture is
          held, e.g. reuse the pinch-hold gesture as "listening" trigger).
TODO(V5): load a local Whisper model (base/small is usually enough for
          short commands) and transcribe the captured audio buffer.
TODO(V5): consider a lightweight wake-word engine (e.g. openWakeWord) if
          hands-free activation is preferred over push-to-talk.
"""
from __future__ import annotations


class SpeechToText:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None  # TODO(V5): whisper.load_model(model_size)

    def start_listening(self) -> None:
        raise NotImplementedError("TODO(V5): begin recording from microphone (push-to-talk)")

    def stop_listening(self) -> str:
        """Stop recording and return the transcribed text."""
        raise NotImplementedError("TODO(V5): stop recording, run Whisper transcription, return text")
