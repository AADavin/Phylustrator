"""The automatic margin — room for what the layers write past the panel (issue #60).

A side of the margin left at ``None`` is **automatic**: it never comes out narrower than ``margin``,
and grows when something would otherwise be drawn off the page. A side given a number is that
number. Only the layer that wrote the text knows how wide it came out, so the measuring is done by
drawing the figure and reading back what it claimed.
"""

from __future__ import annotations

import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.render import text_width
from phylustrator.trees import (
    color_branches,
    legend,
    loads,
    plot,
    tip_labels,
)

_NWK = "((A:0.3,B:0.4)ab:0.2,(C:0.3,D:1.9)cd:0.5)r;"
_LONG = {"A": "A short name", "B": "B short name", "C": "C short name",
         "D": "D a much longer tip label · with a second part"}


def _texts(svg):
    """Every label as (x, text)."""
    return [(float(x), text) for x, text in
            re.findall(r'<text x="([-\d.]+)"[^>]*>([^<]+)</text>', svg)]


def _wide(text, size):
    """How wide a label comes out, measured the way the layer measures it."""
    return text_width(text, family="Helvetica", size=size)


def _right_end(figure, size):
    """How far right the widest label reaches."""
    return max(x + _wide(text, size) for x, text in _texts(figure.as_svg()))


# --- the bug in the issue -------------------------------------------------------------------------


def test_a_long_tip_label_is_not_cut_off_at_the_right_edge():
    """The figure in the issue: the label of D, on the longest branch, ran off the page."""
    figure = plot(loads(_NWK)) + tip_labels(values=_LONG, size=9)
    assert _right_end(figure, 9) <= figure.style.width + 0.5


def test_the_margin_a_pinned_figure_was_given_is_the_margin_it_gets():
    """A number means that number — a figure that wants the panel exactly where it put it says so,
    and keeps the clipping if that is what it asked for."""
    style = Style(margin_right=50)
    figure = plot(loads(_NWK), style=style) + tip_labels(values=_LONG, size=9)
    assert figure._fitted_style() is style
    assert _right_end(figure, 9) > style.width, "pinned, so nothing made room for it"


def test_a_figure_that_already_fits_does_not_move_by_a_pixel():
    """Growth happens only when something would be drawn off the page, so every figure whose
    labels already fit comes out exactly as it did before."""
    tree = loads(_NWK)
    plain = plot(tree, style=Style(width=800, height=400, margin=50))
    assert (plain + tip_labels()).as_svg() == (
        plot(tree, style=Style(width=800, height=400, margin=50, margin_right=50))
        + tip_labels()).as_svg()


def test_the_margin_never_comes_out_narrower_than_the_one_asked_for():
    """Automatic is a floor, not a free hand: a figure with nothing past the tips keeps its 90."""
    style = Style(width=700, height=300, margin=90)
    figure = plot(loads(_NWK), style=style) + tip_labels()
    assert figure._fitted_style().margin_at("right") == pytest.approx(90.0)


# --- it is the same page the geometry reports -----------------------------------------------------


def test_geometry_reports_the_page_the_drawing_used():
    """A companion panel lines itself up from `geometry()`. Measured against margins the drawing
    never used, every panel under a tree with long names would be out by the difference."""
    figure = plot(loads(_NWK)) + tip_labels(values=_LONG, size=9, offset=6.0)
    written = dict((text, x) for x, text in _texts(figure.as_svg()))
    for tip in figure.geometry().tips:
        assert written[_LONG[tip.name]] == pytest.approx(tip.x + 6.0, abs=0.01)


def test_the_drawn_tree_ends_where_the_geometry_says_it_does():
    """The same thing read off the branches rather than the names."""
    figure = plot(loads(_NWK)) + tip_labels(values=_LONG, size=9)
    ends = [float(x) for x, _ in
            re.findall(r'L([-\d.]+),([-\d.]+)" stroke="#333333"', figure.as_svg())]
    assert figure.geometry().tip_x == pytest.approx(max(ends), abs=0.01)


def test_a_clade_box_is_measured_on_the_same_page_too():
    """`clade_box` lays out the zoom lines before anything is drawn; on a different page they point
    at nothing."""
    figure = plot(loads(_NWK)) + tip_labels(values=_LONG, size=9)
    box = figure.clade_box("cd")
    tips = {p.name: p for p in figure.geometry().tips}
    assert box.x1 >= tips["D"].x - 1.0, "the box reaches its own tip"
    assert box.x1 <= figure.style.width


