"""node_intervals: the uncertainty on a node's age, as a bar on the distance axis."""
import math
import re

import pytest

from phylustrator import Style
from phylustrator.trees import loads, node_intervals, plot
from phylustrator.trees.layout import radial

NWK = "((a:1,b:1)n1:2,(c:2,d:2)n2:1)root:0.5;"
SPANS = {"n1": (2.2, 3.4), "n2": (1.1, 2.0)}


class _Lines:
    """A canvas stand-in that records the lines a layer draws, in layout coordinates."""

    def __init__(self):
        self.lines = []

    def line(self, x1, y1, x2, y2, color, width, **kw):
        self.lines.append((x1, y1, x2, y2, color, width, kw))


def _segments(svg):
    return [tuple(float(v) for v in m) for m in re.findall(
        r'<path d="M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+)" stroke="#6a9bd8"', svg)]


def test_an_interval_is_a_bar_on_the_distance_axis():
    fig = plot(loads(NWK), style=Style(width=400, height=300)) + node_intervals(SPANS)
    geom = fig.geometry()
    bars = _segments(fig.as_svg())
    assert len(bars) == 2
    rows = {n.name: n for n in geom.nodes}
    for (x0, y0, x1, y1) in bars:
        assert y0 == pytest.approx(y1), "a bar runs along the time axis, not across it"
        node = min(rows.values(), key=lambda n: abs(n.y - y0))
        lo, hi = SPANS[node.name]
        assert (x0, x1) == pytest.approx((geom.px(lo), geom.px(hi)))


def test_a_bar_lets_the_branch_show_through_and_is_squared_off():
    svg = (plot(loads(NWK)) + node_intervals(SPANS)).as_svg()
    assert 'stroke-opacity="0.45"' in svg and 'stroke-linecap="butt"' in svg


def test_one_node_may_carry_its_own_colour():
    """So that intervals which do and do not contain a known value can be told apart."""
    svg = (plot(loads(NWK)) + node_intervals(SPANS, colors={"n2": "#c1443c"})).as_svg()
    assert "#c1443c" in svg and len(_segments(svg)) == 1


def test_on_a_radial_tree_the_bar_runs_along_the_node_s_own_angle():
    """The radius is the time axis there, so the span of distance lies along the branch."""
    tree = loads(NWK)
    layout = radial(tree)
    canvas = _Lines()
    node_intervals(SPANS)(canvas, tree, layout, Style())
    stem = float(tree.root.length)
    by_name = {n.name: n for n in tree.walk() if n.name}
    assert len(canvas.lines) == 2
    for x0, y0, x1, y1, *_ in canvas.lines:
        r0, r1 = math.hypot(x0, y0), math.hypot(x1, y1)
        # match by radius, not by atan2: the layout's angles run on past pi and atan2 wraps
        name = min(SPANS, key=lambda k: abs(SPANS[k][0] - stem - r0))
        lo, hi = SPANS[name]
        assert r0 == pytest.approx(lo - stem), "the stem has to come off the radius"
        assert r1 == pytest.approx(hi - stem)
        a = layout.angle[by_name[name]]
        assert (x0, y0) == pytest.approx((r0 * math.cos(a), r0 * math.sin(a))), "off its own branch"


def test_an_unrooted_layout_has_no_age_to_draw_on():
    with pytest.raises(ValueError, match="unrooted"):
        (plot(loads(NWK), layout="unrooted") + node_intervals(SPANS)).as_svg()


def test_a_name_that_is_not_in_the_tree_is_refused():
    with pytest.raises(ValueError, match="zz"):
        (plot(loads(NWK)) + node_intervals({"zz": (1.0, 2.0)})).as_svg()


def test_an_interval_may_be_given_as_ages():
    """A clock quotes an HPD as ages before the present. Read as distances from the root, every bar
    lands somewhere else on the tree."""
    tree = loads("(((Hs:6,Pt:6)n1:2,Gg:8)n2:3,(Pp:9.5,Hl:9.5)n3:1.5)n4:4;")
    ages = {"n1": (5.2, 7.0), "n2": (7.1, 9.2), "n4": (10.1, 12.4)}
    fig = plot(tree, style=Style(width=400, height=300)) + node_intervals(ages, before_present=True)
    geom = fig.geometry()
    bars = _segments(fig.as_svg())
    assert len(bars) == 3
    for name in ages:
        node = next(n for n in geom.nodes if n.name == name)
        on_row = [b for b in bars if abs(b[1] - node.y) < 0.5]
        assert len(on_row) == 1, f"no bar on {name}'s row"
        x0, _, x1, _ = on_row[0]
        assert x0 <= node.x <= x1, f"{name} sits outside its own interval"
