"""A panel under a rectangular tree, on the tree's time axis: ``below``, ``node_points``, the node
positions in ``Figure.geometry`` and the per-side margins that make room for them (issue #7)."""

import re
from dataclasses import replace

import pytest

from phylustrator import Style, below
from phylustrator.genomes import bars
from phylustrator.trees import loads, node_points, plot, tip_labels

# R's stem is 0.5, so under the default stem-aware layout: R 0.5, E 1.5, H 2.0, C 2.5, A 3.5
NEWICK = "(((A:1,B:1)C:1,D:2)E:1,(F:1.5,G:1.5)H:1.5)R:0.5;"


def _circles(svg):
    return [(float(x), float(y)) for x, y in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', svg)]


def _texts(svg):
    return re.findall(r"<text [^>]*>([^<]*)</text>", svg)


# --- geometry -------------------------------------------------------------------------------------

def test_geometry_lists_every_node_and_maps_time_to_pixels():
    geom = plot(loads(NEWICK)).geometry()
    by_name = {n.name: n for n in geom.nodes}
    assert len(geom.nodes) == 9
    assert {n.name for n in geom.nodes if not n.is_leaf} == {"R", "E", "C", "H"}
    for tip in geom.tips:                                   # a tip is the same point either way
        assert (by_name[tip.name].x, by_name[tip.name].y) == pytest.approx((tip.x, tip.y))
    assert geom.px(2.5) == pytest.approx(by_name["C"].x)
    assert geom.px(geom.xlim[1]) == pytest.approx(by_name["A"].x)
    assert geom.x_pixels[0] == pytest.approx(50.0)          # time 0 sits on the left margin


# --- margins --------------------------------------------------------------------------------------

def test_side_margins_default_to_margin():
    tree = loads(NEWICK)
    sides = dict(margin_left=30, margin_right=30, margin_top=30, margin_bottom=30)
    assert (plot(tree, style=Style(margin=30)).as_svg()
            == plot(tree, style=Style(margin=30, **sides)).as_svg())


def test_a_side_left_unset_follows_margin_after_replace():
    """Resolving the sides once, at construction, would freeze them at the old ``margin``."""
    style = replace(Style(margin=50, margin_left=90), margin=10)
    assert style.margin_at("left") == 90
    assert style.margin_at("bottom") == 10
    with pytest.raises(ValueError):
        style.margin_at("middle")


def test_one_side_margin_moves_only_that_side():
    tree = loads(NEWICK)
    base = Style(width=400, height=300, margin=20)
    plain = plot(tree, style=base).geometry()
    wide = plot(tree, style=replace(base, margin_left=80)).geometry()
    assert wide.x_pixels[0] == pytest.approx(80.0)
    assert wide.x_pixels[1] == pytest.approx(plain.x_pixels[1])
    assert [t.y for t in wide.tips] == pytest.approx([t.y for t in plain.tips])


# --- below ----------------------------------------------------------------------------------------

def test_below_puts_each_point_under_its_node():
    """The point of the issue: a value measured at a node is drawn at that node's pixel x."""
    fig = plot(loads(NEWICK), style=Style(margin_left=70)) + tip_labels()
    values = {"R": -1.0, "E": 2.0, "H": 3.0, "C": 0.5, "A": 1.0}
    svg = below(fig, node_points(values), axis=None).as_svg()
    geom = fig.geometry()
    x_of = {n.name: n.x for n in geom.nodes}
    circles = sorted(_circles(svg))
    assert [x for x, _ in circles] == pytest.approx(sorted(x_of[name] for name in values))
    lowest_tip = max(t.y for t in geom.tips)
    assert all(y > lowest_tip for _, y in circles)
    # higher value, higher on the page: sorted by x the nodes are R, E, H, C, A
    ys = dict(zip(["R", "E", "H", "C", "A"], (y for _, y in circles)))
    assert ys["H"] < ys["E"] < ys["A"] < ys["C"] < ys["R"]


def test_below_leaves_the_tree_where_it_was():
    fig = plot(loads(NEWICK)) + tip_labels()
    alone = fig.as_svg()
    composite = below(fig, node_points({"C": 1.0})).as_svg()
    branches = re.findall(r"<path [^>]*/>", alone)
    labels = re.findall(r"<text [^>]*>[^<]*</text>", alone)
    assert branches and labels
    assert all(element in composite for element in branches + labels)


def test_below_draws_the_time_axis_under_the_panel_and_on_the_page():
    """A small bottom margin once cut the axis label in half at the page edge."""
    fig = plot(loads(NEWICK), style=Style(margin=20))
    svg = below(fig, node_points({"C": 1.0, "H": 2.0}), axis="Time (My)").as_svg()
    assert "Time (My)" in _texts(svg)
    axis_y = float(re.search(r'<text x="[\d.]+" y="([\d.]+)"[^>]*>Time \(My\)</text>', svg).group(1))
    page_height = float(re.search(r'<svg [^>]*height="([\d.]+)"', svg).group(1))
    assert all(axis_y > y for _, y in _circles(svg))
    assert axis_y + fig.style.font_size / 2 < page_height
    assert "Time (My)" not in below(fig, node_points({"C": 1.0}), axis=None).as_svg()


def test_below_refuses_a_tree_without_a_time_axis_and_a_row_panel():
    tree = loads(NEWICK)
    with pytest.raises(ValueError, match="rectangular"):
        below(plot(tree, layout="radial"), node_points({"C": 1.0}))
    with pytest.raises(TypeError, match="beside"):
        below(plot(tree), bars({"A": 1.0}))


# --- node_points ----------------------------------------------------------------------------------

def test_node_points_names_the_nodes_it_cannot_find():
    with pytest.raises(ValueError, match="Cx"):
        below(plot(loads(NEWICK)), node_points({"Cx": 1.0, "C": 2.0}))


def test_node_points_ticks_stop_on_round_numbers():
    svg = below(plot(loads(NEWICK)), node_points({"C": -1.3, "H": 2.7}), axis=None).as_svg()
    assert {"-2", "-1", "0", "1", "2", "3"} <= set(_texts(svg))


def test_node_points_zero_line_only_when_the_range_crosses_zero():
    tree = plot(loads(NEWICK))
    assert "#b8bec3" in below(tree, node_points({"C": -1.0, "H": 2.0})).as_svg()
    assert "#b8bec3" not in below(tree, node_points({"C": 1.0, "H": 2.0})).as_svg()
    assert "#b8bec3" not in below(tree, node_points({"C": -1.0, "H": 2.0}, zero=False)).as_svg()


def test_node_points_line_joins_the_points_left_to_right():
    values = {"R": 0.0, "E": 1.0, "H": 3.0, "C": 2.0}
    svg = below(plot(loads(NEWICK)), node_points(values, line=True, line_color="#123456")).as_svg()
    assert svg.count('stroke="#123456"') == 3


# --- the interval on a value, drawn through its point (issue #12) --------------------------------

_EST = {"R": 0.2, "E": 0.947, "C": 0.776, "H": 1.195}
_SPREAD = {"R": (0.0, 0.6), "E": (0.0, 1.0), "C": (0.0, 2.0), "H": (0.7, 2.4)}


def _lines(svg, color="#3a6ea5"):
    return [tuple(float(v) for v in m) for m in
            re.findall(r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)"'
                       r'[^>]*stroke="' + color + r'"', svg)] or \
           [tuple(float(v) for v in m) for m in
            re.findall(r'<path d="M ?([-\d.]+),([-\d.]+) L ?([-\d.]+),([-\d.]+)"'
                       r'[^>]*stroke="' + color + r'"', svg)]


