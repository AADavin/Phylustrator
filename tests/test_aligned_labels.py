"""Tip labels written in one column, with leaders (issue #75).

On a tree drawn to scale the tips are ragged, so the names are too. `align_tips` lines them up by
drawing the terminal branches longer than they are, which is a lie about the one thing a phylogram
is for. `aligned=True` moves the **names** instead and joins each shorter tip to its own with a thin
dotted leader, which is how a phylogram is usually labelled.
"""

from __future__ import annotations

import re

import pytest

from phylustrator import Style
from phylustrator.trees import loads, plot, tip_labels

_NWK = "(((A:1,B:1)ab:1,(C:1,D:1)cd:1)abcd:1,(E:1,F:1)ef:1)r;"   # E and F end one unit short
_STYLE = Style(width=480, height=300, margin=45)


def _figure(orientation="right", **kw):
    return plot(loads(_NWK), stem=False, style=_STYLE, orientation=orientation, **kw)


def _written(svg):
    return {text: (float(x), float(y)) for x, y, text in
            re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]+)</text>', svg)}


def _leaders(svg):
    return re.findall(r'<path d="M ([-\d.]+),([-\d.]+) L ([-\d.]+),([-\d.]+)"[^>]*'
                      r'stroke-dasharray="1,3"', svg)


# --- the names line up, the branches do not move --------------------------------------------------


def test_every_name_is_written_in_one_column():
    names = _written((_figure() + tip_labels(aligned=True)).as_svg())
    xs = {round(p[0], 3) for name, p in names.items() if name in set("ABCDEF")}
    assert len(xs) == 1, "one column"


def test_the_names_are_ragged_without_it():
    names = _written((_figure() + tip_labels()).as_svg())
    xs = {round(p[0], 3) for name, p in names.items() if name in set("ABCDEF")}
    assert len(xs) == 2, "A-D at one depth, E and F one unit short"


def test_the_short_branches_keep_their_length():
    """The whole point: `align_tips` would have drawn E and F a unit longer than they are."""
    plain = {p.name: p.x for p in _figure().geometry().tips}
    aligned = {p.name: p.x for p in (_figure() + tip_labels(aligned=True)).geometry().tips}
    assert aligned == plain
    assert aligned["E"] < aligned["A"], "still short, as the tree says"


def test_the_column_stands_past_the_furthest_tip():
    figure = _figure() + tip_labels(aligned=True, offset=6.0)
    tips = {p.name: p for p in figure.geometry().tips}
    names = _written(figure.as_svg())
    assert names["E"][0] == pytest.approx(tips["A"].x + 6.0, abs=0.01)


# --- the leaders ----------------------------------------------------------------------------------


def test_a_short_tip_is_joined_to_its_name():
    svg = (_figure() + tip_labels(aligned=True)).as_svg()
    assert len(_leaders(svg)) == 2, "one each for E and F, which are the only short tips"


def test_a_tip_already_at_the_column_gets_no_leader():
    """A leader with nowhere to go is a dash sitting on the tip."""
    svg = (plot(loads("((A:1,B:1)x:1,(C:1,D:1)y:1)r;"), stem=False, style=_STYLE)
           + tip_labels(aligned=True)).as_svg()
    assert _leaders(svg) == [], "an ultrametric tree needs none"


def test_a_leader_runs_from_its_own_tip_to_its_own_name():
    figure = _figure() + tip_labels(aligned=True)
    tips = {p.name: p for p in figure.geometry().tips}
    svg = figure.as_svg()
    rows = {round(float(y1)): (float(x1), float(x2)) for x1, y1, x2, _ in _leaders(svg)}
    assert round(tips["E"].y) in rows
    start, end = rows[round(tips["E"].y)]
    assert start > tips["E"].x, "starting clear of the tip, not on it"
    assert end < _written(svg)["E"][0], "and stopping before the glyphs"


def test_the_leaders_can_be_left_out():
    svg = (_figure() + tip_labels(aligned=True, leader=False)).as_svg()
    assert _leaders(svg) == []
    assert ">E</text>" in svg, "the names are still in the column"


def test_the_leaders_take_their_look():
    svg = (_figure() + tip_labels(aligned=True, leader_color="#c1443c", leader_width=2.0,
                                  leader_dash="4,2")).as_svg()
    assert 'stroke="#c1443c"' in svg and 'stroke-dasharray="4,2"' in svg


# --- the other orientations, and the layouts that cannot ------------------------------------------


@pytest.mark.parametrize("orientation", ["right", "left", "down", "up"])
def test_it_follows_the_tree_round(orientation):
    figure = _figure(orientation) + tip_labels(aligned=True)
    names = _written(figure.as_svg())
    axis = 0 if orientation in ("right", "left") else 1
    placed = {round(p[axis], 3) for name, p in names.items() if name in set("ABCDEF")}
    assert len(placed) == 1, f"{orientation}: one column"
    assert len(_leaders(figure.as_svg())) == 2


def test_a_round_layout_says_why_it_cannot():
    for layout in ("radial", "unrooted"):
        with pytest.raises(ValueError, match="tips end along a line"):
            (plot(loads(_NWK), layout=layout) + tip_labels(aligned=True)).as_svg()


# --- it works with the rest of the figure ---------------------------------------------------------


def test_the_automatic_margin_measures_the_column_and_not_the_tips():
    """The names stand further right than any tip, so a margin measured at the tips would cut
    them off — which is the bug #60 fixed, reached a different way."""
    long_names = {name: f"{name} a rather long name indeed" for name in "ABCDEF"}
    figure = _figure() + tip_labels(aligned=True, values=long_names, size=9)
    ends = [x + len(text) * 9 * 0.58 for text, (x, _) in _written(figure.as_svg()).items()]
    assert max(ends) <= _STYLE.width + 0.5


def test_it_is_off_unless_asked_for():
    tree = loads(_NWK)
    assert (plot(tree, stem=False, style=_STYLE) + tip_labels()).as_svg() == (
        plot(tree, stem=False, style=_STYLE) + tip_labels(aligned=False)).as_svg()
