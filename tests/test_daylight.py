"""Equal-daylight for unrooted trees (issue #71).

Equal-angle gives each subtree a wedge in proportion to its leaves, measured at the root. Further
out that wedge is no longer where the subtree sits, so a tree with a long backbone bends into a half
circle and one whole side of the picture stays empty. Felsenstein's refinement looks at each
internal node in turn and turns its subtrees until the gaps between them are equal.
"""

from __future__ import annotations

import math

import pytest

from phylustrator import Style
from phylustrator.trees import loads, plot
from phylustrator.trees.layout import _arc, unrooted


def _ladder(k=12):
    """The tree in the issue: a long backbone of small clades, which is the shape that bends."""
    def clade(i):
        return f"((t{i}a:1,t{i}b:1):1,(t{i}c:1,t{i}d:1):1)"
    nwk = clade(0)
    for i in range(1, k):
        nwk = f"({nwk}:1,{clade(i)}:1)"
    return loads(nwk + ";")


def _shape(layout, tree):
    """How square the drawing is, and the widest empty angle around the middle of the tips."""
    xs = [layout.coords[n][0] for n in tree.walk()]
    ys = [layout.coords[n][1] for n in tree.walk()]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    tips = [layout.coords[leaf] for leaf in tree.leaves]
    cx = sum(x for x, _ in tips) / len(tips)
    cy = sum(y for _, y in tips) / len(tips)
    angles = sorted(math.atan2(y - cy, x - cx) for x, y in tips)
    gaps = [(angles[(i + 1) % len(angles)] - a) % (2 * math.pi) for i, a in enumerate(angles)]
    return min(w, h) / max(w, h), math.degrees(max(gaps))


# --- the arc of a subtree -------------------------------------------------------------------------


def test_one_point_covers_no_arc():
    assert _arc([0.3]) == (0.3, 0.0)


def test_an_arc_is_the_complement_of_the_widest_gap():
    angles = [0.0, 0.1, 0.2]
    start, width = _arc(angles)
    assert start == pytest.approx(0.0)
    assert width == pytest.approx(0.2)


def test_an_arc_across_the_far_side_of_zero_is_not_the_whole_circle():
    """A set of angles has no least and no greatest. Measured as max minus min, a subtree sitting
    either side of zero would come out as nearly the whole circle and never be moved."""
    angles = [-0.1, 0.0, 0.1]
    start, width = _arc(angles)
    assert width == pytest.approx(0.2)
    assert start == pytest.approx(-0.1)


# --- what it does to the picture --------------------------------------------------------------


def test_the_tree_is_spread_over_the_whole_circle():
    tree = _ladder()
    flat_ratio, flat_gap = _shape(unrooted(tree, cladogram=True), tree)
    day_ratio, day_gap = _shape(unrooted(tree, cladogram=True, daylight=True), tree)
    assert flat_gap > 60.0, "equal-angle leaves a side of it empty"
    assert day_gap < 30.0, "equal-daylight fills it"
    assert day_ratio > flat_ratio, "and the drawing comes out squarer"


def test_the_tips_all_moved_somewhere():
    tree = _ladder()
    flat = unrooted(tree, cladogram=True)
    day = unrooted(tree, cladogram=True, daylight=True)
    moved = sum(1 for leaf in tree.leaves
                if math.dist(flat.coords[leaf], day.coords[leaf]) > 1e-6)
    assert moved > len(tree.leaves) / 2


def test_it_is_off_unless_asked_for():
    tree = _ladder(4)
    assert unrooted(tree).coords == unrooted(tree, daylight=False).coords


def test_the_same_tree_comes_out_the_same_way_twice():
    """A figure drawn twice has to be the same figure, and this one turns things in a loop."""
    tree = _ladder(5)
    assert unrooted(tree, daylight=True).coords == unrooted(tree, daylight=True).coords


def test_the_branch_lengths_are_not_touched():
    """It turns subtrees about their nodes, so every branch keeps the length it was drawn at."""
    tree = _ladder(5)
    flat, day = unrooted(tree), unrooted(tree, daylight=True)

    def lengths(layout):
        return sorted(round(math.dist(layout.coords[n], layout.coords[n.parent]), 9)
                      for n in tree.walk() if n.parent is not None)

    assert lengths(flat) == lengths(day)


def test_a_number_asks_for_that_many_rounds():
    tree = _ladder()
    one = unrooted(tree, cladogram=True, daylight=1)
    many = unrooted(tree, cladogram=True, daylight=8)
    assert one.coords != many.coords
    assert _shape(many, tree)[1] <= _shape(one, tree)[1] + 1.0, "more rounds do not make it worse"


def test_no_rounds_is_the_layout_it_started_from():
    tree = _ladder(4)
    assert unrooted(tree, daylight=0).coords == unrooted(tree).coords


def test_a_tree_too_small_to_have_daylight_is_left_alone():
    """Every node here has two neighbours or fewer, so there is nothing to share out."""
    tree = loads("(a:1,b:1);")
    assert unrooted(tree, daylight=True).coords == unrooted(tree).coords


# --- through the figure -------------------------------------------------------------------------


def test_the_figure_takes_it_and_draws():
    figure = plot(_ladder(), layout="unrooted", cladogram=True, daylight=True,
                  style=Style(width=600, height=600))
    assert "<path" in figure.as_svg()


def test_it_survives_adding_a_layer():
    base = plot(_ladder(4), layout="unrooted", daylight=True)
    assert (base + (lambda c, t, lay, s: None)).daylight is True


def test_the_layout_is_only_worked_out_once():
    """The figure is laid out for a measuring pass, for the drawing, and again for a geometry. At
    a couple of seconds on a thousand tips, paying that three times would show."""
    figure = plot(_ladder(4), layout="unrooted", daylight=True)
    assert figure._lay_out() is figure._lay_out()


def test_the_layouts_that_have_no_daylight_to_share_refuse_it():
    for layout in ("rectangular", "radial", "diagonal"):
        with pytest.raises(ValueError, match="no daylight to share out"):
            plot(_ladder(3), layout=layout, daylight=True)
