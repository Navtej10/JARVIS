"""
Shared pytest fixtures. Add camera/MediaPipe mocks here as tests need them,
so individual test files stay hardware-free.
"""
import sys
from pathlib import Path

# Make the project root importable as `tracking`, `gestures`, etc. when
# running `pytest` from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent))
