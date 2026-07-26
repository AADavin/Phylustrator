"""Figure: the skeleton renders to SVG, and the stem shows up as one extra branch."""

import pytest

from phylustrator import color_branches, loads, plot


@pytest.mark.parametrize("layout", ["rectangular", "radial", "unrooted"])
def test_all_layouts_render_coloured(layout):
    tree = loads("((A:1,B:1)C:1,(D:1,E:1)F:1)R:2;")
    svg = (plot(tree, layout=layout)
           + color_branches({"A": 1.0, "B": 2.0, "D": 3.0, "E": 4.0})).as_svg()
    assert svg.lstrip().startswith("<") and "#" in svg


def test_plot_produces_svg():
    svg = plot(loads("((A:1,B:1)C:1,D:2)R;")).as_svg()
    assert svg.lstrip().startswith("<") and "#333333" in svg  # a branch was drawn


def test_stem_adds_one_branch():
    tree = loads("((A:1,B:1)C:1,D:2)R:3;")
    with_stem = plot(tree).as_svg().count("#333333")
    without = plot(tree, stem=False).as_svg().count("#333333")
    assert with_stem == without + 1


def test_dashed_branches():
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    assert "stroke-dasharray" in plot(tree, dashed={"A", "B", "C"}).as_svg()
    assert "stroke-dasharray" not in plot(tree).as_svg()  # none dashed by default


def test_composable_grammar_returns_new_figure():
    tree = loads("(A:1,B:1)R;")
    base = plot(tree)
    added = base + (lambda canvas, tree, layout, style: None)
    assert added is not base and len(added.layers) == len(base.layers) + 1
