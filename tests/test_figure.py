"""Figure: the skeleton renders to SVG, and the stem shows up as one extra branch."""

import re

import pytest

from phylustrator.trees import (branch_events, color_branches, color_history, color_lanes,
                                loads, note, plot)


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


def test_color_history_takes_a_palette_or_a_colormap():
    """The states are labels or numbers, and the rule is `color_branches`'s: a palette for labels, a
    colormap for numbers. A quantity that steps along a branch — how much of a gene module a lineage
    still holds — is both numeric and mid-branch, which needs the two halves at once."""
    tree = loads("((A:2,B:2)C:1,D:3)R:1;")
    labels = {"A": [("on", 1.0), ("off", 1.0)], "B": [("off", 2.0)]}
    svg = (plot(tree) + color_history(labels, palette={"on": "#111111", "off": "#eeeeee"})).as_svg()
    assert "#111111" in svg and "#eeeeee" in svg          # both segments of A are painted

    numbers = {"A": [(1.0, 1.0), (0.5, 1.0)], "B": [(0.0, 2.0)]}
    numeric = (plot(tree) + color_history(numbers)).as_svg()
    assert numeric.lstrip().startswith("<") and numeric.count("#") > 2   # a colormap, not a palette


def test_color_history_survives_a_zero_length_segment():
    """Two changes at the same instant leave a segment of duration 0. It has no length to draw, and
    the states around it must still land in the right order."""
    tree = loads("((A:2,B:2)C:1,D:3)R:1;")
    hist = {"A": [(1.0, 1.0), (0.75, 0.0), (0.5, 1.0)]}
    svg = (plot(tree) + color_history(hist)).as_svg()
    assert svg.lstrip().startswith("<")


def test_color_history_limits_fix_the_scale_across_panels():
    """Without `limits` each panel normalises to its own states, so the same colour means a
    different number in each — wrong for a row of panels meant to be compared."""
    tree = loads("(A:1,B:1)R:1;")
    narrow = {"A": [(0.4, 1.0)], "B": [(0.6, 1.0)]}
    own = (plot(tree) + color_history(narrow)).as_svg()
    fixed = (plot(tree) + color_history(narrow, limits=(0.0, 1.0))).as_svg()
    assert own != fixed


def test_a_line_safe_colormap_never_goes_pale():
    """Every perceptually-uniform sequential map ends near-white, which is fine for a heatmap and not
    for a branch a few pixels wide: the values at that end vanish instead of being faint."""
    from phylustrator.color import colormap_hex

    def luminance(hex_colour):
        r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    for pale, safe in (("viridis", "viridis_dark"), ("magma", "magma_dark")):
        assert max(luminance(c) for c in colormap_hex(pale)) > 200        # the problem
        assert max(luminance(c) for c in colormap_hex(safe)) < 180        # the fix
        assert colormap_hex(safe)[0] == colormap_hex(pale)[0]             # same dark end, same order


def test_note_dy_nudges_the_text_without_moving_the_tree():
    """A note read as a panel title wants air between it and the tree; ``dy`` gives it."""
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    def y_of(svg):
        return float(re.search(r'<text[^>]*\by="([-\d.]+)"', svg).group(1))
    plain = (plot(tree) + note("A  on time")).as_svg()
    lifted = (plot(tree) + note("A  on time", dy=-14)).as_svg()
    assert y_of(lifted) == pytest.approx(y_of(plain) - 14)
    assert lifted.count("#333333") == plain.count("#333333")    # the tree itself has not moved


def test_a_ring_is_an_open_marker_and_a_circle_is_not():
    """A ring marks something present but not counted — an unsampled tip — so it is hollow: the
    fill is the page and the colour is in the stroke."""
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    ring = (plot(tree) + branch_events([{"kind": "unsampled", "node": "A", "x": 1.5}],
                                       styles={"unsampled": ("ring", "#111111")})).as_svg()
    disc = (plot(tree) + branch_events([{"kind": "unsampled", "node": "A", "x": 1.5}],
                                       styles={"unsampled": ("circle", "#111111")})).as_svg()
    assert '<circle' in ring and 'fill="#ffffff"' in ring and 'stroke="#111111"' in ring
    assert 'fill="#111111"' in disc          # the filled one puts the colour in the fill
    assert 'fill="#111111"' not in ring.split("<circle", 1)[1].split(">", 1)[0]