# --- what it costs, and where it stops ------------------------------------------------------------


def test_a_figure_with_no_layers_is_never_measured():
    """The measuring is a drawing, so a figure with nothing to measure does not pay for one."""
    style = Style(width=400, height=300)
    assert plot(loads(_NWK), style=style)._fitted_style() is style


def test_the_fit_is_measured_once_and_remembered():
    figure = plot(loads(_NWK)) + tip_labels(values=_LONG, size=9)
    first = figure._fitted_style()
    assert figure._fitted_style() is first
    assert figure.as_svg() == figure.as_svg()


def test_adding_a_layer_measures_the_new_figure_not_the_old_one():
    """`+` returns a new figure, so the remembered fit must not travel with it."""
    base = plot(loads(_NWK)) + tip_labels()
    narrow = base._fitted_style().margin_at("right")
    wide = (plot(loads(_NWK)) + tip_labels(values=_LONG, size=9))._fitted_style().margin_at("right")
    assert wide > narrow


@pytest.mark.parametrize("layout", ["radial", "unrooted"])
def test_a_round_layout_gets_room_on_whichever_side_it_needs_it(layout):
    """Radial and unrooted names point outward on every side, so the fit has to work on all four.
    It used to have nothing to go on at all (issue #89) and the names ran off the page."""
    style = Style(width=500, height=500, margin=40)
    figure = plot(loads(_NWK), layout=layout, style=style) + tip_labels(values=_LONG, size=9)
    fitted = figure._fitted_style()
    assert max(fitted.margin_at(side) for side in ("left", "right", "top", "bottom")) > 40.0
    assert min(fitted.margin_at(side) for side in ("left", "right", "top", "bottom")) >= 40.0


@pytest.mark.parametrize("layout", ["radial", "unrooted"])
def test_a_round_tree_s_names_all_land_on_the_page(layout):
    style = Style(width=500, height=500, margin=40)
    figure = plot(loads(_NWK), layout=layout, style=style) + tip_labels(values=_LONG, size=9)
    for x, text in _texts(figure.as_svg()):
        assert -0.5 <= x <= style.width + 0.5, f"{text!r} is anchored off the page"


# --- the key that no longer needs a margin by hand ------------------------------------------------

_KINDS = {"A": "one", "B": "one", "C": "two", "D": "two", "ab": "one", "cd": "two"}
_PALETTE = {"one": "#0072B2", "two": "#D55E00"}
_KEY_TEXT = {"clade", "one", "two"}


def _keyed(style, *layers):
    figure = (plot(loads(_NWK), style=style)
              + color_branches(_KINDS, palette=_PALETTE) + tip_labels())
    for layer in layers:
        figure = figure + layer
    return figure


def test_a_key_outside_the_panel_is_given_room_rather_than_warned_about():
    """Before this, a key asked to sit beside the figure ran off the page and said which
    `margin_right=` to set; left automatic, the panel narrows until it fits (#67)."""
    style = Style(width=560, height=360, margin=40)
    figure = _keyed(style, legend("clade", loc="right"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        svg = figure.as_svg()
    entries = [x for x, text in _texts(svg) if text in _KEY_TEXT]
    assert entries, "the key is drawn"
    assert max(entries) < style.width, "and starts on the page"


def test_the_key_still_stays_outside_the_panel_it_made_room_for():
    """Growing the margin must not let the key slide back over the tip names: the two settle on
    each other, the names ending before the key starts."""
    style = Style(width=560, height=360, margin=40)
    svg = _keyed(style, legend("clade", loc="right")).as_svg()
    entries = [x for x, text in _texts(svg) if text in _KEY_TEXT]
    names = [x for x, text in _texts(svg) if text in set("ABCD")]
    assert max(names) < min(entries), "the key starts past the longest tip label"


def test_a_key_and_long_names_both_get_room():
    style = Style(width=700, height=360, margin=40)
    figure = (plot(loads(_NWK), style=style)
              + color_branches(_KINDS, palette=_PALETTE)
              + tip_labels(values=_LONG, size=9)
              + legend("clade", loc="right"))
    svg = figure.as_svg()
    names = max(x + _wide(text, 9) for x, text in _texts(svg) if text in _LONG.values())
    key = min(x for x, text in _texts(svg) if text in _KEY_TEXT)
    assert names <= key + 0.5, "the names stop before the key"
    assert key < style.width
