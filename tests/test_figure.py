"""Figure: the skeleton renders to SVG, and the stem shows up as one extra branch."""

import pytest

from phylustrator.trees import color_branches, color_lanes, loads, plot


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


def test_color_branches_dashed():
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    svg = (plot(tree) + color_branches({"A": 1.0, "B": 2.0, "C": 1.5, "D": 0.5}, dashed={"A", "B"})).as_svg()
    assert "stroke-dasharray" in svg   # coloured branches can still be dashed


def test_color_lanes_paints_two_traits():
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    names = ("A", "B", "C", "D", "R")
    x = {n: [("1", 1.0)] for n in names}          # trait X present everywhere
    y = {n: [("0", 1.0)] for n in names}          # trait Y absent everywhere
    svg = (plot(tree, skeleton=False)
           + color_lanes([(x, {"1": "#123456"}), (y, {"0": "#abcdef"})])).as_svg()
    assert "#123456" in svg and "#abcdef" in svg   # both lanes drawn


def test_color_lanes_needs_rectangular():
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    with pytest.raises(ValueError):
        (plot(tree, layout="radial") + color_lanes([({}, {})])).as_svg()


def test_composable_grammar_returns_new_figure():
    tree = loads("(A:1,B:1)R;")
    base = plot(tree)
    added = base + (lambda canvas, tree, layout, style: None)
    assert added is not base and len(added.layers) == len(base.layers) + 1


def test_every_colormap_runs_dark_to_light_and_is_sampled_end_to_end():
    """Each named map must be usable, and `colormap` must return its first and last anchor at the
    ends of the range — a map registered with too few anchors, or sampled off by one, would show up
    here rather than as a figure that is subtly the wrong colour."""
    from phylustrator.color import _COLORMAPS, colormap, colormap_hex

    assert set(_COLORMAPS) >= {"viridis", "magma", "cividis", "coolwarm"}
    for name, anchors in _COLORMAPS.items():
        assert len(anchors) >= 8, name
        sample = colormap(name)
        assert sample(0.0) == anchors[0] and sample(1.0) == anchors[-1], name
        assert len(colormap_hex(name)) == len(anchors)
        assert all(h.startswith("#") and len(h) == 7 for h in colormap_hex(name)), name
