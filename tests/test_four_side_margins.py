"""#89: tip names that spill off the page, on a round tree and on a turned one.

A radial or unrooted tree writes its names outward in every direction; a ``"down"`` tree centres
them under its tips, so the first and the last reach past the panel sideways. Neither claimed a
margin, and the round branch recorded no obstacle either, so the names ran off the page and a key
could be dropped on top of them. The claim protocol itself only had ``"right"`` and ``"bottom"``.
"""

from __future__ import annotations

import math
import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.render import OUTWARD, Canvas, text_width
from phylustrator.trees import (
    color_branches,
    legend,
    loads,
    plot,
    ring,
    tip_labels,
    tip_track,
)

_NWK = ("((Aaaaaaaaaaaaaaaaaaaa:1,Bbbbbbbbbbbbbbbbbbbb:1)x:1,"
        "(Cccccccccccccccccccc:1,Dddddddddddddddddddd:1)y:1)r;")
_SMALL = "((A:1,B:1)x:1,(C:1,D:1)y:1)r;"
_STYLE = Style(width=360, height=360, margin=30)
_SIDES = ("left", "right", "top", "bottom")


def _labels(svg):
    """Every drawn label as (x, y, text, rotation in degrees, text-anchor)."""
    out = []
    for tag in re.findall(r"<text [^>]*>[^<]*</text>", svg):
        x = float(re.search(r'\bx="([-\d.]+)"', tag).group(1))
        y = float(re.search(r'\by="([-\d.]+)"', tag).group(1))
        turn = re.search(r"rotate\(([-\d.]+)", tag)
        place = re.search(r'text-anchor="([a-z]+)"', tag)
        text = re.search(r">([^<]*)</text>", tag).group(1)
        out.append((x, y, text, float(turn.group(1)) if turn else 0.0,
                    place.group(1) if place else "start"))
    return out


def _ends(x, y, text, turn, place, size):
    """Both ends of a label on the page: it runs along its own direction, from wherever its anchor
    puts it. Read off the SVG the renderer wrote, so this does not just restate `label_box`."""
    wide = text_width(text, family="Helvetica", size=size)
    first = {"start": 0.0, "end": -wide, "middle": -wide / 2}[place]
    ux, uy = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    return [(x + run * ux, y + run * uy) for run in (first, first + wide)]


def _margins(figure):
    fitted = figure._fitted_style()
    return {side: fitted.margin_at(side) for side in _SIDES}


# --- the claim protocol ---------------------------------------------------------------------------

def test_every_side_can_be_claimed():
    canvas = Canvas(Style(), (0.0, 1.0), (0.0, 1.0))
    for side in _SIDES:
        canvas.claim(side, 123.0)
        assert canvas.claimed(side, 0.0) == 123.0


def test_furthest_means_away_from_the_panel_whichever_side_it_is():
    canvas = Canvas(Style(), (0.0, 1.0), (0.0, 1.0))
    for side in _SIDES:
        canvas.claim(side, 100.0)
        canvas.claim(side, 200.0)
    assert canvas.claimed("right", 0.0) == 200.0 and canvas.claimed("bottom", 0.0) == 200.0
    assert canvas.claimed("left", 0.0) == 100.0 and canvas.claimed("top", 0.0) == 100.0


def test_the_sides_are_named_the_way_the_page_is_laid_out():
    assert OUTWARD == {"left": -1, "top": -1, "right": 1, "bottom": 1}


# --- the figure in the issue ----------------------------------------------------------------------

@pytest.mark.parametrize("layout", ["radial", "unrooted"])
def test_a_round_tree_s_names_stop_before_the_page_edge(layout):
    figure = plot(loads(_NWK), layout=layout, style=_STYLE) + tip_labels()
    page = (_STYLE.width, _STYLE.height)
    for x, y, text, turn, place in _labels(figure.as_svg()):
        for px, py in _ends(x, y, text, turn, place, _STYLE.font_size):
            assert -1.0 <= px <= page[0] + 1.0, f"{text!r} runs off the page sideways"
            assert -1.0 <= py <= page[1] + 1.0, f"{text!r} runs off the page vertically"


@pytest.mark.parametrize("layout", ["radial", "unrooted"])
def test_a_round_tree_grows_a_side_the_old_fit_could_not_reach(layout):
    """The point of the four-side claim: a name at 12 o'clock or at 9 needs top or left, and
    neither could be asked for before."""
    grown = {side for side, value in _margins(plot(loads(_NWK), layout=layout, style=_STYLE)
                                              + tip_labels()).items() if value > _STYLE.margin}
    assert grown & {"left", "top"}, f"only {sorted(grown)} grew"


def test_a_radial_tree_with_names_all_round_it_grows_on_all_four():
    grown = {side for side, value in _margins(plot(loads(_NWK), layout="radial", style=_STYLE)
                                              + tip_labels()).items() if value > _STYLE.margin}
    assert grown == set(_SIDES)


