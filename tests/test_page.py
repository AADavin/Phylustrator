"""Several figures on one page, as vectors (issues #17, #30 and #41).

`beside` and `below` each pair one tree with one companion panel, so two trees side by side — the
same tree under two analyses, the commonest comparison there is — had to leave the library and be
stitched together as images. `page` nests whole figures instead, each keeping its own layers and
style, and the page carries the title and the panel letters that belong to the figure as a whole.
"""

from __future__ import annotations

import re

import pytest

import phylustrator as ph
from phylustrator import Style
from phylustrator.trees import color_branches, loads, plot, tip_labels, title

_NWK = "((a:1,b:1)n1:2,(c:2,d:2)n2:1)root;"


def _tree(**kw):
    return plot(loads(_NWK), **kw) + tip_labels()


def _letters(svg):
    return re.findall(r'font-weight="bold"[^>]*>([A-Z])</text>', svg)


def _texts(svg):
    return [(float(m.group(1)), m.group(2)) for m in
            re.finditer(r'<text x="([-\d.]+)"[^>]*>([^<]*)</text>', svg)]


# --- two figures that are not a tree and a panel (issue #30) -----------------------------------


def test_two_trees_go_side_by_side():
    """`beside(left, right)` read the second tree as a genomes panel and raised AttributeError."""
    page = ph.page([[_tree(), _tree(layout="radial")]], width=700)
    assert page.as_svg().count("<svg x=") == 2


def test_each_figure_keeps_its_own_layers():
    page = ph.page([[_tree() + title("one"), _tree() + title("two")]], width=700)
    svg = page.as_svg()
    assert ">one</text>" in svg and ">two</text>" in svg


def test_a_flat_list_is_one_row():
    assert ph.page([_tree(), _tree()], width=700).as_svg().count("<svg x=") == 2


def test_an_empty_cell_leaves_a_gap():
    svg = ph.page([[_tree(), None]], width=700).as_svg()
    assert svg.count("<svg x=") == 1


# --- as vectors, not as a picture of a figure (issue #17) --------------------------------------


def test_a_page_nests_its_figures_as_vectors():
    """The point of the page: a journal gets a vector figure, not a picture of one."""
    svg = ph.page([[_tree(), _tree()]], width=700).as_svg()
    assert "image/png" not in svg
    assert svg.count("<text") > 4, "the tip labels are still text"


def test_beside_nests_its_tree_as_vectors_too():
    """It used to render the tree to a PNG and paste it in, which made half the composite a
    picture and needed cairosvg to build at all."""
    M = ph.genomes.Matrix(rows=["a", "b", "c", "d"], cols=["f1"], values=[[1], [0], [1], [0]])
    svg = ph.beside(_tree(), ph.genomes.heatmap(M), width=600).as_svg()
    assert "image/png" not in svg and "<svg x=" in svg


def test_two_figures_do_not_answer_to_each_other_s_gradients():
    """drawsvg numbers the ids in every figure from zero, so without renaming the second figure's
    gradients would resolve to the first one's and quietly draw the wrong colours."""
    values = {"a": 0.1, "b": 0.9, "c": 0.5, "d": 0.2}
    left = plot(loads(_NWK)) + color_branches(values, cmap="viridis", gradient=True)
    right = plot(loads(_NWK)) + color_branches(values, cmap="magma", gradient=True)
    svg = ph.page([[left, right]], width=700).as_svg()
    ids = re.findall(r'id="([^"]+)"', svg)
    assert ids and len(ids) == len(set(ids))
    pointed_at = set(re.findall(r"url\(#([^)]+)\)", svg))
    assert pointed_at and all(f'id="{name}"' in svg for name in pointed_at)


# --- the title and the letters belong to the page (issue #41) ----------------------------------


def test_the_title_is_centred_over_the_whole_page():
    """A title on a figure inside the page centres over that figure's own column: on a 45/55 split
    it sits left of the middle, which is what #41 hit."""
    width = 800
    svg = ph.page([[_tree(), _tree()]], width=width, title="Presence of three families").as_svg()
    x = next(x for x, text in _texts(svg) if text == "Presence of three families")
    assert x == pytest.approx(width / 2)


def test_a_composite_can_go_on_a_page():
    """#41 itself: a title over a beside() composite, which has no title of its own."""
    M = ph.genomes.Matrix(rows=["a", "b", "c", "d"], cols=["f1"], values=[[1], [0], [1], [0]])
    composite = ph.beside(_tree(), ph.genomes.heatmap(M), width=600)
    svg = ph.page([[composite]], width=640, title="Over the whole thing").as_svg()
    assert ">Over the whole thing</text>" in svg
    assert svg.count("<svg x=") >= 2, "the composite, and the tree nested inside it"


def test_letters_run_in_reading_order():
    svg = ph.page([[_tree(), _tree()], [_tree(), _tree()]], width=700, letters=True).as_svg()
    assert _letters(svg) == ["A", "B", "C", "D"]


def test_letters_can_be_given_outright():
    svg = ph.page([[_tree(), _tree()]], width=700, letters="XY").as_svg()
    assert _letters(svg) == ["X", "Y"]


def test_an_empty_cell_does_not_eat_a_letter():
    """A gap in the page is not a panel, and the panel after it is still B."""
    svg = ph.page([[None, _tree()], [_tree(), None]], width=700, letters=True).as_svg()
    assert _letters(svg) == ["A", "B"]


def test_no_letters_unless_they_are_asked_for():
    assert _letters(ph.page([[_tree(), _tree()]], width=700).as_svg()) == []


# --- a page a journal can measure --------------------------------------------------------------


def test_a_page_can_be_sized_in_points():
    """A journal asks for one column wide, and a pixel is not a width you can promise."""
    svg = ph.page([[_tree()]], width=482, units="pt").as_svg()
    assert 'width="482pt"' in svg
    assert 'viewBox="0 0 482' in svg, "the drawing underneath stays in pixels"


def test_the_units_have_to_be_units():
    with pytest.raises(ValueError, match="units must be one of"):
        ph.page([[_tree()]], width=482, units="furlongs")


def test_pixels_are_the_default_and_write_no_unit():
    svg = ph.page([[_tree()]], width=400).as_svg()
    assert re.search(r'width="400(\.0)?"', svg)


# --- the shape of the page ----------------------------------------------------------------------


def test_a_fixed_height_shares_itself_between_the_rows():
    page = ph.page([[_tree()], [_tree()]], width=600, height=500)
    assert 'height="500"' in page.as_svg() or 'height="500.0"' in page.as_svg()


def test_without_a_height_the_page_grows_to_fit():
    one = ph.page([[_tree()]], width=600).as_svg()
    two = ph.page([[_tree()], [_tree()]], width=600).as_svg()
    heights = [float(re.search(r'height="([\d.]+)"', s).group(1)) for s in (one, two)]
    assert heights[1] > heights[0]


def test_a_figure_is_redrawn_at_its_cell_size_not_scaled_into_it():
    """Scaling the drawing would scale the text with it, so two cells of different widths would
    carry two different type sizes."""
    svg = ph.page([[_tree(style=Style(width=900, height=700))]], width=400).as_svg()
    inner = re.search(r'<svg x="[\d.]+" y="[\d.]+" [^>]*width="([\d.]+)"', svg)
    assert float(inner.group(1)) < 400, "the figure was re-rendered into the cell"
    assert "scale(" not in svg


def test_the_page_saves_like_any_figure(tmp_path):
    out = ph.page([[_tree(), _tree()]], width=600, title="A page").save(tmp_path / "page.svg")
    assert out.exists() and out.read_text().count("<svg x=") == 2
