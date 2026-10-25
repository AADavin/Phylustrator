"""The species tube and the gene inside it (issue #42).

The usual picture of a reconciliation: the species tree drawn as a wide branch with rounded bends,
and the gene as a thin line running inside it — along a branch, starting part-way down one, stopping
where it is lost.
"""

from __future__ import annotations

import math
import re

import pytest

from phylustrator import Style
from phylustrator.trees import branch_events, gene_path, loads, plot, tip_labels, tube

_NWK = "(((A:0.45,B:0.45)ab:0.25,C:0.7)abc:0.3,(D:0.5,E:0.5)de:0.5)root:0.15;"


def _paths(svg, stroke=None, width=None):
    """Every path drawn, as (d, stroke, stroke-width)."""
    out = []
    for line in svg.splitlines():
        found = re.search(r'<path d="([^"]+)"[^>]*stroke="([^"]+)" stroke-width="([\d.]+)"', line)
        if not found:
            continue
        d, paint, w = found.group(1), found.group(2), float(found.group(3))
        if (stroke is None or paint == stroke) and (width is None or abs(w - width) < 0.01):
            out.append((d, paint, w))
    return out


def _points(d):
    return [(float(x), float(y)) for x, y in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)]


def _figure(layout="rectangular", **kw):
    style = Style(width=600, height=380, margin=50)
    return plot(loads(_NWK), style=style, layout=layout, skeleton=False, **kw)


# --- the tube ------------------------------------------------------------------------------------


def test_every_branch_is_drawn_twice_wide_then_narrow():
    """Once in the outline colour and once narrower in the fill, so the outlines of two branches
    leaving one node merge into a tube instead of crossing it."""
    svg = (_figure() + tube(width=18, edge=2.0)).as_svg()
    outline = _paths(svg, stroke="#1a1a1a", width=18.0)
    fill = _paths(svg, stroke="#f2f2f2", width=14.0)
    branches = sum(1 for n in loads(_NWK).walk() if n.parent is not None) + 1   # and the stem
    assert len(outline) == len(fill) == branches


def test_every_outline_is_drawn_before_any_fill():
    """Otherwise a branch drawn later cuts its outline across one drawn earlier."""
    svg = (_figure() + tube()).as_svg()
    order = [paint for _, paint, _ in _paths(svg)]
    assert order == sorted(order, key=lambda p: 0 if p == "#1a1a1a" else 1)


def test_a_bend_is_rounded():
    svg = (_figure() + tube(radius=8)).as_svg()
    assert any("Q" in d for d, _, _ in _paths(svg)), "the turn at a split is curved"


def test_no_radius_means_no_curve():
    svg = (_figure() + tube(radius=0)).as_svg()
    assert all("Q" not in d for d, _, _ in _paths(svg))


def test_a_tip_gets_the_outside_of_its_cap_on_the_tip():
    """A round cap reaches half the tube's width past the end of its path, so a tube drawn to the
    tip would overhang it and run under the tip's own label."""
    width = 18.0
    figure = _figure() + tube(width=width)
    tips = {p.name: p for p in figure.geometry().tips}
    ends = [_points(d)[-1] for d, _, _ in _paths(figure.as_svg(), stroke="#1a1a1a")]
    near_a = min(ends, key=lambda p: abs(p[1] - tips["A"].y) + abs(p[0] - tips["A"].x))
    assert near_a[0] == pytest.approx(tips["A"].x - width / 2, abs=1.0)


def test_an_inner_branch_keeps_its_cap_to_fill_the_fork():
    """Between two branches leaving a node at an angle there is a wedge, and the cap is what fills
    it: squared off, a diagonal tree shows a notch at every fork."""
    figure = _figure(layout="diagonal") + tube(width=16)
    nodes = {p.name: p for p in figure.geometry().nodes}
    ends = [_points(d)[-1] for d, _, _ in _paths(figure.as_svg(), stroke="#1a1a1a")]
    assert any(math.dist(p, (nodes["ab"].x, nodes["ab"].y)) < 0.6 for p in ends)


def test_a_tube_needs_a_layout_whose_branches_cross_the_page():
    for layout in ("radial", "unrooted"):
        with pytest.raises(ValueError, match="rectangular or diagonal"):
            (_figure(layout=layout) + tube()).as_svg()


