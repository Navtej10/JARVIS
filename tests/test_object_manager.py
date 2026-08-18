"""
Unit tests for interaction/object_manager.py (V3).

TODO(V3): once hit_test() is implemented, add cases for:
  - point inside a single registered object -> that object returned
  - point inside two overlapping objects -> the one with higher z_index returned
  - point inside no registered objects -> None returned
"""
import pytest

from interaction.object_manager import BoundingBox, ObjectManager, SpatialObject


def test_bounding_box_contains():
    box = BoundingBox(x=10, y=10, width=100, height=50)
    assert box.contains(50, 30) is True
    assert box.contains(5, 5) is False


def test_register_and_unregister_object():
    manager = ObjectManager()
    obj = SpatialObject(id="panel1", kind="panel", bounds=BoundingBox(0, 0, 100, 100))
    manager.register_object(obj)
    assert manager._objects["panel1"] is obj
    manager.unregister_object("panel1")
    assert "panel1" not in manager._objects


def test_hit_test_not_yet_implemented():
    pytest.skip("TODO(V3): implement hit_test() then replace this with real assertions")