def _panel_svg(**kw):
    fig = plot(loads(NEWICK), style=Style(width=620, height=300, margin_left=70))
    return below(fig, node_points(_EST, **kw), panel_height=190).as_svg()


def test_a_whisker_is_drawn_through_each_point():
    """A value measured on a tree usually comes with an uncertainty, and the panel could draw the
    estimate and not the interval."""
    svg = _panel_svg(intervals=_SPREAD)
    uprights = [(x1, y1, y2) for x1, y1, x2, y2 in _lines(svg) if abs(x1 - x2) < 0.01]
    assert len(uprights) == len(_SPREAD)
    points = {round(x, 1) for x, _ in _circles(svg)}
    assert {round(x, 1) for x, _, _ in uprights} <= points, "each on its own node's column"


def test_an_interval_has_a_cap_at_each_end():
    svg = _panel_svg(intervals={"C": (0.0, 2.0)})
    flats = [(y1, x1, x2) for x1, y1, x2, y2 in _lines(svg) if abs(y1 - y2) < 0.01]
    assert len(flats) == 2


def test_the_axis_grows_to_hold_the_whiskers():
    """A range taken from the estimates alone cuts the bars off at the edge of the panel, which
    reads as an interval that stops there."""
    plain_lo, plain_hi, _ = node_points(_EST)._range()
    lo, hi, _ = node_points(_EST, intervals=_SPREAD)._range()
    assert hi >= 2.4 > plain_hi, "the top of the highest whisker is on the axis"
    assert lo <= 0.0 and lo <= plain_lo


def test_a_fixed_range_cuts_the_bar_and_drops_the_cap_it_cuts():
    """A cap on an end the axis does not reach would say the interval stops there."""
    svg = _panel_svg(intervals={"C": (0.0, 9.0)}, vmin=0.0, vmax=2.0)
    flats = [(y1, x1, x2) for x1, y1, x2, y2 in _lines(svg) if abs(y1 - y2) < 0.01]
    assert len(flats) == 1, "only the end that is on the axis gets a cap"


def test_an_interval_that_runs_backwards_is_refused():
    with pytest.raises(ValueError, match="runs backwards"):
        node_points(_EST, intervals={"C": (2.0, 0.0)})


def test_an_interval_without_a_value_is_refused():
    """It is drawn through its point, so the point has to be there."""
    with pytest.raises(ValueError, match="interval but no value"):
        node_points(_EST, intervals={"nowhere": (0.0, 1.0)})


def test_a_whisker_takes_its_node_s_own_colour():
    svg = _panel_svg(intervals={"C": (0.0, 2.0)}, colors={"C": "#D55E00"})
    assert _lines(svg, color="#D55E00")


def test_no_intervals_draws_what_it_always_drew():
    before = _panel_svg()
    assert len(_circles(before)) == len(_EST)
    assert not [1 for x1, y1, x2, y2 in _lines(before) if abs(x1 - x2) < 0.01]