def test_the_tube_takes_its_colours_and_its_width():
    svg = (_figure() + tube(width=30, fill="#ffffff", stroke="#0072B2", edge=3.0)).as_svg()
    assert _paths(svg, stroke="#0072B2", width=30.0)
    assert _paths(svg, stroke="#ffffff", width=24.0)


# --- the gene inside it ---------------------------------------------------------------------------


def _gene(segments, **kw):
    figure = _figure() + gene_path(segments, **kw)
    return figure, _paths(figure.as_svg(), stroke=kw.get("color", "#c1443c"))


def test_a_whole_branch_is_named_by_itself():
    figure, drawn = _gene(["C"])
    assert len(drawn) == 1
    nodes = {p.name: p for p in figure.geometry().nodes}
    points = _points(drawn[0][0])
    assert points[0] == pytest.approx((nodes["abc"].x, nodes["abc"].y), abs=0.6)
    assert points[-1] == pytest.approx((nodes["C"].x, nodes["C"].y), abs=0.6)


def test_a_segment_that_starts_part_way_down_begins_there():
    """A copy born inside a branch starts where it is born, not at the split above it."""
    figure, drawn = _gene([{"branch": "abc", "from": 0.30}])
    nodes = {p.name: p for p in figure.geometry().nodes}
    first = _points(drawn[0][0])[0]
    assert nodes["root"].x < first[0] < nodes["abc"].x
    assert first[1] == pytest.approx(nodes["abc"].y, abs=0.6)


def test_a_segment_that_starts_at_the_top_comes_through_the_bend():
    """Otherwise the line cuts the corner instead of following the tube round it."""
    _, through = _gene(["ab"])
    _, part = _gene([{"branch": "ab", "from": 0.75}])
    assert len(_points(through[0][0])) > len(_points(part[0][0]))


def test_a_segment_can_stop_early():
    """Where a lineage is lost part-way down a branch."""
    figure, drawn = _gene([{"branch": "C", "to": 0.60}])
    nodes = {p.name: p for p in figure.geometry().nodes}
    assert _points(drawn[0][0])[-1][0] < nodes["C"].x


def test_depths_outside_the_branch_are_pulled_onto_it():
    figure, drawn = _gene([{"branch": "C", "from": -5.0, "to": 99.0}])
    nodes = {p.name: p for p in figure.geometry().nodes}
    points = _points(drawn[0][0])
    assert points[-1][0] == pytest.approx(nodes["C"].x, abs=0.6)


def test_two_copies_in_one_tube_can_run_side_by_side():
    _, middle = _gene(["C"])
    _, shifted = _gene(["C"], offset=4.0)
    assert _points(shifted[0][0])[0][1] - _points(middle[0][0])[0][1] == pytest.approx(4.0, abs=0.1)


def test_a_lineage_can_be_drawn_broken():
    _, drawn = _gene(["C"], dash=True)
    svg = (_figure() + gene_path(["C"], dash=True)).as_svg()
    assert "stroke-dasharray" in svg


def test_a_name_that_is_not_in_the_tree_is_refused():
    with pytest.raises(ValueError, match="not in the tree"):
        (_figure() + gene_path(["nowhere"])).as_svg()


def test_the_gene_needs_the_same_layouts_the_tube_does():
    with pytest.raises(ValueError, match="rectangular or diagonal"):
        (_figure(layout="radial") + gene_path(["C"])).as_svg()


def test_the_whole_reconciliation_draws():
    """The figure issue #42 wrote by hand: a gene entering part-way down a branch, following it to
    three tips, transferred to another lineage, and carrying on there."""
    figure = (_figure()
              + tube(width=18)
              + gene_path([{"branch": "abc", "from": 0.30}, "ab", "A", "B", "C",
                           {"branch": "D", "from": 0.90}])
              + branch_events([{"kind": "transfer", "donor": "C", "recipient": "D", "x": 0.90}],
                              legend=False)
              + tip_labels(offset=14))
    svg = figure.as_svg()
    assert len(_paths(svg, stroke="#c1443c")) == 6
    assert "#2e8b57" in svg, "the transfer arrow"
