"""Logarithmic time panels show multiplicative changes with equal spacing."""

import re
import xml.etree.ElementTree as ET

import pytest

from phylustrator import Style, below
from phylustrator.trees import band, loads, node_points, plot


def figure():
    return plot(loads("((a:1,b:1)x:1,(c:1,d:1)y:1)r;"),
                style=Style(width=500, height=250, margin_left=100))


def test_log_points_have_equal_decade_spacing_and_decade_ticks():
    panel = node_points({"r": 1, "x": 10, "y": 100}, log=True, line=True)
    svg = below(figure(), panel, axis=None, panel_height=180).as_svg()
    ys = sorted(float(y) for y in re.findall(r'<circle[^>]+ cy="([-\d.]+)"', svg))
    assert len(ys) == 3
    assert ys[1] - ys[0] == pytest.approx(90)
    assert ys[2] - ys[1] == pytest.approx(90)
    text = [element.text for element in ET.fromstring(svg).iter()
            if element.tag.endswith("}text")]
    assert text == ["1", "10", "100"]


def test_log_range_includes_intervals_and_handles_a_constant_value():
    assert node_points({"r": 10}, log=True).r_range()[:2] == (1, 100)
    panel = node_points({"r": 10}, intervals={"r": (0.2, 500)}, log=True)
    assert panel.r_range()[:2] == (0.1, 1000)


def test_log_band_and_middle_share_the_mapping_with_fixed_limits():
    panel = band({0: (1, 100), 1: (10, 1000)}, middle={0: 10, 1: 100},
                 log=True, vmin=1, vmax=1000, line_color="#987654")
    svg = below(figure(), panel, axis=None, panel_height=180).as_svg()
    line, = [element for element in ET.fromstring(svg).iter()
             if element.tag.endswith("}path") and element.get("stroke") == "#987654"]
    coordinates = [float(value) for value in re.findall(r"[-\d.]+", line.get("d"))]
    assert coordinates[1] - coordinates[3] == pytest.approx(60)
    assert panel.r_range()[:2] == (1, 1000)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_log_values_identify_the_invalid_node(value):
    with pytest.raises(ValueError, match="log.*bad_node"):
        node_points({"bad_node": value}, log=True)


@pytest.mark.parametrize("pair", [(0, 10), (1, float("inf"))])
def test_log_intervals_identify_the_invalid_node(pair):
    with pytest.raises(ValueError, match="log.*bad_node"):
        node_points({"bad_node": 5}, intervals={"bad_node": pair}, log=True)


def test_log_band_identifies_invalid_time_keys_in_endpoints_and_middle():
    with pytest.raises(ValueError, match="log.*2.5"):
        band({0: (1, 2), 2.5: (0, 3)}, log=True)
    with pytest.raises(ValueError, match="log.*4.5"):
        band({0: (1, 2), 1: (2, 3)}, middle={4.5: -1}, log=True)


@pytest.mark.parametrize("limit", ["vmin", "vmax"])
@pytest.mark.parametrize("value", [0, -2, float("nan"), float("inf")])
def test_log_limits_must_be_positive_and_finite(limit, value):
    with pytest.raises(ValueError, match="log.*" + limit):
        node_points({"r": 1}, log=True, **{limit: value})


def test_log_fixed_limits_must_increase():
    with pytest.raises(ValueError, match="vmin.*vmax"):
        node_points({"r": 5}, log=True, vmin=10, vmax=1)


def test_log_disabled_retains_negative_measurements_and_linear_mapping():
    panel = node_points({"r": -1, "x": 0, "y": 1}, log=False)
    assert panel.r_range()[:2] == (-1, 1)
    assert "#b8bec3" in below(figure(), panel).as_svg()
