"""A rectangular tree that turns (issue #68).

The root at the top and the tips along the bottom is how a tree goes into a multi-panel figure
beside another one. Only `diagonal` turned, so the choice was a slanted tree or rotating the
finished SVG, which lays every name on its side.

The two flat layouts are the same tree in the same places and differ only in how a branch is drawn
between them, so they share the turning. What has to be checked here is the drawing: the right-angle
pair, and the layers that assumed a rectangular branch runs across the page.
"""

from __future__ import annotations

import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.trees import (
    branch_events,
    branch_markers,
    gene_path,
    highlight_clade,
    loads,
    node_intervals,
    plot,
    time_axis,
    tip_labels,
    tube,
)
from phylustrator.trees.layout import diagonal, rectangular

_NWK = "((A:1,B:1)x:1,(C:1,D:1)y:1)r:0.4;"
_STYLE = Style(width=460, height=400, margin=50)


def _figure(orientation="down", **kw):
    return plot(loads(_NWK), layout="rectangular", orientation=orientation, style=_STYLE, **kw)


def _segments(svg):
    """Every straight branch segment as (x1, y1, x2, y2)."""
    return [tuple(float(v) for v in m) for m in
            re.findall(r'<path d="M([-\d.]+),([-\d.]+) L([-\d.]+),([-\d.]+)"', svg)]


# --- the same tree in the same places as the diagonal one -----------------------------------------


@pytest.mark.parametrize("orientation", ["right", "down", "left", "up"])
def test_it_puts_the_nodes_where_the_diagonal_layout_puts_them(orientation):
    """They are one tree laid out one way; only the drawing between the nodes differs. Two copies
    of the turning would be two chances to turn it differently."""
    tree = loads(_NWK)
    flat = rectangular(tree, orientation=orientation)
    slanted = diagonal(tree, orientation=orientation)
    assert all(flat.coords[n] == slanted.coords[n] for n in tree.walk())
    assert (flat.xlim, flat.ylim) == (slanted.xlim, slanted.ylim)


def test_the_default_is_unchanged():
    """Every figure drawn before this took the right-facing layout and must still get it."""
    tree = loads(_NWK)
    assert plot(tree).as_svg() == plot(tree, orientation="right").as_svg()


def test_a_round_layout_has_no_orientation_to_take():
    for layout in ("radial", "unrooted"):
        with pytest.raises(ValueError, match="no orientation to take"):
            plot(loads(_NWK), layout=layout, orientation="down")


# --- the drawing ----------------------------------------------------------------------------------


def test_every_branch_is_still_a_right_angle_pair():
    """Turned, the run and the connector swap axes — they must not stay the way they were, or the
    tree is drawn sideways across itself."""
    svg = _figure().as_svg()
    for x1, y1, x2, y2 in _segments(svg):
        assert x1 == pytest.approx(x2) or y1 == pytest.approx(y2), "no slanted segment"
    assert any(x1 == pytest.approx(x2) for x1, _, x2, _ in _segments(svg)), "runs down the page"
    assert any(y1 == pytest.approx(y2) for _, y1, _, y2 in _segments(svg)), "connectors across it"


def test_the_run_goes_down_the_page_and_the_connector_across_it():
    """On a down tree the depth is y, so a branch runs in y at its own place in the tip order."""
    figure = _figure(stem=False)
    nodes = {p.name: p for p in figure.geometry().nodes}
    runs = [s for s in _segments(figure.as_svg()) if s[0] == pytest.approx(s[2])]
    a = [s for s in runs if s[0] == pytest.approx(nodes["A"].x, abs=0.5)]
    assert a, "A's branch runs down its own column"
    assert min(a[0][1], a[0][3]) == pytest.approx(nodes["x"].y, abs=0.5), "from its parent's depth"
    assert max(a[0][1], a[0][3]) == pytest.approx(nodes["A"].y, abs=0.5), "to its own"


def test_the_stem_runs_back_along_the_depth_axis():
    figure = _figure()
    root = {p.name: p for p in figure.geometry().nodes}["r"]
    stem = [s for s in _segments(figure.as_svg())
            if s[0] == pytest.approx(root.x, abs=0.5) and min(s[1], s[3]) < root.y - 1]
    assert stem, "the stem goes up from the root, not back along the tip order"