def test_a_turned_tree_gets_room_for_its_outermost_names():
    """A "down" tree centres each name under its tip, so the first and the last hang off the sides
    and no amount of right-and-bottom fitting could help."""
    figure = (plot(loads(_NWK), orientation="down", style=_STYLE) + tip_labels())
    margins = _margins(figure)
    assert margins["left"] > _STYLE.margin and margins["right"] > _STYLE.margin
    for x, y, text, turn, place in _labels(figure.as_svg()):
        assert place == "middle", "a down tree centres its names under the tips"
        for px, _ in _ends(x, y, text, turn, place, _STYLE.font_size):
            assert -1.0 <= px <= _STYLE.width + 1.0, f"{text!r} hangs off the side"


# --- what must not change -------------------------------------------------------------------------

def test_a_figure_that_already_fits_keeps_every_margin():
    figure = plot(loads(_SMALL), layout="radial", style=_STYLE) + tip_labels()
    assert _margins(figure) == dict.fromkeys(_SIDES, _STYLE.margin)


def test_a_pinned_side_is_left_where_it_was_put():
    style = Style(width=360, height=360, margin=30, margin_left=12, margin_top=12)
    figure = plot(loads(_NWK), layout="radial", style=style) + tip_labels()
    margins = _margins(figure)
    assert (margins["left"], margins["top"]) == (12, 12)
    assert margins["right"] > 30, "the automatic sides still grow"


def test_a_name_wider_than_the_page_does_not_squeeze_the_panel_away():
    """Two opposite sides growing at once would eat each other; each stops at the cap instead."""
    from phylustrator.trees.figure import _FIT_CAP

    huge = loads("(" + ",".join(f"{'W' * 90}{n}:1" for n in "AB") + ");")
    figure = plot(huge, layout="radial", style=_STYLE) + tip_labels()
    margins = _margins(figure)
    assert max(margins.values()) <= _FIT_CAP * 360 + 0.5
    assert _STYLE.width - margins["left"] - margins["right"] > 0, "a panel is left to draw in"


def test_a_key_beside_the_figure_still_starts_at_the_panel_edge():
    """A turned tree's names are claimed on the right as well, but they sit *inside* the panel, and
    a key placed outside it must not be pulled in to meet them."""
    style = Style(width=640, height=420, margin=40, margin_right=120)
    figure = (plot(loads(_SMALL), orientation="down", style=style)
              + color_branches({"A": "one", "B": "one", "C": "two", "D": "two"},
                               palette={"one": "#0072B2", "two": "#D55E00"})
              + tip_labels() + legend("clade", loc="right"))
    key = min(x for x, _, text, *_ in _labels(figure.as_svg()) if text in {"clade", "one", "two"})
    assert key >= style.width - 120, "the key is outside the panel, where it was asked to be"


# --- the obstacle the round branch never recorded ---------------------------------------------------

def test_a_corner_key_now_knows_it_is_sitting_on_a_round_tree_s_names():
    style = Style(width=420, height=420, margin=70)
    figure = (plot(loads(_NWK), layout="radial", style=style) + tip_labels()
              + color_branches({"Aaaaaaaaaaaaaaaaaaaa": "one"}, palette={"one": "#0072B2"})
              + legend("clade", loc="top-left"))
    with warnings.catch_warnings(record=True) as said:
        warnings.simplefilter("always")
        figure.as_svg()
    assert any("tip label" in str(w.message) for w in said), "it used to have no way to know"


# --- the chips past the tips ------------------------------------------------------------------------

def test_a_round_tree_s_chips_get_room_on_every_side():
    style = Style(width=300, height=300, margin=6)
    values = dict.fromkeys("ABCD", 1.0)
    figure = (plot(loads(_SMALL), layout="radial", style=style)
              + tip_track(values, size=26, offset=22))
    margins = _margins(figure)
    assert max(margins.values()) > 6, "a chip pushed past the page asks for room"


def test_a_ring_s_band_name_asks_for_room_of_its_own():
    """It sits outside the ring, which is outside everything else on the figure."""
    style = Style(width=300, height=300, margin=8)
    sides = {"A": "a long band name", "B": "a long band name",
             "C": "another one", "D": "another one"}
    figure = (plot(loads(_SMALL), layout="radial", style=style)
              + ring(sides, palette={"a long band name": "#2B64A8", "another one": "#2E7D3A"},
                     labels=True))
    assert max(_margins(figure).values()) > 8
    for x, y, text, turn, place in _labels(figure.as_svg()):
        for px, _ in _ends(x, y, text, turn, place, style.font_size * 0.95):
            assert -1.0 <= px <= style.width + 1.0, f"{text!r} is off the page"


# --- the box itself ---------------------------------------------------------------------------------

def test_a_turned_label_s_box_follows_the_text_and_not_the_page():
    from phylustrator.render import label_box

    flat = label_box(100.0, 100.0, 40.0, 10.0, anchor="start")
    assert flat == (100.0, 95.0, 140.0, 105.0)
    up = label_box(100.0, 100.0, 40.0, 10.0, anchor="start", rotate=-90.0)
    assert up == pytest.approx((95.0, 60.0, 105.0, 100.0))


def test_the_anchor_says_which_side_of_the_point_the_text_lies():
    from phylustrator.render import label_box

    at = dict(wide=40.0, tall=10.0)
    assert label_box(100.0, 100.0, anchor="end", **at)[0] == pytest.approx(60.0)
    assert label_box(100.0, 100.0, anchor="middle", **at)[0] == pytest.approx(80.0)
    assert label_box(100.0, 100.0, anchor="start", **at)[2] == pytest.approx(140.0)
