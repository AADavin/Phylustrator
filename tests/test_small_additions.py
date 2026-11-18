"""Three smaller things: a straight transfer arrow, a named ring band, and a labelled grid.

Issues #77, #69 and #72. Each is a figure that could be drawn by hand with a layer of one's own —
which is what all three reporters did — and each is a line of the library's own job.
"""

from __future__ import annotations

import math
import re

import pytest

import phylustrator as ph
from phylustrator import Style
from phylustrator.compose import _spans
from phylustrator.trees import branch_events, loads, plot, ring, tip_labels

# --- #77: a transfer drawn straight ---------------------------------------------------------------

_T_NWK = "((A:1,B:1)ab:1,(C:1.5,D:1.5)cd:0.5)r;"
_TRANSFER = {"kind": "transfer", "donor": "C", "recipient": "B", "x": 1.6}


def _arrow(figure):
    found = re.findall(r'<path d="([^"]+)"[^>]*stroke="#2e8b57"', figure.as_svg())
    return found[0] if found else None


def _control(d):
    """The quadratic's control point — where the bow is."""
    x, y = re.search(r"Q([-\d.]+),([-\d.]+)", d).groups()
    return float(x), float(y)


def _ends(d):
    m = re.match(r"M([-\d.]+),([-\d.]+) Q[-\d.]+,[-\d.]+,([-\d.]+),([-\d.]+)", d)
    return [float(v) for v in m.groups()]


def test_a_transfer_bows_out_by_default():
    d = _arrow(plot(loads(_T_NWK), stem=False) + branch_events([_TRANSFER], legend=False))
    x0, y0, x1, y1 = _ends(d)
    cx, _ = _control(d)
    assert abs(cx - (x0 + x1) / 2) > 5.0, "the control point is off the line"


def test_curve_zero_draws_it_straight():
    """A transfer happens at one time, so on a rectangular tree a straight arrow at that time
    shows the donor and the recipient both standing there."""
    d = _arrow(plot(loads(_T_NWK), stem=False)
               + branch_events([_TRANSFER], legend=False, curve=0))
    x0, y0, x1, y1 = _ends(d)
    cx, cy = _control(d)
    assert cx == pytest.approx((x0 + x1) / 2, abs=0.01)
    assert cy == pytest.approx((y0 + y1) / 2, abs=0.01)


def test_one_event_can_ask_for_its_own_bow():
    """The one arrow that would otherwise run along a branch and be lost in it."""
    straight = _arrow(plot(loads(_T_NWK), stem=False)
                      + branch_events([{**_TRANSFER, "curve": 0}], legend=False))
    bowed = _arrow(plot(loads(_T_NWK), stem=False)
                   + branch_events([{**_TRANSFER, "curve": 40}], legend=False))
    assert _control(straight) != _control(bowed)


def test_an_offset_arrow_bows_the_same_way():
    """The shifted path is a different call, and used to ignore the bow entirely."""
    d = _arrow(plot(loads(_T_NWK), stem=False)
               + branch_events([_TRANSFER], legend=False, offset=4.0, curve=0))
    x0, y0, x1, y1 = _ends(d)
    cx, _ = _control(d)
    assert cx == pytest.approx((x0 + x1) / 2, abs=0.01)


# --- #69: naming a ring's bands -------------------------------------------------------------------

_R_NWK = "(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1);"
_GROUPS = {n: ("left" if n in "ABCD" else "right") for n in "ABCDEFGH"}
_PALETTE = {"left": "#2B64A8", "right": "#2E7D3A"}


def _ring_figure(**kw):
    return (plot(loads(_R_NWK), layout="radial", style=Style(width=560, height=520))
            + ring(_GROUPS, palette=_PALETTE, **kw))


def _label(svg, text):
    found = re.search(rf'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*fill="([^"]+)"[^>]*>{text}</text>',
                      svg)
    return (float(found.group(1)), float(found.group(2)), found.group(3)) if found else None


def test_a_band_is_named_in_its_own_colour():
    svg = _ring_figure(labels=True).as_svg()
    assert _label(svg, "left")[2] == "#2B64A8"
    assert _label(svg, "right")[2] == "#2E7D3A"


def test_nothing_is_written_unless_it_is_asked_for():
    assert ">left</text>" not in _ring_figure().as_svg()


def test_the_name_sits_outside_the_ring_at_the_middle_of_its_band():
    figure = _ring_figure(labels=True)
    tips = {p.name: p for p in figure.geometry().tips}
    root = [p for p in figure.geometry().nodes if p.name == ""][0]   # the unnamed root, at the centre
    x, y, _ = _label(figure.as_svg(), "left")
    band = [tips[n] for n in "ABCD"]
    want = sum(math.atan2(t.y - root.y, t.x - root.x) for t in band) / len(band)
    got = math.atan2(y - root.y, x - root.x)
    assert math.cos(want - got) > 0.9, "pointing into the middle of its own band"
    assert (math.hypot(x - root.x, y - root.y)
            > max(math.hypot(t.x - root.x, t.y - root.y) for t in band)), "past the ring"


