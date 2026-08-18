"""
Central settings loader for Stark Interface.

Loads environment variables (.env) and calibration/config JSON, and exposes
them as a single typed object so no module has to know *where* config comes
from -- only `settings` module does.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path(__file__).parent
CALIBRATION_PATH = CONFIG_DIR / "calibration.json"
CALIBRATION_EXAMPLE_PATH = CONFIG_DIR / "calibration.example.json"


@dataclass
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    camera_index: int = field(default_factory=lambda: int(os.getenv("STARK_CAMERA_INDEX", "0")))
    log_level: str = field(default_factory=lambda: os.getenv("STARK_LOG_LEVEL", "INFO"))
    calibration: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Settings":
        path = CALIBRATION_PATH if CALIBRATION_PATH.exists() else CALIBRATION_EXAMPLE_PATH
        with open(path, "r", encoding="utf-8") as f:
            calibration = json.load(f)
        return cls(calibration=calibration)


settings = Settings.load()
