"""Tip bars share their zero and numeric scale, including on ragged trees."""

import xml.etree.ElementTree as ET

import pytest

from phylustrator import Style, trees
from phylustrator.render import text_width


def figure(**kwargs):
    return trees.plot(trees.loads("((A:1,B:2)x:1,C:4)r;"),
                      style=Style(width=1000, height=380, margin=70), **kwargs)


def elements(svg, kind):
    return [node for node in ET.fromstring(svg).iter() if node.tag.endswith("}" + kind)]


def bars(svg):
    return [node for node in elements(svg, "rect") if node.get("fill") == "#123456"]


@pytest.mark.parametrize("orientation", ["right", "left"])
def test_bars_have_a_shared_origin_and_proportional_lengths(orientation):
    fig = figure(orientation=orientation) + trees.tip_bars(
        {"A": 2, "B": 4, "C": 1}, width=220, gap=10, color="#123456", ticks=(0, 2, 4))
    svg = fig.as_svg()
    rectangles = bars(svg)
    assert len(rectangles) == 3
    assert [float(r.get("width")) for r in rectangles] == pytest.approx([110, 220, 55])
    origins = [float(r.get("x")) + (float(r.get("width")) if orientation == "left" else 0)
               for r in rectangles]
    assert origins == pytest.approx([origins[0]] * 3)
    tips = fig.geometry().tips
    centers = [float(r.get("y")) + float(r.get("height")) / 2 for r in rectangles]
    assert centers == pytest.approx([tip.y for tip in tips])
    assert all(origin > max(t.x for t in tips) if orientation == "right"
               else origin < min(t.x for t in tips) for origin in origins)


def test_grid_is_behind_bars_and_the_axis_sits_below_all_rows():
    fig = figure() + trees.tip_bars({"A": 4}, color="#123456", label="Genes", ticks=(0, 2, 4))
    svg = fig.as_svg()
    rect, = bars(svg)
    y_bottom = max(tip.y for tip in fig.geometry().tips)
    text = {node.text: node for node in elements(svg, "text")}
    assert all(float(text[tick].get("y")) > y_bottom for tick in ("0", "2", "4", "Genes"))
    assert svg.index('stroke="#d9dee3"') < svg.index('fill="#123456"')
    assert float(rect.get("height")) > 0


def test_labels_and_numeric_axis_stay_inside_the_page():
    names = {"A": "Long tip name", "B": "Another tip", "C": "Last tip"}
    fig = figure() + trees.tip_labels(values=names) + trees.tip_bars(
        {"A": 4, "B": 2, "C": 0}, color="#123456", label="Genes per genome") + trees.title("Counts")
    svg = fig.as_svg()
    rectangles = bars(svg)
    origin = float(rectangles[0].get("x"))
    text = elements(svg, "text")
    for node in text:
        x, y = float(node.get("x")), float(node.get("y"))
        size = float(node.get("font-size"))
        assert 0 <= y - size / 2 <= y + size / 2 <= fig.style.height
        if node.text in names.values():
            assert x + text_width(node.text, family=fig.style.font_family, size=size) < origin
    assert max(float(r.get("x")) + float(r.get("width")) for r in rectangles) <= fig.style.width


def test_explicit_maximum_clips_and_zero_values_are_valid():
    svg = (figure() + trees.tip_bars({"A": 10, "B": 0}, vmax=5, width=100,
                                   color="#123456")).as_svg()
    assert [float(r.get("width")) for r in bars(svg)] == [100, 0]
    zero_svg = (figure() + trees.tip_bars({"A": 0}, color="#123456")).as_svg()
    zero, = bars(zero_svg)
    assert float(zero.get("width")) == 0
    assert float(zero.get("height")) > 0
    assert "1" in [node.text for node in elements(zero_svg, "text")]


@pytest.mark.parametrize("kwargs", [{"layout": "radial"}, {"orientation": "down"}])
def test_unsupported_layouts_are_rejected(kwargs):
    with pytest.raises(ValueError, match="rectangular.*right.*left"):
        (figure(**kwargs) + trees.tip_bars({"A": 1})).as_svg()


@pytest.mark.parametrize("values,kwargs", [
    ({}, {}), ({"A": -1}, {}), ({"A": float("nan")}, {}), ({"A": float("inf")}, {}),
    ({"A": 1}, {"vmax": 0}), ({"A": 1}, {"width": -1}),
    ({"A": 1}, {"gap": -1}), ({"A": 1}, {"ticks": (-1,)}),
])
def test_invalid_values_and_geometry_are_rejected(values, kwargs):
    with pytest.raises(ValueError):
        trees.tip_bars(values, **kwargs)


def test_unknown_tip_names_are_rejected():
    with pytest.raises(ValueError, match="unknown"):
        (figure() + trees.tip_bars({"unknown": 4})).as_svg()
