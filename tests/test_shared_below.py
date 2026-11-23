"""Overlay comparisons keep one common vertical scale and a visible series key."""

import xml.etree.ElementTree as ET

import pytest

from phylustrator import Style, below
from phylustrator.trees import band, loads, node_points, plot


def figure(width=500):
    return plot(loads("((a:1,b:1)x:1,(c:1,d:1)y:1)r;"),
                style=Style(width=width, height=250, margin_left=70))


def elements(svg, kind):
    return [element for element in ET.fromstring(svg).iter()
            if element.tag.endswith("}" + kind)]


def test_series_share_a_scale_and_only_one_y_axis():
    first = node_points({"r": 1, "x": 2}, color="#123456", label="Rate")
    second = node_points({"y": 100}, color="#abcdef", label="Rate")
    svg = below(figure(), [first, second], labels=["Method A", "Method B"],
                axis=None, panel_height=180).as_svg()
    small = [float(circle.get("cy")) for circle in elements(svg, "circle")
             if circle.get("fill") == "#123456"]
    largest, = [float(circle.get("cy")) for circle in elements(svg, "circle")
                if circle.get("fill") == "#abcdef"]
    assert 0 < abs(small[1] - small[0]) < 180 / 10
    assert largest < min(small)
    text = [element.text for element in elements(svg, "text")]
    assert text.count("Rate") == 1
    assert "Method A" in text and "Method B" in text


def test_interval_bounds_participate_in_the_shared_scale_without_mutation():
    first = node_points({"r": 50}, intervals={"r": (0, 200)}, color="#123456")
    second = node_points({"x": 50}, color="#abcdef")
    originals = [vars(panel).copy() for panel in (first, second)]
    svg = below(figure(), [first, second], axis=None).as_svg()
    circles = elements(svg, "circle")
    assert len(circles) == 2
    assert float(circles[0].get("cy")) == pytest.approx(float(circles[1].get("cy")))
    assert [vars(panel) for panel in (first, second)] == originals
    assert first.r_range()[:2] == (0, 200)


def test_band_and_points_can_share_a_panel():
    region = band({0: (1, 100), 1: (1, 100)}, color="#112233")
    points = node_points({"r": 50}, color="#445566")
    svg = below(figure(), [region, points], axis=None).as_svg()
    assert "#112233" in svg and "#445566" in svg
    assert len(elements(svg, "circle")) == 1
    assert "Series 1" in svg and "Series 2" in svg


def test_one_element_sequence_keeps_the_single_panel_output():
    panel = node_points({"r": 1, "x": 2})
    assert below(figure(), (panel,)).as_svg() == below(figure(), panel).as_svg()


def test_legend_wraps_entries_and_stays_on_the_page():
    panels = [node_points({"r": n}, color=color) for n, color in
              enumerate(("red", "green", "blue"), 1)]
    svg = below(figure(width=300), panels,
                labels=["First method", "Second method", "Third method"]).as_svg()
    text = [element for element in elements(svg, "text") if "method" in (element.text or "")]
    assert len(text) == 3
    ys = [float(element.get("y")) for element in text]
    assert len(set(ys)) > 1
    assert max(ys) < float(ET.fromstring(svg).get("height"))


def test_empty_series_and_mismatched_names_are_rejected():
    with pytest.raises(ValueError, match="at least one"):
        below(figure(), [])
    with pytest.raises(ValueError, match="labels"):
        below(figure(), [node_points({"r": 1})], labels=["one", "two"])
