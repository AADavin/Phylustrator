"""Part of a label in italics (issue #74).

`gene 1 (Escherichia coli)` wants the species italic and the gene upright, and a label was written
in one style or the other. `*…*` marks the stretch.

The drawing is the awkward part. `<tspan>` is the obvious answer and is what the SVG should say,
but cairosvg anchors a label containing tspans by its *last* chunk alone — an end-anchored name
slides most of its own width to the right — and a tspan takes no transform, so a family with no
italic face of its own cannot be leaned the way `raw_text` leans a whole label. So each piece is
drawn as its own element at a measured offset, and the tspan form is kept for where nothing can be
measured.
"""

from __future__ import annotations

import math
import re

import pytest

from phylustrator import Style
from phylustrator.render import Canvas, can_measure_text, text_width
from phylustrator.trees import loads, node_labels, plot, tip_labels
from phylustrator.trees.layers.labels import split_markup

_NWK = "((a:1,b:1)x:0.5,(c:1,d:1)y:0.5)r;"
_LABELS = {"a": "gene 1 (*Escherichia coli*)", "b": "gene 2 (*Salmonella enterica*)"}


def _texts(svg):
    return [(float(x), text) for x, text in
            re.findall(r'<text x="([-\d.]+)"[^>]*>([^<]*)</text>', svg)]


# --- the markup -----------------------------------------------------------------------------------


def test_a_marked_stretch_becomes_its_own_italic_piece():
    assert split_markup("gene 1 (*Escherichia coli*)") == [
        ("gene 1 (", "normal"), ("Escherichia coli", "italic"), (")", "normal")]


def test_a_plain_label_is_one_piece():
    assert split_markup("plain") == [("plain", "normal")]


def test_the_whole_label_can_be_marked():
    assert split_markup("*all of it*") == [("all of it", "italic")]


def test_a_lone_mark_is_a_character():
    """A footnote mark or a significance star must not turn the rest of the name italic."""
    assert split_markup("a * b") == [("a * b", "normal")]
    assert split_markup("*unclosed") == [("*unclosed", "normal")]


def test_an_escaped_mark_is_written():
    assert split_markup(r"star\*here") == [("star*here", "normal")]


def test_several_stretches_alternate():
    assert split_markup("a*b*c*d*e") == [("a", "normal"), ("b", "italic"), ("c", "normal"),
                                         ("d", "italic"), ("e", "normal")]


def test_an_empty_piece_is_dropped():
    assert split_markup("**") == []
    assert split_markup("a**b") == [("a", "normal"), ("b", "normal")]


# --- the drawing ----------------------------------------------------------------------------------


def _canvas(width=400):
    return Canvas(Style(width=width, height=80), (0.0, 1.0), (0.0, 1.0))


_PIECES = [("gene 1 (", "normal"), ("Escherichia coli", "italic"), (")", "normal")]


def test_each_piece_is_drawn_as_its_own_element():
    canvas = _canvas()
    canvas.rich_text(20, 40, _PIECES)
    written = _texts(canvas.as_svg())
    assert [text for _, text in written] == ["gene 1 (", "Escherichia coli", ")"]


def test_the_pieces_are_laid_out_by_what_they_measure():
    """Spaced by the rough per-character guess they would be wrong by a factor of two on a run of
    narrow letters, and the closing bracket would sit inside the species name."""
    canvas = _canvas()
    canvas.rich_text(20, 40, _PIECES)
    placed = dict((text, x) for x, text in _texts(canvas.as_svg()))
    first = text_width("gene 1 (", family="Helvetica", size=12.0)
    assert placed["Escherichia coli"] == pytest.approx(20 + first, abs=0.01)


def test_the_width_it_reports_is_the_sum_of_the_pieces():
    canvas = _canvas()
    total = canvas.rich_text(20, 40, _PIECES)
    assert total == pytest.approx(sum(text_width(s, family="Helvetica", size=12.0, style=st)
                                      for s, st in _PIECES), abs=0.01)


@pytest.mark.parametrize("anchor", ["start", "end", "middle"])
def test_the_label_is_anchored_where_it_was_asked_to_be(anchor):
    """The bug this works around: cairosvg anchors a label of tspans by its last chunk alone, so an
    end-anchored name slid most of its own width to the right."""
    canvas = _canvas()
    total = canvas.rich_text(200, 40, _PIECES, anchor=anchor)
    placed = _texts(canvas.as_svg())
    left = min(x for x, _ in placed)
    want = {"start": 200.0, "end": 200.0 - total, "middle": 200.0 - total / 2}[anchor]
    assert left == pytest.approx(want, abs=0.01)


def test_one_piece_is_just_a_label():
    """No measuring, no splitting: the ordinary path, so an unmarked label is drawn as it was."""
    canvas = _canvas()
    canvas.rich_text(20, 40, [("plain", "normal")], anchor="end")
    line = [ln for ln in canvas.as_svg().splitlines() if "<text" in ln][0]
    assert 'text-anchor="end"' in line and 'x="20"' in line


