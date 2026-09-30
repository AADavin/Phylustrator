"""branch_spindles: a lens on the branch, on a coloured stretch that fades into the branch."""
import re

import pytest

from phylustrator import Style
from phylustrator.trees import branch_spindles, loads, plot


def test_spindle_draws_lens_and_gradients():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree) + branch_spindles([{"node": "n1", "x": 0.7, "color": "#e07b00"},
                                         ("D", None, "#2e8b57")])).as_svg()
    assert svg.count("fill=\"#e07b00\"") >= 1 and svg.count("fill=\"#2e8b57\"") >= 1   # one lens per mark
    assert svg.count("<linearGradient") >= 4              # two fades per mark
    assert "#e07b00" in svg and "#2e8b57" in svg


def test_spindle_radial_and_missing_node():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree, layout="radial") + branch_spindles([("n2", 1.0, None), ("nope", 1.0, None)])).as_svg()
    assert svg.count("<linearGradient") == 2           # one mark drawn, the missing node skipped


def test_spindle_fades_into_the_given_colour():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree) + branch_spindles([{"node": "n1", "color": "#e07b00", "into": "#123456"}])).as_svg()
    assert "#123456" in svg


def _lens_boxes(svg):
    """Every lens polygon as (length along the branch, height across it), in pixels."""
    boxes = []
    for d, _fill in re.findall(r'<path d="([^"]+)" fill="(#[0-9a-fA-F]+)" fill-opacity=', svg):
        xs, ys = [], []
        for point in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d):
            xs.append(float(point[0]))
            ys.append(float(point[1]))
        boxes.append((max(xs) - min(xs), max(ys) - min(ys)))
    return boxes


def test_a_short_branch_shrinks_the_whole_spindle_not_just_its_length():
    """A lens cut to fit its branch kept its height, so it stood up as a sliver taller than it was
    long. Every spindle in a figure has to keep the same shape."""
    tree = loads("((A:1,B:1)X:0.25,(C:0.6,D:0.6)Y:0.65)R:0.1;")
    svg = (plot(tree, style=Style(width=120, height=80, margin=4))
           + branch_spindles([("X", None, "#c9a227"), ("Y", None, "#c9a227")],
                             length=12, height=3.6, fuse=0.5)).as_svg()
    short, full = sorted(_lens_boxes(svg))
    assert short[0] < full[0], "neither lens was shortened, so this proves nothing"
    assert short[0] / short[1] == pytest.approx(full[0] / full[1]), "the shape changed"
    assert short[0] > short[1], "the spindle is taller than it is long: a sliver, not a lens"


def test_a_branch_with_room_keeps_the_length_and_height_it_was_given():
    tree = loads("((A:1,B:1)X:3.0,(C:0.6,D:0.6)Y:3.0)R:0.1;")
    svg = (plot(tree, style=Style(width=400, height=200, margin=10))
           + branch_spindles([("X", None, "#c9a227")], length=12, height=3.6, fuse=0.5)).as_svg()
    (length, height), = _lens_boxes(svg)
    assert length == pytest.approx(12.0) and height == pytest.approx(7.2)
