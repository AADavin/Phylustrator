"""Marks on branches, coloured by a value (issue #43).

``branch_events`` colours a mark by its *kind* and reads from a key. This one colours by a
**number**, through the colormap ``color_branches`` uses, and records the scale so a ``colorbar``
can be added after it.
"""

from __future__ import annotations

import math
import re

import pytest

from phylustrator import Style
from phylustrator.trees import (
    branch_markers,
    colorbar,
    legend,
    loads,
    plot,
    tip_labels,
)

_NWK = "((((a:1,b:1)ab:1,(c:1,d:1)cd:1)abcd:1,(e:1,f:1)ef:1)x:1,g:4)r;"
_VALUES = {"ab": 0.12, "cd": 0.44, "ef": 0.81, "abcd": 0.33, "x": 0.95, "g": 0.6}


def _marks(svg, size=5.0):
    """Every marker's centre, in the order they were drawn."""
    return [(float(cx), float(cy)) for cx, cy in
            re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="' + f"{size:g}", svg)]


def _figure(style=None, **kw):
    return plot(loads(_NWK), style=style or Style(width=600, height=400)) + branch_markers(
        _VALUES, **kw)


# --- where the mark goes ------------------------------------------------------------------------


def test_a_mark_sits_at_the_fraction_of_its_branch_it_was_given():
    """``at`` runs from the parent (0) to the node (1), along the branch as it is drawn."""
    figure = plot(loads(_NWK)) + branch_markers({"ab": 0.5}, at=0.25, spread=False)
    nodes = {p.name: p for p in figure.geometry().nodes}
    (x, y), = _marks(figure.as_svg())
    want = nodes["abcd"].x + 0.25 * (nodes["ab"].x - nodes["abcd"].x)
    assert x == pytest.approx(want, abs=0.5)
    assert y == pytest.approx(nodes["ab"].y, abs=0.5), "on its own row, not the parent's"


def test_the_ends_of_the_branch_are_at_zero_and_one():
    nodes = {p.name: p for p in (plot(loads(_NWK))).geometry().nodes}
    for at, expect in ((0.0, "abcd"), (1.0, "ab")):
        figure = plot(loads(_NWK)) + branch_markers({"ab": 0.5}, at=at, spread=False)
        (x, _), = _marks(figure.as_svg())
        assert x == pytest.approx(nodes[expect].x, abs=0.5)


def test_a_fraction_outside_the_branch_is_refused():
    with pytest.raises(ValueError, match="fraction of the branch"):
        branch_markers(_VALUES, at=1.5)


def test_a_name_that_is_not_in_the_tree_is_refused():
    with pytest.raises(ValueError, match="not in the tree"):
        (plot(loads(_NWK)) + branch_markers({"nowhere": 1.0})).as_svg()


@pytest.mark.parametrize("layout", ["rectangular", "radial", "unrooted", "diagonal"])
def test_every_layout_draws_the_marks(layout):
    svg = (plot(loads(_NWK), layout=layout) + branch_markers(_VALUES)).as_svg()
    assert len(_marks(svg)) == len(_VALUES)


def test_a_mark_on_a_radial_branch_lands_on_its_own_angle():
    """The radial branch is a step outward along the node's angle; the mark belongs on it."""
    figure = plot(loads(_NWK), layout="radial") + branch_markers({"ab": 0.5}, at=0.5, spread=False)
    nodes = {p.name: p for p in figure.geometry().nodes}
    cx, cy = nodes["r"].x, nodes["r"].y
    (x, y), = _marks(figure.as_svg())
    to_node = math.atan2(nodes["ab"].y - cy, nodes["ab"].x - cx)
    to_mark = math.atan2(y - cy, x - cx)
    assert math.cos(to_node - to_mark) > 0.999, "same direction from the centre"


# --- the colour, and the bar that explains it ---------------------------------------------------


def test_the_scale_is_recorded_so_a_colorbar_can_read_it():
    svg = (_figure() + colorbar("rate", loc="top-left")).as_svg()
    assert ">rate</text>" in svg
    assert ">0.12</text>" in svg and ">0.95</text>" in svg, "the ends of the data"


def test_limits_fix_the_range_instead_of_the_data_doing_it():
    """Two figures meant to be compared have to mean the same thing by the same colour."""
    svg = (_figure(limits=(0.0, 1.0)) + colorbar("rate", loc="top-left")).as_svg()
    assert ">0.00</text>" in svg and ">1.00</text>" in svg


def test_labels_record_a_categorical_scale_a_legend_can_read():
    kinds = {"ab": "fast", "cd": "slow", "ef": "fast"}
    svg = (plot(loads(_NWK)) + branch_markers(kinds, palette={"fast": "#D55E00", "slow": "#0072B2"})
           + legend("rate", loc="bottom-right")).as_svg()
    assert ">fast</text>" in svg and ">slow</text>" in svg


def test_a_branch_with_no_value_gets_no_mark():
    svg = (plot(loads(_NWK)) + branch_markers({"ab": 0.5, "cd": None})).as_svg()
    assert len(_marks(svg)) == 1


# --- two marks on one spot ----------------------------------------------------------------------


def _crowded():
    """A tree whose deep branches are so short that two marks land on the same pixel."""
    return loads("(((a:1,b:1)ab:0.002,(c:1,d:1)cd:0.002)deep:0.002,(e:1,f:1)ef:0.002)r;")


def test_marks_that_would_cover_each_other_are_parted():
    tree = _crowded()
    values = {"ab": 0.1, "cd": 0.5, "ef": 0.9}
    style = Style(width=420, height=420)
    together = _marks((plot(tree, layout="radial", style=style)
                       + branch_markers(values, spread=False)).as_svg())
    apart = _marks((plot(tree, layout="radial", style=style)
                    + branch_markers(values, spread=True, gap=14.0)).as_svg())

    def closest(points):
        return min(math.dist(p, q) for i, p in enumerate(points) for q in points[i + 1:])

    assert closest(together) < closest(apart)
    assert closest(apart) >= 13.9, "parted to the gap they were given"


def test_parting_them_is_the_same_every_time():
    """A figure drawn twice has to come out the same, including the arbitrary direction two marks
    on exactly one point are parted in."""
    tree = _crowded()
    values = {"ab": 0.1, "cd": 0.5, "ef": 0.9}
    once = _marks((plot(tree, layout="radial") + branch_markers(values)).as_svg())
    twice = _marks((plot(tree, layout="radial") + branch_markers(values)).as_svg())
    assert once == twice


def test_one_mark_is_left_exactly_where_its_branch_is():
    figure = plot(loads(_NWK)) + branch_markers({"ab": 0.5})
    nodes = {p.name: p for p in figure.geometry().nodes}
    (x, y), = _marks(figure.as_svg())
    assert y == pytest.approx(nodes["ab"].y, abs=0.5), "nothing to part it from"


# --- the labels ---------------------------------------------------------------------------------


def test_a_label_goes_across_the_branch_not_along_it():
    """Along it the text runs into the tip's own name, on any branch that ends at a tip — which is
    where a figure labelling every branch puts half of them."""
    figure = (plot(loads(_NWK)) + branch_markers({"g": 0.6}, labels={"g": "0.60"}, spread=False)
              + tip_labels())
    svg = figure.as_svg()
    (mx, my), = _marks(svg)
    label = re.search(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>0\.60</text>', svg)
    lx, ly = float(label.group(1)), float(label.group(2))
    assert abs(lx - mx) < 2.0, "centred over the mark"
    assert ly < my, "above the branch, where a support value goes"


def test_a_label_is_only_written_when_it_is_given():
    svg = (plot(loads(_NWK)) + branch_markers(_VALUES, labels={"ab": "only this one"})).as_svg()
    assert ">only this one</text>" in svg
    assert svg.count("<text") == 1