@pytest.mark.parametrize("orientation", ["right", "down", "left", "up"])
def test_the_tips_end_up_on_the_side_the_name_says(orientation):
    """The name says where the tips are, as a reader describes a figure."""
    figure = _figure(orientation)
    tips = figure.geometry().tips
    nodes = {p.name: p for p in figure.geometry().nodes}
    root = nodes["r"]
    if orientation == "right":
        assert all(t.x > root.x for t in tips)
    elif orientation == "left":
        assert all(t.x < root.x for t in tips)
    elif orientation == "down":
        assert all(t.y > root.y for t in tips)
    else:
        assert all(t.y < root.y for t in tips)


# --- the layers that read the layout --------------------------------------------------------------


def test_the_names_go_past_the_tips_on_the_side_the_tips_face():
    svg = (_figure() + tip_labels(offset=8)).as_svg()
    written = {text: (x, y) for x, y, text in
               re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]+)</text>', svg)}
    tips = {p.name: p for p in (_figure() + tip_labels()).geometry().tips}
    for name in "ABCD":
        assert float(written[name][1]) > tips[name].y, f"{name}'s name is below its tip"


def test_a_mark_sits_at_the_fraction_of_the_branch_it_was_given():
    """`_along` read the fraction off x, which on a turned tree is the tip order: every mark
    landed on a tip column instead of part-way down its branch."""
    figure = _figure(stem=False) + branch_markers({"A": 0.5}, at=0.25, spread=False)
    nodes = {p.name: p for p in figure.geometry().nodes}
    (cx, cy), = [(float(x), float(y)) for x, y in
                 re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', figure.as_svg())]
    assert cx == pytest.approx(nodes["A"].x, abs=0.5), "in its own column"
    want = nodes["x"].y + 0.25 * (nodes["A"].y - nodes["x"].y)
    assert cy == pytest.approx(want, abs=0.5), "a quarter of the way down from its parent"


def test_an_event_sits_at_the_depth_it_was_given():
    figure = _figure() + branch_events([{"kind": "duplication", "node": "A", "x": 1.9}],
                                       legend=False)
    nodes = {p.name: p for p in figure.geometry().nodes}
    marks = re.findall(r'<rect x="([-\d.]+)" y="([-\d.]+)"', figure.as_svg())
    assert marks, "the duplication square is drawn"
    x, y = float(marks[-1][0]), float(marks[-1][1])
    assert x == pytest.approx(nodes["A"].x, abs=6.0), "on A's own branch"
    assert nodes["x"].y < y < nodes["A"].y, "between its parent and its tip"


def test_a_tube_turns_its_corner_with_the_tree():
    """The corner is the connector meeting the run, and the two swap over when the tree turns."""
    svg = (_figure() + tube(width=16) + gene_path(["x", "A"])).as_svg()
    gene = re.findall(r'<path d="([^"]+)" fill="none" stroke="#c1443c"', svg)
    assert len(gene) == 2
    assert "Q" in gene[1], "the gene follows the tube round the bend"


def test_the_open_end_of_the_stem_is_closed_with_a_line_across_it():
    """The cap was measured between the root's corner and its start, which for a root are the same
    point: a zero-length path with no direction to lie across, in every orientation."""
    for orientation in ("right", "down", "left", "up"):
        svg = (_figure(orientation) + tube(width=16)).as_svg()
        caps = re.findall(r'<path d="M ([-\d.]+),([-\d.]+) L ([-\d.]+),([-\d.]+)" fill="none" '
                          r'stroke="#1a1a1a" stroke-width="1.6"', svg)
        assert caps, f"{orientation}: the ends are capped"
        for x1, y1, x2, y2 in caps:
            assert (x1, y1) != (x2, y2), f"{orientation}: a cap with no length draws nothing"


def test_a_clade_is_still_a_box_on_a_turned_tree():
    assert "<rect" in (_figure() + highlight_clade("x")).as_svg()


# --- what a turned tree cannot have ---------------------------------------------------------------


def test_the_time_axis_says_it_cannot_run_under_a_turned_tree():
    """It runs along the bottom, and a down tree carries its time down the page."""
    with pytest.warns(UserWarning, match="carries its time down the page"):
        (_figure() + time_axis("time")).as_svg()


def test_an_interval_bar_refuses_a_turned_tree():
    with pytest.raises(ValueError, match="cannot be drawn on a down tree"):
        (_figure() + node_intervals({"x": (0.5, 1.5)})).as_svg()


def test_a_right_facing_tree_still_takes_both():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        (_figure("right") + time_axis("time") + node_intervals({"x": (0.5, 1.5)})).as_svg()