def test_a_dict_writes_something_else_and_skips_what_it_leaves_out():
    svg = _ring_figure(labels={"left": "Clade I"}).as_svg()
    assert ">Clade I</text>" in svg
    assert ">right</text>" not in svg and ">left</text>" not in svg


def test_a_value_in_two_places_is_named_on_each():
    """A band is a run of neighbouring tips. Naming the value once would put the name in the gap
    between its two bands."""
    split = {n: ("odd" if i % 2 else "even") for i, n in enumerate("ABCDEFGH")}
    svg = (plot(loads(_R_NWK), layout="radial", style=Style(width=560, height=520))
           + ring(split, palette={"odd": "#2B64A8", "even": "#2E7D3A"}, labels=True)).as_svg()
    assert svg.count(">odd</text>") == 4


def test_the_colour_can_be_set_instead():
    svg = _ring_figure(labels=True, label_color="#111111").as_svg()
    assert _label(svg, "left")[2] == "#111111"


# --- #72: naming the rows and columns of a page ---------------------------------------------------


def _grid(n_rows=2, n_cols=3):
    tree = loads("((A:1,B:1)x:1,(C:1,D:1)y:1)r;")
    return [[plot(tree, style=Style(width=200, height=140)) + tip_labels(size=7)
             for _ in range(n_cols)] for _ in range(n_rows)]


def test_a_flat_list_is_one_label_per_column():
    assert _spans(["a", "b", "c"], 3, "column") == [("a", 0, 0), ("b", 1, 1), ("c", 2, 2)]


def test_a_pair_says_how_many_it_covers():
    assert _spans([("ALE", 2), ("TEQUILA", 2)], 4, "row") == [("ALE", 0, 1), ("TEQUILA", 2, 3)]


def test_labels_that_do_not_cover_the_grid_are_refused():
    with pytest.raises(ValueError, match="cover 2 columns, but the grid has 3"):
        _spans(["a", "b"], 3, "column")


def test_a_span_of_less_than_one_is_refused():
    with pytest.raises(ValueError, match="spans at least one row"):
        _spans([("x", 0)], 1, "row")


def test_the_columns_and_rows_are_named():
    svg = ph.page(_grid(), width=760, col_labels=["one", "two", "three"],
                  row_labels=["first", "second"]).as_svg()
    for text in ("one", "two", "three", "first", "second"):
        assert f">{text}</text>" in svg


def test_a_column_label_is_centred_over_its_column():
    svg = ph.page(_grid(n_rows=1, n_cols=2), width=760, pad=20, gap=16,
                  col_labels=["one", "two"]).as_svg()
    placed = {text: float(x) for x, text in
              re.findall(r'<text x="([-\d.]+)"[^>]*>(one|two)</text>', svg)}
    cell_w = (760 - 40 - 16) / 2
    assert placed["one"] == pytest.approx(20 + cell_w / 2, abs=0.5)
    assert placed["two"] == pytest.approx(20 + cell_w + 16 + cell_w / 2, abs=0.5)


def test_a_row_label_is_turned_to_read_upwards():
    """Upright it would need a gutter as wide as the longest name, which is most of a cell."""
    svg = ph.page(_grid(), width=760, row_labels=["first", "second"]).as_svg()
    line = [ln for ln in svg.splitlines() if ">first</text>" in ln][0]
    assert "rotate(-90" in line


def test_a_spanning_row_label_sits_between_the_rows_it_covers():
    svg = ph.page(_grid(n_rows=4), width=760, row_labels=[("ALE", 2), ("TEQUILA", 2)]).as_svg()
    placed = {text: float(y) for y, text in
              re.findall(r'<text x="[-\d.]+" y="([-\d.]+)"[^>]*>(ALE|TEQUILA)</text>', svg)}
    assert placed["ALE"] < placed["TEQUILA"], "in the order the rows are in"


def test_the_grid_makes_room_for_the_labels():
    """Not drawn over the figures: the cells move right and down to clear them."""
    plain = ph.page(_grid(), width=760).as_svg()
    named = ph.page(_grid(), width=760, col_labels=["a", "b", "c"],
                    row_labels=["x", "y"]).as_svg()

    def first_cell(svg):
        found = re.search(r'<svg x="([-\d.]+)" y="([-\d.]+)"', svg)
        return float(found.group(1)), float(found.group(2))

    assert first_cell(named)[0] > first_cell(plain)[0], "the cells move right of the row labels"
    assert first_cell(named)[1] > first_cell(plain)[1], "and down below the column labels"


def test_an_unlabelled_page_is_what_it_was():
    cells = _grid()
    assert ph.page(cells, width=760).as_svg() == ph.page(cells, width=760, col_labels=None,
                                                         row_labels=None).as_svg()
