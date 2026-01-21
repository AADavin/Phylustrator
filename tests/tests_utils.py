import pytest
from phylustrator.utils import to_rgb, to_hex, lerp_color, polar_to_cartesian
import math

def test_to_rgb():
    assert to_rgb("#ffffff") == (255, 255, 255)
    assert to_rgb("#000") == (0, 0, 0)
    assert to_rgb("red") == (255, 0, 0)
    assert to_rgb("invalid") == (0, 0, 0)

def test_to_hex():
    assert to_hex((255, 255, 255)) == "#ffffff"
    assert to_hex((0, 0, 0)) == "#000000"
    # Test clipping
    assert to_hex((300, -10, 100)) == "#ff0064"

def test_lerp_color():
    # Midpoint between black and white
    assert lerp_color("#000000", "#ffffff", 0.5) == "#7f7f7f"
    # Bound checks
    assert lerp_color("#000000", "#ffffff", -1) == "#000000"
    assert lerp_color("#000000", "#ffffff", 2) == "#ffffff"

def test_polar_to_cartesian():
    # 0 degrees, radius 100 should be (100, 0)
    x, y = polar_to_cartesian(0, 100)
    assert pytest.approx(x) == 100
    assert pytest.approx(y) == 0
    
    # 90 degrees, radius 100 should be (0, 100)
    x, y = polar_to_cartesian(90, 100)
    assert pytest.approx(x) == 0
    assert pytest.approx(y) == 100
