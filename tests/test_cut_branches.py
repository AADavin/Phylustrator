"""A very long branch drawn cut short (issue #64).

One branch of 10 in a tree whose others are 0.1 to 1 sets the scale, and every other branch
collapses — which is what a gene tree looks like when the program that inferred it caps a branch.
`cut=` caps each branch for the drawing, and the figure marks what it cut: a tree drawn out of scale
that does not say so misstates its own data.
"""

from __future__ import annotations

import math
import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.trees import loads, plot, time_axis, tip_labels
from phylustrator.trees.figure import _LAYOUTS
from phylustrator.trees.layout import cut_branches, rectangular, unrooted

_TIPS = ",".join(f"t{i}:0.3" for i in range(20))
_NWK = f"(({_TIPS},long:10)x:0.2,y:0.3)r;"
_DEEP = "((a:0.3,b:0.3)x:10,(c:0.3,d:0.3)y:0.2,long:10)r;"
_STYLE = Style(width=640, height=520, margin=50)


def _spans(cut):
    """How much of the tree's span the short branches take up."""
    geom = plot(loads(_NWK), style=_STYLE, cut=cut).geometry()
    pos = {p.name: p.x for p in geom.nodes}
    return (pos["t0"] - pos["r"]) / (pos["long"] - pos["r"])


def _strokes(svg):
    return re.findall(r'<path d="M ([-\d.]+),([-\d.]+) L ([-\d.]+),([-\d.]+)"', svg)


# --- the layout -----------------------------------------------------------------------------------


def test_the_long_branch_no_longer_takes_the_whole_page():
    """The figure in the issue: twenty tips sharing 5% of the width."""
    assert _spans(None) < 0.06
    assert _spans(1.0) > 0.40


def test_a_branch_shorter_than_the_cut_is_untouched():
    tree = loads(_NWK)
    uncut = rectangular(tree)
    cut = rectangular(tree, cut=1.0)
    short = tree.find("t0")
    assert cut.depth(short) == pytest.approx(uncut.depth(short))


def test_the_cut_is_per_branch_and_accumulates():
    """Capping the totals instead would pile every clade beyond a long branch on top of each other
    at the cut, rather than carrying on from it."""
    tree = loads("(a:10,(b:10,c:0.5)x:10)r;")
    layout = rectangular(tree, cut=1.0)
    assert layout.depth(tree.find("x")) == pytest.approx(1.0)
    assert layout.depth(tree.find("b")) == pytest.approx(2.0), "its own cut branch carries on from x"
    assert layout.depth(tree.find("c")) == pytest.approx(1.5)


def test_the_tree_itself_is_not_changed():
    """It is a drawing choice, not a transformation: the lengths are still there to be written."""
    tree = loads(_NWK)
    plot(tree, cut=1.0).as_svg()
    assert tree.find("long").length == pytest.approx(10.0)


def test_which_branches_were_cut_is_recorded():
    tree = loads(_NWK)
    assert {n.name for n in cut_branches(tree, 1.0)} == {"long"}
    assert cut_branches(tree, None) == frozenset()
    assert cut_branches(tree, 20.0) == frozenset()


@pytest.mark.parametrize("layout", ["rectangular", "diagonal", "radial"])
def test_the_layouts_that_carry_a_depth_cap_it(layout):
    tree = loads(_NWK)
    laid = _LAYOUTS[layout](tree, cut=1.0)
    assert laid.depth(tree.find("long")) == pytest.approx(1.2), "0.2 to x, then the cut"
    assert laid.depth(tree.find("t0")) == pytest.approx(0.5), "and a short branch is untouched"
    assert laid.cut_at == frozenset({tree.find("long")})


def test_the_unrooted_layout_caps_its_own_lengths():
    """It steps out along each branch itself rather than through the shared depth, so it is the one
    layout that could have been missed."""
    tree = loads(_NWK)
    origin = (0.0, 0.0)
    far = math.dist(unrooted(tree).coords[tree.find("long")], origin)
    cut = math.dist(unrooted(tree, cut=1.0).coords[tree.find("long")], origin)
    assert far > 9.0, "uncut it reaches right out (a little under 10.2: the path bends)"
    assert cut < 1.3, "cut, it stops just past its parent"
    assert unrooted(tree, cut=1.0).cut_at == frozenset({tree.find("long")})


def test_a_cut_of_zero_or_less_is_refused():
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="has to be positive"):
            plot(loads(_NWK), cut=bad)


def test_an_uncut_figure_is_exactly_what_it_was():
    tree = loads(_NWK)
    assert (plot(tree, style=_STYLE) + tip_labels()).as_svg() == (
        plot(tree, style=_STYLE, cut=None) + tip_labels()).as_svg()


# --- the mark it leaves ---------------------------------------------------------------------------


def test_a_cut_branch_is_marked_and_says_its_true_length():
    svg = (plot(loads(_NWK), style=_STYLE, cut=1.0) + tip_labels()).as_svg()
    assert ">10</text>" in svg, "the branch's real length, beside the break"


def test_nothing_is_marked_on_a_tree_drawn_to_scale():
    svg = (plot(loads(_NWK), style=_STYLE) + tip_labels()).as_svg()
    assert ">10</text>" not in svg


def test_the_mark_is_two_strokes_and_they_lean():
    """Upright they read as a tick or a node mark; leaning, as the break they are."""
    plain = _strokes(plot(loads(_NWK), style=_STYLE).as_svg())
    marked = _strokes(plot(loads(_NWK), style=_STYLE, cut=1.0).as_svg())
    added = len(marked) - len(plain)
    assert added == 2, "one pair, for the one cut branch"
    for x1, y1, x2, y2 in marked[-2:]:
        assert float(x1) != pytest.approx(float(x2)), "not square across a horizontal branch"
        assert float(y1) != pytest.approx(float(y2))


def test_the_mark_sits_on_the_branch_it_belongs_to():
    figure = plot(loads(_NWK), style=_STYLE, cut=1.0)
    nodes = {p.name: p for p in figure.geometry().nodes}
    marks = _strokes(figure.as_svg())[-2:]
    for x1, y1, x2, y2 in marks:
        assert nodes["x"].x < (float(x1) + float(x2)) / 2 < nodes["long"].x
        assert abs((float(y1) + float(y2)) / 2 - nodes["long"].y) < 8.0


def test_the_mark_is_drawn_over_a_layer_that_paints_the_branch():
    """It goes on last. A figure that hid its own break mark under a tube would be back to
    misstating its data."""
    svg = (plot(loads(_NWK), style=_STYLE, cut=1.0) + tip_labels()).as_svg()
    assert svg.index(">10</text>") > svg.rindex(">t19</text>")


# --- the axis that would disagree with it ---------------------------------------------------------


def test_a_cut_branch_with_descendants_warns_a_time_axis_off():
    """It holds up every clade beyond it, so the axis gives those clades the wrong distances. The
    break marks say the tree is not to scale and the axis says it is; both cannot be right."""
    with pytest.warns(UserWarning, match="hold up everything beyond them"):
        (plot(loads(_DEEP), style=_STYLE, cut=1.0) + time_axis("t")).as_svg()


def test_a_cut_tip_branch_moves_nothing_else_and_is_not_warned_about():
    """The usual case, and the one in the issue."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        (plot(loads(_NWK), style=_STYLE, cut=1.0) + time_axis("t")).as_svg()


def test_an_uncut_tree_with_an_axis_is_silent():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        (plot(loads(_DEEP), style=_STYLE) + time_axis("t")).as_svg()
