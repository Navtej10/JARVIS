import pytest
import math
from gestures.rotate import snap_value

def test_snap_value():
    # Test linear snapping (like scale)
    assert snap_value(1.23, 0.1) == 1.2
    assert snap_value(1.27, 0.1) == 1.3
    assert snap_value(0.99, 0.1) == 1.0
    assert snap_value(0.95, 0.1) == 1.0
    assert snap_value(0.94, 0.1) == 0.9

    # Test increment <= 0
    assert snap_value(1.23, 0.0) == 1.23
    assert snap_value(1.23, -1.0) == 1.23

    # Test angular snapping (like rotation, in radians)
    increment_15_deg = math.radians(15)
    
    # 10 degrees -> 15 degrees
    val_10 = math.radians(10)
    snapped_10 = snap_value(val_10, increment_15_deg)
    assert math.isclose(snapped_10, math.radians(15), abs_tol=1e-4)
    
    # 7 degrees -> 0 degrees
    val_7 = math.radians(7)
    snapped_7 = snap_value(val_7, increment_15_deg)
    assert math.isclose(snapped_7, 0.0, abs_tol=1e-4)
    
    # 22 degrees -> 15 degrees (wait, 22.5 is the midpoint. 22 is < 22.5, so rounds to 15)
    val_22 = math.radians(22)
    snapped_22 = snap_value(val_22, increment_15_deg)
    assert math.isclose(snapped_22, math.radians(15), abs_tol=1e-4)

    # 23 degrees -> 30 degrees
    val_23 = math.radians(23)
    snapped_23 = snap_value(val_23, increment_15_deg)
    assert math.isclose(snapped_23, math.radians(30), abs_tol=1e-4)