def test_an_italic_piece_is_leaned_when_the_family_has_no_italic_face():
    """Helvetica ships an Oblique, not an Italic, so `font-style` is ignored in the PNG and the
    species name would come out upright — the whole point of #73, one piece at a time."""
    from phylustrator import render
    render._ITALIC_SEEN.clear()
    render._ITALIC_SEEN["Helvetica"] = False
    canvas = _canvas()
    canvas.rich_text(20, 40, _PIECES, family="Helvetica")
    lines = [ln for ln in canvas.as_svg().splitlines() if "<text" in ln]
    italic = [ln for ln in lines if ">Escherichia coli<" in ln][0]
    upright = [ln for ln in lines if ">gene 1 (<" in ln][0]
    assert "skewX" in italic and "font-style" not in italic
    assert "skewX" not in upright, "only the marked stretch leans"
    render._ITALIC_SEEN.clear()


def test_a_family_with_an_italic_face_is_asked_for_it_properly():
    from phylustrator import render
    render._ITALIC_SEEN.clear()
    render._ITALIC_SEEN["Times New Roman"] = True
    canvas = _canvas()
    canvas.rich_text(20, 40, _PIECES, family="Times New Roman")
    italic = [ln for ln in canvas.as_svg().splitlines() if ">Escherichia coli<" in ln][0]
    assert 'font-style="italic"' in italic and "skewX" not in italic
    render._ITALIC_SEEN.clear()


def test_without_a_way_to_measure_it_falls_back_to_tspans(monkeypatch):
    """Laid out by hand on a guess the pieces would be visibly mis-spaced; one element with tspans
    is spaced by the renderer. The anchoring bug it reintroduces is cairosvg's, and cairosvg is
    exactly what is missing in that case."""
    from phylustrator import render
    monkeypatch.setattr(render, "can_measure_text", lambda: False)
    canvas = _canvas()
    canvas.rich_text(20, 40, _PIECES)
    svg = canvas.as_svg()
    assert svg.count("<text") == 1
    assert '<tspan font-style="italic">Escherichia coli</tspan>' in svg


def test_the_text_is_escaped():
    canvas = _canvas()
    canvas.rich_text(20, 40, [("a & b", "normal"), ("<c>", "italic")])
    assert "&amp;" in canvas.as_svg()


# --- through the label layers ---------------------------------------------------------------------


def test_a_tip_label_sets_its_species_apart():
    svg = (plot(loads(_NWK), style=Style(width=560, height=300))
           + tip_labels(values=_LABELS, markup=True)).as_svg()
    written = [text for _, text in _texts(svg)]
    assert "Escherichia coli" in written and "gene 1 (" in written


def test_markup_is_off_unless_asked_for():
    """A label that already carries an asterisk must not be re-read."""
    labels = {"a": "clade *", "b": "other *"}
    svg = (plot(loads(_NWK)) + tip_labels(values=labels)).as_svg()
    assert ">clade *</text>" in svg


def test_a_node_label_takes_it_too():
    svg = (plot(loads(_NWK)) + node_labels(values={"x": "*Escherichia*"}, markup=True)).as_svg()
    assert ">Escherichia</text>" in svg


@pytest.mark.parametrize("layout", ["rectangular", "radial", "unrooted"])
def test_every_layout_writes_the_pieces(layout):
    """The round layouts turn their names, so the pieces have to turn with them."""
    svg = (plot(loads(_NWK), layout=layout, style=Style(width=560, height=400))
           + tip_labels(values=_LABELS, markup=True)).as_svg()
    assert ">Escherichia coli</text>" in svg


def test_a_turned_name_lays_its_pieces_out_along_itself():
    """Not along the page's x. A name on a radial tree's left side is written at 297 degrees, and
    its species would otherwise be placed due east of its genus while each piece faced south-west."""
    figure = (plot(loads(_NWK), layout="radial", style=Style(width=560, height=400))
              + tip_labels(values=_LABELS, markup=True))
    lines = [ln for ln in figure.as_svg().splitlines() if "<text" in ln]
    turned = [ln for ln in lines if ">Salmonella enterica<" in ln][0]
    genus = [ln for ln in lines if ">gene 2 (<" in ln][0]
    assert "rotate(" in turned, "the piece turns with the name"
    def place(line):
        found = re.search(r'<text x="([-\d.]+)" y="([-\d.]+)"', line)
        return float(found.group(1)), float(found.group(2))

    gx, gy = place(genus)
    sx, sy = place(turned)
    angle = math.degrees(math.atan2(sy - gy, sx - gx)) % 360
    turn = float(re.search(r"rotate\(([-\d.]+)", turned).group(1)) % 360
    assert abs(angle - turn) < 1.0, "the species follows the genus along the label's own direction"


def test_measuring_is_available_here():
    """If this fails the suite above is testing the fallback, not the path figures take."""
    assert can_measure_text()
