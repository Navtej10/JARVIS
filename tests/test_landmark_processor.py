"""
Unit tests for tracking/landmark_processor.py.

TODO(V1): test ExponentialSmoother.update() convergence behavior with known
          alpha values (deterministic, no hardware needed).
TODO(V1): test LandmarkProcessor.to_screen_point() against a fixed
          calibration fixture (mock hand_space_corners) to verify the
          hand-space -> screen-space mapping math independent of any camera.
"""
import pytest

from tracking.landmark_processor import ExponentialSmoother


def test_exponential_smoother_converges_toward_new_value():
    smoother = ExponentialSmoother(alpha=0.5)
    first = smoother.update(0.0, 0.0)
    second = smoother.update(1.0, 1.0)
    assert first == (0.0, 0.0)
    assert second == (0.5, 0.5)  # halfway toward the new value, as expected for alpha=0.5


def test_to_screen_point_not_yet_implemented():
    pytest.skip("TODO(V1): implement to_screen_point() then replace this with a real assertion")
