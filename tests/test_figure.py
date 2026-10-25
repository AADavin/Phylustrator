"""Figure: the skeleton renders to SVG, and the stem shows up as one extra branch."""

import math
import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.trees import (
    branch_events,
    color_branches,
    color_history,
    color_lanes,
    colorbar,
    highlight_lineage,
    legend,
    lineage,
    loads,
    node_labels,
    note,
    plot,
    rubberband,
    scale_bar,
    time_axis,
    time_marker,
    tip_labels,
    tip_track,
    title,
)


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


def test_a_coloured_branch_keeps_the_dash_the_figure_gave_it():
    """`plot(dashed=…)` survives a colouring layer drawn over it.

    A colouring layer overdraws the skeleton, so before it knew about the figure's `dashed` it
    painted extinct lineages solid — a run's dead branches quietly becoming survivors in every
    coloured figure. The layer's own `dashed=` still wins when it is given one."""
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    values = {"A": 0.0, "B": 1.0, "C": 0.5, "D": 0.2, "R": 0.4}
    dashes = (plot(tree, dashed={"D"}) + color_branches(values)).as_svg()
    none = (plot(tree) + color_branches(values)).as_svg()
    assert "stroke-dasharray" in dashes
    assert "stroke-dasharray" not in none
    # the layer's own set still wins. With the skeleton off, nothing else can draw a dash, so what
    # is left in the SVG is the colouring layer's own doing
    both = (plot(tree, dashed={"D"}, skeleton=False) + color_branches(values)).as_svg()
    override = (plot(tree, dashed={"D"}, skeleton=False)
                + color_branches(values, dashed=set())).as_svg()
    assert "stroke-dasharray" in both
    assert "stroke-dasharray" not in override


def test_a_key_clears_the_tree_behind_it():
    """A colorbar or a legend is drawn inside the plot, so it paints the page colour behind itself.

    Without it a branch runs under the letters and neither is readable — which is what a tall stem
    does to a top-left key on any tree deep enough to reach the corner."""
    tree = loads("((A:1,B:1)C:1,D:2)R;")
    bar = (plot(tree) + color_branches({"A": 0.0, "B": 1.0, "C": 0.5, "D": 0.2})
           + colorbar("rate")).as_svg()
    key = (plot(tree) + color_branches({"A": "x", "B": "y", "C": "x", "D": "y"})
           + legend("state")).as_svg()
    for svg in (bar, key):
        assert '<rect' in svg and 'fill="#ffffff"' in svg


def test_headroom_pushes_the_tree_down_and_leaves_the_bottom_alone():
    """A key drawn top-left shares a row with the first branch unless the tree is given headroom."""
    from phylustrator import Style

    tree = loads("((A:1,B:1)C:1,D:2)R;")
    plain = plot(tree, style=Style(width=400, height=300, margin=20))
    lifted = plot(tree, style=Style(width=400, height=300, margin=20, headroom=60))
    top = lambda fig: min(t.y for t in fig.geometry().tips)      # noqa: E731
    bottom = lambda fig: max(t.y for t in fig.geometry().tips)   # noqa: E731
    assert top(lifted) > top(plain) + 30
    assert bottom(lifted) == pytest.approx(bottom(plain))


def test_rubberband_wraps_a_radial_tree_in_its_population_colours():
    """The band renders on a radial tree and paints each population's colour."""
    tree = loads("((A:1,B:1)C:1,(D:1,E:1)F:1,(G:1,H:1)I:1)R:1;")
    pops = {"A": "p0", "B": "p0", "D": "p1", "E": "p1", "G": "p2", "H": "p2"}
    palette = {"p0": "#207080", "p1": "#c77bad", "p2": "#9060b0"}
    svg = (plot(tree, layout="radial")
           + rubberband(pops, palette=palette)).as_svg()
    assert svg.lstrip().startswith("<")
    for colour in palette.values():
        assert colour in svg


def test_rubberband_survives_a_lopsided_tree_and_stays_smooth():
    """A near cluster and a far one on a long branch is the case the clamp must survive: the band
    still renders, and rounding it (a bigger ``smooth``) does not error or drop the colours."""
    tree = loads("((A:0.1,B:0.1)C:0.1,((D:0.1,E:0.1)F:0.1):5.0)R:1;")
    pops = {"A": "p0", "B": "p0", "D": "p1", "E": "p1"}
    palette = {"p0": "#207080", "p1": "#c77bad"}
    for smooth in (0.0, 0.18, 0.4):
        svg = (plot(tree, layout="radial")
               + rubberband(pops, palette=palette, gap=8.0, smooth=smooth)).as_svg()
        assert svg.count("<path") > 0
        assert "#207080" in svg and "#c77bad" in svg


# --- time_marker across the layouts (issue #8) ------------------------------------------------

_MARKER_TREE = "((((A:1,B:1)F:1,C:2)G:1,D:3)H:1,E:4)R;"


def _circle(svg):
    """The (cx, cy, r) of the one circle in the figure — the radial marker."""
    found = re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([-\d.]+)"', svg)
    assert len(found) == 1, f"expected one circle, found {len(found)}"
    return tuple(float(v) for v in found[0])


def test_time_marker_draws_in_rectangular_and_radial():
    """It rendered nothing at all in radial, and said nothing about it."""
    tree = loads(_MARKER_TREE)
    for layout in ("rectangular", "radial"):
        svg = (plot(tree, layout=layout) + time_marker(2.0, color="#D55E00", width=4)).as_svg()
        assert "#D55E00" in svg, f"the marker is missing from the {layout} layout"


def test_the_radial_marker_is_a_circle_through_the_nodes_at_that_distance():
    tree = loads(_MARKER_TREE)
    fig = plot(tree, layout="radial") + time_marker(2.0, color="#D55E00")
    cx, cy, r = _circle(fig.as_svg())
    at_two = [n for n in fig.geometry().nodes if n.name == "G"][0]      # G sits at distance 2
    assert math.hypot(at_two.x - cx, at_two.y - cy) == pytest.approx(r)
    assert r > 0


def test_the_radial_marker_takes_the_stem_off_the_time():
    """The radial layout starts at the crown, as branch_events already assumed for its events."""
    tree = loads("((((A:1,B:1)F:1,C:2)G:1,D:3)H:1,E:4)R:1.5;")
    fig = plot(tree, layout="radial") + time_marker(3.5)                # 2.0 past the crown
    cx, cy, r = _circle(fig.as_svg())
    at_two = [n for n in fig.geometry().nodes if n.name == "G"][0]
    assert math.hypot(at_two.x - cx, at_two.y - cy) == pytest.approx(r)


def test_the_radial_marker_keeps_its_dash():
    tree = loads(_MARKER_TREE)
    assert "stroke-dasharray" in (plot(tree, layout="radial") + time_marker(2.0)).as_svg()
    assert "stroke-dasharray" not in (plot(tree, layout="radial")
                                      + time_marker(2.0, dash=False)).as_svg()


def test_time_marker_refuses_the_unrooted_layout():
    """A distance from the origin is not a place on an equal-angle layout. Say so, do not skip."""
    with pytest.raises(ValueError, match="unrooted"):
        (plot(loads(_MARKER_TREE), layout="unrooted") + time_marker(2.0)).as_svg()


def test_time_marker_refuses_a_time_the_radial_layout_cannot_show():
    with pytest.raises(ValueError, match="stem"):
        (plot(loads("((A:1,B:1)F:1,C:2)R:1.5;"), layout="radial") + time_marker(0.5)).as_svg()


# --- a centred title, and a legend in any corner (issues #9 and #10) ---------------------------

_PLACED = Style(width=400, height=300, margin=20)
_ENTRIES = {"a": "#111111", "b": "#222222"}
_CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")


def _rect(svg, fill):
    found = re.search(rf'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)" '
                      rf'fill="{fill}"', svg)
    assert found, f"no rect filled {fill}"
    return tuple(float(v) for v in found.groups())


def _swatches(svg):
    return [_rect(svg, fill) for fill in _ENTRIES.values()]


def _backdrop(svg):
    """The white patch the legend paints behind itself — the block's own box."""
    boxes = re.findall(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)" '
                       r'fill="#ffffff"', svg)
    boxes = [tuple(float(v) for v in b) for b in boxes if (float(b[0]), float(b[1])) != (0.0, 0.0)]
    assert len(boxes) == 1, f"expected one backdrop, found {len(boxes)}"
    return boxes[0]


def _legend_svg(loc):
    return (plot(loads("((A:1,B:1)C:1,D:2)R;"), style=_PLACED)
            + legend("state", loc=loc, entries=_ENTRIES)).as_svg()


def test_title_sits_centred_over_the_panel():
    """note pins text to a corner; a title belongs over the middle of the figure."""
    svg = (plot(loads("((A:1,B:1)C:1,D:2)R;"), style=_PLACED) + title("Primates")).as_svg()
    found = re.search(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*text-anchor="(\w+)"[^>]*>Primates</text>', svg)
    assert found
    x, y, anchor = float(found.group(1)), float(found.group(2)), found.group(3)
    assert x == pytest.approx(_PLACED.width / 2) and anchor == "middle"
    assert y < _PLACED.margin, "the title should sit in the top margin, above the tree"


def test_a_title_stays_on_the_page_when_the_top_margin_is_thin():
    svg = (plot(loads("(A:1,B:1)R;"), style=Style(width=400, height=300, margin=4))
           + title("Primates", size=20)).as_svg()
    y = float(re.search(r'<text x="[-\d.]+" y="([-\d.]+)"[^>]*>Primates</text>', svg).group(1))
    assert y >= 10.0, "half the title would be cut off by the top edge"


def test_note_refuses_a_loc_that_is_not_a_corner():
    """`loc="top-centre"` used to fall through and print right-aligned instead."""
    with pytest.raises(ValueError, match="title"):
        note("Primates", loc="top-centre")
    with pytest.raises(ValueError, match="top-left"):
        note("Primates", loc="top")


def test_the_legend_default_corner_is_unchanged():
    assert _legend_svg("top-left") == (plot(loads("((A:1,B:1)C:1,D:2)R;"), style=_PLACED)
                                       + legend("state", entries=_ENTRIES)).as_svg()


@pytest.mark.filterwarnings("ignore::UserWarning")      # it is put in every corner on purpose
def test_the_legend_sits_in_the_corner_it_is_given():
    """branch_events has always taken the four corners; legend was pinned to the top left."""
    top_left = _swatches(_legend_svg("top-left"))
    for loc in _CORNERS:
        svg = _legend_svg(loc)
        swatches = _swatches(svg)
        bx, by, bw, bh = _backdrop(svg)
        assert bx >= 0 and by >= 0, f"{loc}: the legend runs off the page"
        assert bx + bw <= _PLACED.width and by + bh <= _PLACED.height, f"{loc}: off the page"
        if "left" in loc:
            assert swatches[0][0] == pytest.approx(_PLACED.margin), loc
        else:
            # the block is right-aligned on the right margin (the backdrop adds 6px of padding)
            assert bx + bw - 6 == pytest.approx(_PLACED.width - _PLACED.margin), loc
        if "top" in loc:
            assert swatches[0][1] == pytest.approx(top_left[0][1]), loc
        else:
            lowest = max(y + h for _, y, _, h in swatches)
            assert lowest == pytest.approx(_PLACED.height - _PLACED.margin, abs=1.0), loc


def test_legend_refuses_a_loc_that_is_not_a_corner():
    with pytest.raises(ValueError, match="bottom-right"):
        legend("state", loc="middle", entries=_ENTRIES)


# --- an event carrying its own style (issue #11) -----------------------------------------------

_EV_TREE = "((A:1,B:1)C:1,D:2)R;"
_EV_STYLE = Style(width=420, height=300, margin=30)


def _events_svg(events, **kw):
    return (plot(loads(_EV_TREE), style=_EV_STYLE) + branch_events(events, **kw)).as_svg()


def _arcs(svg):
    """Each transfer arc as (colour, width, opacity) — the curved body, not the two head strokes."""
    out = []
    for m in re.finditer(r'<path d="M[^"]*Q[^"]*" fill="none" stroke="([^"]+)" '
                         r'stroke-width="([\d.]+)"([^>]*)>', svg):
        faded = re.search(r'stroke-opacity="([\d.]+)"', m.group(3))
        out.append((m.group(1), float(m.group(2)), float(faded.group(1)) if faded else 1.0))
    return out


def _transfer(**kw):
    return {"kind": "transfer", "donor": "A", "recipient": "D", "x": 1.6, **kw}


def test_an_event_without_a_weight_is_drawn_exactly_as_before():
    """A weight of 1 is the full style, so an unweighted figure must not move at all."""
    assert _events_svg([_transfer()]) == _events_svg([_transfer(weight=1.0)])


def test_a_weighted_arc_is_thinner_and_fainter():
    """Summed over gene families, every pair carries a count; drawn at one weight they all look
    the same."""
    (_, heavy_w, heavy_o), = _arcs(_events_svg([_transfer()]))
    (colour, light_w, light_o), = _arcs(_events_svg([_transfer(weight=0.2)]))
    assert light_w < heavy_w and light_o < heavy_o
    assert light_w == pytest.approx(heavy_w * 0.4)      # floor 0.25 + 0.75 * 0.2
    assert light_o == pytest.approx(0.4)
    assert colour == "#2e8b57", "the weight must not change the kind's colour"


def test_the_weight_floor_keeps_the_lightest_arc_on_the_page():
    (_, full, _), = _arcs(_events_svg([_transfer()]))
    (_, width, opacity), = _arcs(_events_svg([_transfer(weight=0.0)]))
    assert width == pytest.approx(full * 0.25) and width > 0
    assert opacity == pytest.approx(0.25)
    (_, raised, _), = _arcs(_events_svg([_transfer(weight=0.0)], weight_floor=0.5))
    assert raised == pytest.approx(full * 0.5)


def test_a_weight_outside_zero_to_one_is_clamped():
    assert _events_svg([_transfer(weight=5)]) == _events_svg([_transfer()])
    assert _events_svg([_transfer(weight=-2)]) == _events_svg([_transfer(weight=0.0)])


def test_an_event_can_carry_its_own_colour_and_size():
    plain = _rect(_events_svg([{"kind": "duplication", "node": "A", "x": 1.5}], legend=False),
                  "#3a7ca5")
    bigger = _rect(_events_svg([{"kind": "duplication", "node": "A", "x": 1.5,
                                 "size": 11.0, "color": "#ff0000"}], legend=False), "#ff0000")
    assert bigger[2] == pytest.approx(plain[2] * 2), "size did not override the layer's size"


def test_the_legend_shows_the_kind_colour_not_one_events_override():
    svg = _events_svg([{"kind": "duplication", "node": "A", "x": 1.5, "color": "#ff0000"}])
    assert "#ff0000" in svg                       # the mark took the override
    assert "#3a7ca5" in svg, "the key names the kind, so it keeps the kind's colour"


def test_a_tuple_event_still_works():
    svg = _events_svg([("A", 1.5, "duplication")], legend=False)
    assert "#3a7ca5" in svg and "fill-opacity" not in svg


# --- a transfer has to be able to happen --------------------------------------------------------

# A's branch runs 1..2, D's runs 0..2, so the two coexist over 1..2
def test_a_transfer_outside_the_window_is_refused():
    """Drawn, it sits on a row whose branch has already ended, and reads as a transfer that never
    happened. Five arcs of a figure went out that way."""
    with pytest.raises(ValueError, match=r"outside \[1, 2\]"):
        _events_svg([_transfer(x=2.6)])
    with pytest.raises(ValueError, match="A -> D"):
        _events_svg([_transfer(x=0.4)])


def test_a_transfer_between_lineages_that_never_meet_says_so():
    """E ends at 1 and its grandchild A starts at 2, so no time can hold both. A parent and its
    child do touch, at the instant of the split, and that stays drawable."""
    tree = loads("(((A:1,B:1)C:1,D:2)E:1,F:3)R;")
    with pytest.raises(ValueError, match="never exist at the same time"):
        (plot(tree, style=_EV_STYLE)
         + branch_events([{"kind": "transfer", "donor": "A", "recipient": "E", "x": 1.5}])).as_svg()
    assert (plot(tree, style=_EV_STYLE)
            + branch_events([{"kind": "transfer", "donor": "A", "recipient": "C",
                              "x": 2.0}])).as_svg()


def test_a_transfer_on_a_branch_end_is_kept():
    """Branch lengths come from a reconstruction; a time on the boundary must not fail."""
    for x in (1.0, 2.0):
        assert _arcs(_events_svg([_transfer(x=x)]))


def test_clamp_false_draws_a_transfer_exactly_where_it_says():
    assert _arcs(_events_svg([_transfer(x=2.6)], clamp=False))


def test_the_window_follows_the_layout_that_drops_the_stem():
    """Times are given on the rectangular, stem-inclusive scale. The radial layout starts at the
    crown, so the window has to shift with it rather than refusing a valid transfer."""
    tree = loads("((A:1,B:1)C:1,D:2)R:0.5;")           # every distance moves out by the 0.5 stem
    ev = [{"kind": "transfer", "donor": "A", "recipient": "D", "x": 2.1}]
    for layout in ("rectangular", "radial"):
        assert (plot(tree, layout=layout, style=_EV_STYLE) + branch_events(ev)).as_svg()
    with pytest.raises(ValueError, match="outside"):
        (plot(tree, layout="radial", style=_EV_STYLE)
         + branch_events([{**ev[0], "x": 0.9}])).as_svg()


def test_a_point_marker_outside_its_branch_is_still_pulled_onto_it():
    """Markers clamp, as they always have: only a transfer is refused, because moving it would
    redraw it at a time the caller did not give."""
    svg = _events_svg([{"kind": "duplication", "node": "A", "x": 9.0}], legend=False)
    assert _rect(svg, "#3a7ca5")[0] < _EV_STYLE.width, "the marker was not brought back on the page"


# --- flat numeric colouring, and who owns the bar under a node (issues #13 and #27) -------------

_BUG_NWK = "(((a:1,b:1)n1:1,(c:1.5,d:1.5)n2:0.5)n3:1,((e:1,f:1)n4:1.2,g:2.2)n5:0.8)root:0.5;"


def _segments(svg):
    """Every straight segment as (x0, y0, x1, y1, stroke)."""
    out = []
    for x0, y0, x1, y1, stroke in re.findall(
            r'<path d="M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+)" stroke="([^"]+)"', svg):
        out.append((float(x0), float(y0), float(x1), float(y1), stroke))
    return out


def _verticals(svg, stroke=None):
    return [s for s in _segments(svg)
            if abs(s[0] - s[2]) < 1e-9 and abs(s[1] - s[3]) > 1e-9 and (stroke is None or s[4] == stroke)]


def test_a_numeric_map_can_be_drawn_flat():
    """A value that belongs to the branch as a whole is misread as a gradient: the branch is shaded
    by its parent's value, and it looks like it changes along its length."""
    tree = loads(_BUG_NWK)
    values = {n.name: 0.9 for n in tree.walk() if n.parent is not None}
    values["n1"] = 0.05
    assert "<linearGradient" in (plot(tree) + color_branches(values)).as_svg()
    flat = (plot(tree) + color_branches(values, gradient=False)).as_svg()
    assert "<linearGradient" not in flat
    assert len({s[4] for s in _segments(flat)}) > 1, "the colormap still has to colour the branches"


def test_a_flat_numeric_map_keeps_its_colorbar():
    """The workaround in the issue — recolour by hand and pass a palette — costs the colorbar."""
    tree = loads(_BUG_NWK)
    values = {n.name: 0.9 for n in tree.walk() if n.parent is not None}
    svg = (plot(tree) + color_branches(values, gradient=False) + colorbar("rate")).as_svg()
    assert "<linearGradient" in svg and "rate" in svg       # the bar itself is the only gradient


def test_the_bar_under_a_node_belongs_to_the_child():
    """A map of every branch leaves the root out, since the root has no branch. The root's bar went
    unpainted and the two clades floated apart."""
    tree = loads(_BUG_NWK)
    branches = {n.name: "#4a6fa5" for n in tree.walk() if n.parent is not None}
    svg = (plot(tree, style=Style(branch_color="none", branch_width=1.0))
           + color_branches(branches, palette={"#4a6fa5": "#4a6fa5"}, width=1.0)).as_svg()
    painted = _verticals(svg, "#4a6fa5")
    assert len(painted) == 12, "every connector segment, the root's two included, must be painted"
    leftmost = min(v[0] for v in _verticals(svg))          # the root's bar, nearest the origin
    assert len([v for v in painted if v[0] == leftmost]) == 2, "the root's own bar is still missing"


def test_a_gradient_still_starts_the_drop_in_the_parents_colour():
    """Under a gradient the child's branch begins in the parent's colour, so the drop keeps it."""
    tree = loads(_BUG_NWK)
    values = {n.name: (0.1 if n.name == "n3" else 0.9) for n in tree.walk()}
    svg = (plot(tree) + color_branches(values)).as_svg()
    under_root = sorted(_verticals(svg), key=lambda v: v[0])[:2]
    assert len({v[4] for v in under_root}) == 1, "the two halves of one bar must agree"


def test_a_radial_ring_splits_only_when_the_children_differ():
    """The ring at a node is one arc of 24 segments; it is cut per child only when it has to be."""
    tree = loads(_BUG_NWK)
    one = {n.name: "x" for n in tree.walk()}
    mixed = dict(one, n1="y")
    palette = {"x": "#4a6fa5", "y": "#c1443c"}
    uniform_svg = (plot(tree, layout="radial") + color_branches(one, palette=palette)).as_svg()
    mixed_svg = (plot(tree, layout="radial") + color_branches(mixed, palette=palette)).as_svg()
    assert "#c1443c" in mixed_svg
    assert len(_segments(mixed_svg)) > len(_segments(uniform_svg)), "the ring was not split"


# --- one lineage thicker, and layers that leave the rest alone (issues #25 and #28) -------------

_W_NWK = "((a:1,b:1)x:1,(c:1,d:1)y:1)r;"


def _drawn(svg):
    """Every straight segment as (x0, y0, x1, y1, stroke, stroke-width)."""
    out = []
    for x0, y0, x1, y1, stroke, w in re.findall(
            r'<path d="M(-?[\d.]+),(-?[\d.]+) L(-?[\d.]+),(-?[\d.]+)" stroke="([^"]+)" '
            r'stroke-width="([\d.]+)"', svg):
        out.append((float(x0), float(y0), float(x1), float(y1), stroke, float(w)))
    return out


def test_lineage_is_the_path_from_the_root_down():
    tree = loads(_W_NWK)
    assert lineage(tree, "a") == ["r", "x", "a"]
    assert lineage(tree, "r") == ["r"]
    with pytest.raises(ValueError, match="no node named"):
        lineage(tree, "zz")


def _topmost(svg):
    """The stroke finally showing on each piece of geometry: what a reader sees, not what the file
    still holds underneath."""
    out = {}
    for x0, y0, x1, y1, stroke, _w in _drawn(svg):
        out[(round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3))] = stroke
    return out


def test_a_second_layer_can_leave_the_branches_it_does_not_map_alone():
    """A layer meant for a few branches repainted every other one in the default colour."""
    tree = loads(_W_NWK)
    first = color_branches({"a": "x", "b": "x"}, palette={"x": "#c9a227"}, width=1.0)
    kept = _topmost((plot(tree) + first
                     + color_branches({"c": "y"}, palette={"y": "#8a8a8a"}, width=3.0,
                                      others="keep")).as_svg())
    repainted = _topmost((plot(tree) + first
                          + color_branches({"c": "y"}, palette={"y": "#8a8a8a"},
                                           width=3.0)).as_svg())
    gold = [g for g, stroke in _topmost((plot(tree) + first).as_svg()).items()
            if stroke == "#c9a227"]
    assert gold, "the first layer drew nothing to protect"
    assert all(kept[g] == "#c9a227" for g in gold), "the second layer painted over the first"
    assert "#8a8a8a" in kept.values() and "#333333" in kept.values()
    assert any(repainted[g] != "#c9a227" for g in gold), "the default must still repaint everything"


def test_color_branches_takes_a_width_per_branch():
    tree = loads(_W_NWK)
    values = {n.name: "s" for n in tree.walk()}
    svg = (plot(tree) + color_branches(values, palette={"s": "#4a6fa5"},
                                       width={"x": 5.0, "a": 5.0})).as_svg()
    widths = {w for *_, stroke, w in _drawn(svg) if stroke == "#4a6fa5"}
    assert 5.0 in widths and len(widths) > 1, "every branch came out at one width"


def test_a_thick_lineage_does_not_fatten_the_whole_bar():
    """The drop belongs to the child, so the bar at a node is thick only towards the child the
    lineage carries on into."""
    tree = loads(_W_NWK)
    svg = (plot(tree) + highlight_lineage("a", width=4.0)).as_svg()
    thick = [seg for seg in _drawn(svg) if seg[5] == 4.0]
    assert len(thick) == 4, "the lineage is two branches and their two drops"
    verticals = [seg for seg in thick if abs(seg[0] - seg[2]) < 1e-9]
    assert len(verticals) == 2, "both drops of the lineage, and no other"
    ys = {round(seg[1], 3) for seg in verticals} | {round(seg[3], 3) for seg in verticals}
    assert len(ys) == 3, "each drop runs from its node to the next one down the lineage"


def test_highlight_lineage_leaves_every_other_branch_where_it_was():
    tree = loads(_W_NWK)
    plain = _drawn((plot(tree)).as_svg())
    with_it = _drawn((plot(tree) + highlight_lineage("a", width=4.0)).as_svg())
    assert all(seg in with_it for seg in plain), "the base tree was redrawn or moved"
    assert len(with_it) == len(plain) + 4
    with pytest.raises(ValueError, match="no node named"):
        (plot(tree) + highlight_lineage("zz")).as_svg()


# --- four small gaps: labels, chips, unsampled donors, ages (issues #14, #15, #16, #21) ---------

_SMALL = "((A:1,B:1)x:1,(C:1,D:1)y:1)r;"


def _written(svg):
    return re.findall(r"<text [^>]*>([^<]*)</text>", svg)


def test_node_labels_can_write_a_value_worked_out_for_each_node():
    """The library could colour by a dict and not label by one."""
    tree = loads(_SMALL)
    names = _written((plot(tree) + node_labels()).as_svg())
    assert "x" in names and "y" in names                     # the default is still the name
    support = _written((plot(tree) + node_labels(values={"x": 81, "y": 99.0})).as_svg())
    assert "81" in support and "99" in support, "99.0 should be written plainly as 99"
    assert "x" not in support, "the name was written as well as the value"
    computed = _written((plot(tree) + node_labels(text=lambda n: f"[{n.name}]")).as_svg())
    assert "[x]" in computed


def test_labels_skip_a_node_with_no_value_of_its_own():
    tree = loads(_SMALL)
    written = _written((plot(tree) + node_labels(values={"x": 7})
                        + tip_labels(values={"A": "first"})).as_svg())
    assert "7" in written and "first" in written
    assert "y" not in written and "B" not in written


def test_node_labels_can_cover_the_tips_too():
    tree = loads(_SMALL)
    written = _written((plot(tree) + node_labels(values={"A": 1, "x": 2}, leaves=True)).as_svg())
    assert "1" in written and "2" in written


def test_a_tip_chip_can_be_drawn_open():
    """White on white: absence vanished, so a black-and-white presence column was impossible."""
    tree = loads(_SMALL)
    presence = {"A": "present", "B": "absent"}
    palette = {"present": "#000000", "absent": "#ffffff"}
    assert 'stroke="white"' in (plot(tree) + tip_track(presence, palette=palette)).as_svg()
    inked = (plot(tree) + tip_track(presence, palette=palette, stroke="#1a1a1a",
                                    stroke_width=0.8)).as_svg()
    assert 'stroke="#1a1a1a"' in inked and 'fill="#ffffff"' in inked


def test_a_transfer_can_arrive_from_a_donor_outside_the_tree():
    """A transfer from an unsampled lineage was skipped, silently, for want of a donor node."""
    tree = loads(_SMALL)

    def shaft(**kw):
        ev = [{"kind": "transfer", "recipient": "x", "x": 0.5, **kw}]
        svg = (plot(tree) + branch_events(ev, legend=False)).as_svg()
        found = re.search(r'<path d="M([\d.]+),([\d.]+) Q[^"]*" fill="none"', svg)
        assert found, "no arrow was drawn"
        return float(found.group(1)), float(found.group(2))

    x_above, y_above = shaft(donor=None)
    x_below, y_below = shaft(donor=None, side="below")
    assert y_above < y_below, "side= did not flip the arrow"
    assert x_above == pytest.approx(x_below), "an incoming arrow lands at its own time"
    assert shaft(donor="not_in_this_tree") == (x_above, y_above), "an unknown donor is unsampled"


def test_an_incoming_transfer_still_has_to_land_on_the_branch():
    tree = loads(_SMALL)
    with pytest.raises(ValueError, match="into x"):
        (plot(tree) + branch_events([{"kind": "transfer", "donor": None, "recipient": "x",
                                      "x": 9.0}])).as_svg()


def test_a_time_axis_can_count_back_from_the_present():
    """A dated tree reads the other way: 0 under the tips, the root at its age."""
    tree = loads("((A:1000,B:1000)n1:2000,(C:1500,D:1500)n2:1500)r:100;")
    svg = (plot(tree) + time_axis("million years ago", before_present=True, step=1000)).as_svg()
    ticks = [(float(x), t) for x, t in re.findall(r'<text x="([\d.]+)" y="[\d.]+"[^>]*>(\d+)</text>', svg)]
    assert [t for _, t in sorted(ticks)] == ["3000", "2000", "1000", "0"]
    forward = (plot(tree) + time_axis("time", step=1000)).as_svg()
    onward = [t for _, t in sorted((float(x), t) for x, t in
                                   re.findall(r'<text x="([\d.]+)" y="[\d.]+"[^>]*>(\d+)</text>', forward))]
    assert onward == ["0", "1000", "2000", "3000"]
    with pytest.raises(ValueError, match="step must be positive"):
        (plot(tree) + time_axis("t", step=0)).as_svg()


# --- a state that fades along a branch (issue #23) ---------------------------------------------

_FADE_NWK = "((A:1,B:1)X:1,(C:1,D:1)Y:1)R:0.1;"
_FADE_PALETTE = {"a": "#2E6E8E", "b": "#C55A3B"}


def _history(fade=True, **kw):
    """X's branch: state a for its first half, then fading to b by its end."""
    shift = ("a", "b") if fade else "b"
    return {"X": [("a", 0.5), (shift, 0.5)], "A": [("b", 1)], "B": [("b", 1)],
            "Y": [("a", 1)], "C": [("a", 1)], "D": [("a", 1)]}


def test_a_segment_whose_state_is_a_pair_fades_between_the_two():
    """A trait that shifts after an event, rather than switching at an instant."""
    for layout in ("rectangular", "radial"):
        svg = (plot(loads(_FADE_NWK), layout=layout)
               + color_history(_history(), palette=_FADE_PALETTE)).as_svg()
        assert svg.count("<linearGradient") == 1, f"no fade on the {layout} layout"
        assert "#2E6E8E" in svg and "#C55A3B" in svg


def test_a_plain_history_still_steps():
    svg = (plot(loads(_FADE_NWK)) + color_history(_history(fade=False),
                                                  palette=_FADE_PALETTE)).as_svg()
    assert "<linearGradient" not in svg


def test_a_faded_branch_ends_in_the_state_it_faded_into():
    """The connector below X follows X's end state, which is the second half of the pair."""
    svg = (plot(loads(_FADE_NWK)) + color_history(_history(), palette=_FADE_PALETTE)).as_svg()
    drops = [seg for seg in _drawn(svg) if abs(seg[0] - seg[2]) < 1e-9 and abs(seg[1] - seg[3]) > 1e-9]
    under_x = [seg for seg in drops if seg[4] in _FADE_PALETTE.values()]
    assert under_x, "no connector was painted"
    assert "#C55A3B" in {seg[4] for seg in under_x}, "the branch ended in a, not in b"


def test_both_halves_of_a_pair_reach_the_key():
    svg = (plot(loads(_FADE_NWK)) + color_history({"X": [(("a", "b"), 1.0)]},
                                                  palette=_FADE_PALETTE) + legend("state")).as_svg()
    written = re.findall(r"<text [^>]*>([^<]*)</text>", svg)
    assert "a" in written and "b" in written


def test_a_dashed_branch_that_fades_is_drawn_in_the_state_it_ends_in():
    """A dashed line cannot carry a gradient, and a solid one would hide an extinct lineage."""
    svg = (plot(loads(_FADE_NWK), dashed={"X"})
           + color_history(_history(), palette=_FADE_PALETTE, dashed={"X"})).as_svg()
    assert "<linearGradient" not in svg
    assert "stroke-dasharray" in svg and "#C55A3B" in svg


# --- a colormap that runs the other way (issue #32) ---------------------------------------------

def test_a_colormap_reverses_with_an_r_suffix():
    """Reversing a scale is routine when the low values are the interesting ones, and _r is the
    convention everyone arrives with."""
    from phylustrator.color import _COLORMAPS, colormap_hex

    for name in _COLORMAPS:
        assert colormap_hex(f"{name}_r") == list(reversed(colormap_hex(name))), name
    assert colormap_hex("VIRIDIS_R") == colormap_hex("viridis_r"), "the name is case-insensitive"


def test_an_unknown_colormap_still_lists_the_base_names():
    from phylustrator.color import colormap_hex

    with pytest.raises(ValueError) as raised:
        colormap_hex("nope")
    said = str(raised.value)
    assert "viridis" in said and "viridis_r" not in said, "the list should not be doubled"
    assert "_r" in said, "the suffix is worth naming once"


def test_a_reversed_colormap_colours_a_figure():
    tree = loads("((a:1,b:1)n1:2,(c:2,d:2)n2:1)root;")
    values = {"a": 0, "b": 8, "c": 120, "d": 160}
    one_way = (plot(tree) + tip_track(values, cmap="viridis")).as_svg()
    other = (plot(tree) + tip_track(values, cmap="viridis_r")).as_svg()
    assert one_way != other


# --- ticks placed by hand, and under the nodes (issue #29) --------------------------------------

def test_the_axis_takes_the_places_of_its_ticks_and_what_they_say():
    """An axis that reads as the order of the nodes, not as a distance."""
    tree = loads("((A:2,B:2)x:1,(C:1,D:1)y:2)r:1;")
    fig = plot(tree) + time_axis("order", at=[1, 2, 3], labels=["one", "two", "three"])
    svg = fig.as_svg()
    geom = fig.geometry()
    placed = [(float(x), t) for x, t in
              re.findall(r'<text x="([\d.]+)" y="[\d.]+"[^>]*>(one|two|three)</text>', svg)]
    assert [t for _, t in sorted(placed)] == ["one", "two", "three"]
    assert [x for x, _ in sorted(placed)] == pytest.approx([geom.px(1), geom.px(2), geom.px(3)])


def test_a_tick_under_every_internal_node_numbered_from_the_oldest():
    tree = loads("((A:2,B:2)x:1,(C:1,D:1)y:2)r:1;")
    fig = plot(tree) + time_axis("order of the nodes", at="nodes")
    svg = fig.as_svg()
    geom = fig.geometry()
    placed = sorted((float(x), t) for x, t in
                    re.findall(r'<text x="([\d.]+)" y="[\d.]+"[^>]*>([123])</text>', svg))
    inner = sorted(n.x for n in geom.nodes if not n.is_leaf)
    assert [t for _, t in placed] == ["1", "2", "3"], "numbered from the oldest node"
    assert [x for x, _ in placed] == pytest.approx(inner)


def test_the_axis_refuses_two_ways_of_placing_one_tick():
    with pytest.raises(ValueError, match="not both"):
        time_axis("t", at=[1, 2], step=1)
    with pytest.raises(ValueError, match="labels= needs at="):
        time_axis("t", labels=["one"])
    with pytest.raises(ValueError, match="labels="):
        (plot(loads("((A:2,B:2)x:1,(C:1,D:1)y:2)r:1;"))
         + time_axis("t", at=[1, 2], labels=["only one"])).as_svg()


# --- a key that hides a branch says so (issue #35) ----------------------------------------------

_HIDE_NWK = "((((A:1,B:1):1,C:2):1,D:3):1,(E:3.5,F:3.5):0.5);"
_HIDE_VALUES = {"A": "First category with a long descriptive label",
                "E": "Second category with a long descriptive label",
                "F": "Second category with a long descriptive label"}
_HIDE_PALETTE = {"First category with a long descriptive label": "#0072B2",
                 "Second category with a long descriptive label": "#D55E00"}


def _with_legend(**kw):
    base = (plot(loads(_HIDE_NWK)) + color_branches(_HIDE_VALUES, palette=_HIDE_PALETTE)
            + tip_labels())
    return base + legend("", size=14, **kw)


def test_a_key_that_covers_a_branch_names_it():
    """The lowest clade joined at the root, the key covered the branch leading to F, and F looked
    detached from the tree with nothing said."""
    with pytest.warns(UserWarning, match="bottom-left") as caught:
        _with_legend(loc="bottom-left").as_svg()
    assert "F" in str(caught[0].message)


def test_auto_takes_the_corner_that_covers_the_least():
    with warnings.catch_warnings():
        warnings.simplefilter("error")                 # auto must find a free corner here
        _with_legend(loc="auto").as_svg()


def test_auto_picks_a_corner_that_says_nothing_when_one_exists():
    """Not every corner is free on this tree — the point is that auto lands on one that is."""
    quiet = []
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _with_legend(loc=corner).as_svg()
        if not caught:
            quiet.append(corner)
    assert quiet, "no corner is free, so this tree cannot test the choice"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _with_legend(loc="auto").as_svg()


def test_auto_is_a_corner_the_legend_accepts_and_note_does_not():
    assert callable(legend("x", loc="auto", entries={"a": "#111111"}))
    with pytest.raises(ValueError, match="auto"):
        legend("x", loc="middle", entries={"a": "#111111"})
    with pytest.raises(ValueError) as raised:
        note("x", loc="auto")
    allowed = str(raised.value).split(", not ")[0]
    assert "auto" not in allowed, "a note has no tree to measure against, so it has no auto"


# --- plot() can ask for a cladogram (issue #43) --------------------------------------------------

_SHORT_DEEP = "((((a:1,b:1):0.01,(c:1,d:1):0.01):0.01,(e:1,f:1):0.01):0.01,g:1);"


def _radii(fig, tree):
    """Each tip's distance from the root, in the layout's own units."""
    from phylustrator.trees.figure import _LAYOUTS
    layout = _LAYOUTS[fig.layout](tree, stem=fig.stem, cladogram=fig.cladogram)
    return {leaf.name: math.hypot(layout.x(leaf), layout.y(leaf)) for leaf in tree.leaves}


def test_plot_passes_cladogram_to_the_layout():
    """To scale, this tree's deep branches are 0.01 long and every tip sits at radius ~1, so the
    whole topology collapses onto the centre. By depth the tips spread over 1 to 4."""
    tree = loads(_SHORT_DEEP)
    to_scale = _radii(plot(tree, layout="radial"), tree)
    by_depth = _radii(plot(tree, layout="radial", cladogram=True), tree)
    assert max(to_scale.values()) - min(to_scale.values()) < 0.05
    assert by_depth["a"] == pytest.approx(4.0)
    assert by_depth["e"] == pytest.approx(3.0)
    assert by_depth["g"] == pytest.approx(1.0)


def test_cladogram_survives_adding_layers_and_restyling():
    """`+` and `with_style` rebuild the figure, and a dropped flag would silently redraw to scale."""
    tree = loads(_SHORT_DEEP)
    fig = plot(tree, layout="radial", cladogram=True) + tip_labels()
    assert fig.cladogram is True
    assert fig.with_style(Style(width=400, height=400)).cladogram is True
    assert len(fig.as_svg()) > 100


def test_cladogram_is_off_by_default_everywhere_it_is_read():
    """geometry() and clade_box() lay the tree out again, so they have to read the same flag."""
    tree = loads("((A:3,B:3)x:1,C:4)r;")
    assert plot(tree).cladogram is False
    flat = plot(tree, cladogram=True)
    assert flat.geometry().xlim != plot(tree).geometry().xlim
    # x1 is where the tips end, the same in both; x0 is the clade's own root, which moves
    assert flat.clade_box("x").x0 != plot(tree).clade_box("x").x0


# --- a tip_track column can be named (issue #38) -------------------------------------------------

_TRACK_NWK = "((A:1,B:1)x:1,(C:1.5,D:1.5)y:0.5)r;"
_TRACK_PALETTE = {"yes": "#2a78d6", "no": "#ffffff"}
_TRACK_COLUMNS = {"truth": {"A": "yes", "B": "yes", "C": "no", "D": "no"},
                  "tool 1": {"A": "yes", "B": "no", "C": "no", "D": "no"},
                  "tool 2": {"A": "no", "B": "no", "C": "yes", "D": "no"}}


def _three_columns(**kw):
    fig = plot(loads(_TRACK_NWK), style=Style(width=560, height=320, margin_right=110, margin_top=70))
    for i, (name, values) in enumerate(_TRACK_COLUMNS.items()):
        fig = fig + tip_track(values, palette=_TRACK_PALETTE, offset=24 + 15 * i,
                              stroke="#1a1a1a", label=name, **kw)
    return fig


def test_each_column_gets_its_own_header():
    svg = _three_columns().as_svg()
    for name in _TRACK_COLUMNS:
        assert f">{name}<" in svg
    # one header per column, each over its own column and none over another's
    xs = [float(m) for m in re.findall(r'rotate\(-90(?:\.0)? ([\d.]+) [\d.]+\)', svg)]
    assert len(xs) == 3
    assert sorted(xs) == xs and len(set(xs)) == 3


def test_a_header_sits_above_the_top_chip():
    svg = _three_columns().as_svg()
    header_y = min(float(m) for m in re.findall(r'rotate\(-90(?:\.0)? [\d.]+ ([\d.]+)\)', svg))
    chip_y = min(float(m) for m in re.findall(r'<rect[^>]*y="([\d.]+)"[^>]*fill="#2a78d6"', svg))
    assert header_y < chip_y, "the header must clear the chips, not land on them"


def test_a_flat_header_is_centred_and_an_upright_one_is_not():
    """Upright, the text has to grow away from the chips; flat, it reads best centred on them."""
    flat = _three_columns(label_angle=0).as_svg()
    header = [line for line in flat.splitlines() if ">truth<" in line][0]
    assert 'text-anchor="middle"' in header
    assert "rotate(" not in header
    upright = [line for line in _three_columns().as_svg().splitlines() if ">truth<" in line][0]
    assert 'text-anchor="start"' in upright and "rotate(-90" in upright


def test_a_track_with_no_label_writes_nothing_new():
    base = (plot(loads(_TRACK_NWK)) + tip_track(_TRACK_COLUMNS["truth"], palette=_TRACK_PALETTE)).as_svg()
    assert "truth" not in base


def test_a_radial_track_says_the_header_was_dropped():
    """A radial layout fans the chips around the tree, so there is no column to head."""
    fig = (plot(loads(_TRACK_NWK), layout="radial")
           + tip_track(_TRACK_COLUMNS["truth"], palette=_TRACK_PALETTE, label="truth"))
    with pytest.warns(UserWarning, match="radial"):
        svg = fig.as_svg()
    assert "truth" not in svg
    assert svg.count("<rect") >= 4, "the chips are still drawn"


# --- the events key shows the arrow that was drawn (issue #37) -----------------------------------

_EVENT_NWK = "((A:1,B:1)x:1,(C:1.5,D:1.5)y:0.5)r;"
_TRANSFER_INK = "#2e8b57"


def _key_arrows(svg):
    """The shaft of each arrow in the key, as (x1, y1, x2, y2) with the head at the second point.

    The key draws every glyph at stroke-width 2.0 — shaft first, then its two barbs — while the
    marks on the tree scale their width with the event size."""
    paths = re.findall(r'<path d="M([\d.]+),([\d.]+) L([\d.]+),([\d.]+)" stroke="'
                       + _TRANSFER_INK + r'" stroke-width="2.0"', svg)
    return [tuple(float(v) for v in p) for p in paths[0::3]]


def _key_svg(events, **kw):
    return (plot(loads(_EVENT_NWK))
            + branch_events(events, legend_loc="bottom-left", **kw)).as_svg()


def test_a_transfer_from_outside_the_tree_gets_a_vertical_key():
    """It is drawn as a short arrow onto the branch, coming down from above; the key said ->."""
    (x1, y1, x2, y2), = _key_arrows(_key_svg([{"kind": "transfer", "recipient": "x", "x": 0.6}]))
    assert x1 == x2, "the mark points onto the branch, so the key has to as well"
    assert y2 > y1, "arriving from above, it points down"


def test_an_outside_transfer_from_below_points_up():
    svg = _key_svg([{"kind": "transfer", "recipient": "x", "x": 0.6, "side": "below"}])
    (x1, y1, x2, y2), = _key_arrows(svg)
    assert x1 == x2 and y2 < y1


def test_a_transfer_between_two_lineages_keeps_its_horizontal_key():
    svg = _key_svg([{"kind": "transfer", "donor": "A", "recipient": "C", "x": 1.8}])
    (x1, y1, x2, y2), = _key_arrows(svg)
    assert y1 == y2 and x2 > x1


def test_a_kind_drawn_both_ways_shows_both_glyphs():
    svg = _key_svg([{"kind": "transfer", "recipient": "x", "x": 0.6},
                       {"kind": "transfer", "donor": "A", "recipient": "C", "x": 1.8}])
    arrows = _key_arrows(svg)
    assert len(arrows) == 2
    flat, upright = arrows
    assert flat[1] == flat[3], "the donor -> recipient form first"
    assert upright[0] == upright[2], "then the one from outside the tree"
    assert upright[0] > flat[2], "side by side on the row, not on top of each other"


def test_both_glyphs_do_not_run_into_the_label():
    svg = _key_svg([{"kind": "transfer", "recipient": "x", "x": 0.6},
                       {"kind": "transfer", "donor": "A", "recipient": "C", "x": 1.8}])
    label_x = float(re.search(r'<text x="([\d.]+)"[^>]*>transfer<', svg).group(1))
    assert label_x > max(a[2] for a in _key_arrows(svg))


def test_the_other_kinds_are_untouched_by_the_arrow_forms():
    svg = _key_svg([{"kind": "transfer", "recipient": "x", "x": 0.6},
                       {"kind": "duplication", "node": "y", "x": 1.0}])
    assert ">duplication<" in svg and ">transfer<" in svg
    assert len(_key_arrows(svg)) == 1, "the duplication row is a marker, not an arrow"


# --- a colorbar that covers a branch says so (issue #39) -----------------------------------------

_BAR_NWK = "((A:0.9,B:0.95)x:0.3,((C:0.3,D:0.35)y:0.4,(E:0.1,F:0.1)z:0.6)w:0.1)r;"
_BAR_VALUES = {"A": 0.2, "B": 0.2, "x": 0.2, "C": 0.9, "D": 0.9, "y": 0.9,
               "E": 0.9, "F": 0.9, "z": 0.9, "w": 0.6, "r": 0.3}


def _with_colorbar(**kw):
    return (plot(loads(_BAR_NWK), style=Style(width=700, height=400))
            + color_branches(_BAR_VALUES, cmap="viridis", limits=(0, 1), gradient=False)
            + tip_labels() + colorbar("value", **kw))


def test_a_colorbar_that_covers_a_branch_names_it():
    """On a ladderized tree whose first tips are long, the bar sits on the branch to their
    ancestor and the pair looks detached. `legend` warned here; the bar said nothing."""
    with pytest.warns(UserWarning, match="top-left") as caught:
        _with_colorbar(loc="top-left").as_svg()
    assert "(x)" in str(caught[0].message)


def test_a_colorbar_in_a_free_corner_stays_quiet():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _with_colorbar(loc="bottom-left").as_svg()


def test_the_colorbar_warning_names_the_corner_to_move_to():
    """`loc='auto'` is the legend's answer and the bar has none, so the advice has to differ."""
    with pytest.warns(UserWarning) as caught:
        _with_colorbar(loc="top-left").as_svg()
    message = str(caught[0].message)
    assert "Move it to bottom-left." in message and "auto" not in message


def test_a_colorbar_only_takes_the_two_left_corners():
    """A right-hand corner was accepted and then drawn on the left, which is worse than an error."""
    with pytest.raises(ValueError, match="top-left, bottom-left"):
        colorbar("value", loc="top-right")
    assert callable(colorbar("value", loc="bottom-left"))


def test_the_legend_keeps_its_own_advice():
    with pytest.warns(UserWarning, match="loc='auto'"):
        _with_legend(loc="bottom-left").as_svg()


# --- a key outside the panel, where no tree shape can cover it (issue #40) ----------------------

_OUT_NWK = "(((A:3,B:3):1,(C:2,D:2):2):1,((E:3,F:3):2,(G:4,H:4):1):0);"
_OUT_KINDS = {n: "clade one" if n in "ABCD" else "clade two" for n in "ABCDEFGH"}
_OUT_PALETTE = {"clade one": "#D55E00", "clade two": "#0072B2"}


def _outside_figure(style, *layers):
    figure = (plot(loads(_OUT_NWK), style=style)
              + color_branches(_OUT_KINDS, palette=_OUT_PALETTE) + tip_labels())
    for layer in layers:
        figure = figure + layer
    return figure


def _texts(svg):
    return [(float(m.group(1)), float(m.group(2)), m.group(3)) for m in
            re.finditer(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]*)</text>', svg)]


def test_a_key_on_the_right_clears_the_tip_labels():
    """Which corner is free depends on the tree; outside the panel nothing is covered at all."""
    style = Style(width=640, height=360, margin=40, margin_right=170)
    svg = _outside_figure(style, legend("clade", loc="right")).as_svg()
    entries = [x for x, _, text in _texts(svg) if text == "clade one"]
    names = [x for x, _, text in _texts(svg) if text in set("ABCDEFGH")]
    assert entries and max(names) < min(entries), "the key starts past the longest tip label"


def test_a_key_below_clears_the_time_axis():
    style = Style(width=560, height=440, margin=40, margin_bottom=140)
    svg = _outside_figure(style, time_axis("time"), legend("clade", loc="below")).as_svg()
    axis = max(y for _, y, text in _texts(svg) if text == "time")
    key = min(y for _, y, text in _texts(svg) if text == "clade one")
    assert key > axis, "the key goes under the axis, not on it"


def test_two_blocks_below_stack_instead_of_landing_on_each_other():
    style = Style(width=560, height=460, margin=40, margin_bottom=150)
    svg = _outside_figure(style, time_axis("time"), legend("clade", loc="below"),
                          note("ALE, relaxed clock", loc="below")).as_svg()
    key = max(y for _, y, text in _texts(svg) if text == "clade two")
    said = min(y for _, y, text in _texts(svg) if text == "ALE, relaxed clock")
    assert said > key, "the note stacks under the key, in the order they were added"


def test_an_outside_key_never_warns_about_covering_a_branch():
    """On this tree every corner holds a branch or a label; outside the panel there is nothing to
    measure, so there is nothing to say."""
    style = Style(width=400, height=260, margin=30, margin_right=190)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _outside_figure(style, legend("clade", loc="right", size=13)).as_svg()


def test_a_margin_too_thin_says_how_wide_it_has_to_be():
    """The canvas size is fixed before any layer runs, so the key cannot widen the margin itself."""
    style = Style(width=560, height=360, margin=40)
    with pytest.warns(UserWarning, match=r"margin_right=\d+") as caught:
        _outside_figure(style, legend("clade", loc="right")).as_svg()
    assert "runs off the page" in str(caught[0].message)


def test_a_bottom_margin_too_thin_says_so_too():
    style = Style(width=560, height=360, margin=30)
    with pytest.warns(UserWarning, match=r"margin_bottom=\d+"):
        _outside_figure(style, time_axis(), legend("clade", loc="below")).as_svg()


def test_a_note_takes_the_two_outside_places_and_a_colorbar_does_not():
    assert callable(note("x", loc="right"))
    assert callable(note("x", loc="below"))
    with pytest.raises(ValueError, match="top-left, bottom-left"):
        colorbar("v", loc="below")


def test_branch_events_can_put_its_key_outside_too():
    events = [{"kind": "transfer", "donor": "A", "recipient": "H", "x": 4.5},
              {"kind": "duplication", "node": "C", "x": 3.0}]
    style = Style(width=640, height=380, margin=40, margin_right=150)
    figure = (plot(loads(_OUT_NWK), style=style) + tip_labels()
              + branch_events(events, legend_loc="right"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        svg = figure.as_svg()
    key = [x for x, _, text in _texts(svg) if text == "transfer"]
    names = [x for x, _, text in _texts(svg) if text in set("ABCDEFGH")]
    assert key and max(names) < min(key)


def test_a_margin_claim_is_the_furthest_one():
    """So the order the layers were added in does not move the key."""
    from phylustrator.render import Canvas
    canvas = Canvas(Style(), (0.0, 1.0), (0.0, 1.0))
    assert canvas.claimed("right", 42.0) == 42.0
    canvas.claim("right", 100.0)
    canvas.claim("right", 60.0)
    assert canvas.claimed("right", 42.0) == 100.0
    with pytest.raises(ValueError, match="'right' or 'bottom'"):
        canvas.claim("left", 10.0)


# --- an arbitrary path, for the shapes nothing here names (issue #42) ---------------------------


def _canvas(**style):
    from phylustrator.render import Canvas
    return Canvas(Style(width=200, height=120, **style), (0.0, 1.0), (0.0, 1.0))


def _path_line(svg):
    return [line for line in svg.splitlines() if "<path" in line][-1]


def test_a_path_reaches_the_page_as_it_was_written():
    """The one place in the library where the caller owns the geometry: a rounded bend or a tube's
    outline has no named shape to ask for, and the alternative was splicing SVG into as_svg()."""
    canvas = _canvas()
    d = "M 10,10 L 60,10 Q 70,10 70,20 L 70,70"
    canvas.raw_path(d, stroke="#111111", stroke_width=3.0)
    assert f'd="{d}"' in _path_line(canvas.as_svg())


def test_a_path_is_stroked_and_unfilled_unless_it_is_told_otherwise():
    canvas = _canvas()
    canvas.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0)
    line = _path_line(canvas.as_svg())
    assert 'fill="none"' in line and 'stroke="#111111"' in line


def test_a_path_ends_the_way_the_style_says():
    """A tube in a LaTeX figure wants square ends and angular corners; the default is round."""
    rounded = _canvas()
    rounded.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0)
    assert 'stroke-linecap="round"' in _path_line(rounded.as_svg())
    flat = _canvas(line_cap="butt")
    flat.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0)
    assert 'stroke-linecap="butt"' in _path_line(flat.as_svg())
    corner = _canvas()
    corner.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0, join="miter", cap="square")
    line = _path_line(corner.as_svg())
    assert 'stroke-linejoin="miter"' in line and 'stroke-linecap="square"' in line


def test_a_path_can_be_dashed_and_faded():
    canvas = _canvas()
    canvas.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0, dash="5,4", opacity=0.4)
    line = _path_line(canvas.as_svg())
    assert 'stroke-dasharray="5,4"' in line
    assert 'stroke-opacity="0.4"' in line and 'fill-opacity="0.4"' in line


def test_an_opaque_path_writes_no_opacity_at_all():
    canvas = _canvas()
    canvas.raw_path("M 0,0 L 10,10", stroke="#111111", stroke_width=2.0)
    assert "opacity" not in _path_line(canvas.as_svg())


def test_a_tube_can_be_drawn_with_two_passes_of_one_path():
    """The shape issue #42 wrote by hand: each branch drawn wide in the outline colour and again
    narrower in the fill, so neighbouring branches merge into one tube."""
    canvas = _canvas()
    bend = "M 20,20 L 80,20 Q 90,20 90,30 L 90,90"
    canvas.raw_path(bend, stroke="#1a1a1a", stroke_width=14.0)
    canvas.raw_path(bend, stroke="#ffffff", stroke_width=11.0)
    svg = canvas.as_svg()
    assert svg.count(f'd="{bend}"') == 2


# --- auto measures the tip names too, not only the branches (issue #36) --------------------------

_LONG_NWK = "((((A:0.9,B:0.95)x:0.1,(C:0.8,D:0.85)y:0.1):0.1,(E:0.3,F:0.35):0.6):0.1,(G:0.1,H:0.1):0.9);"
_LONG_NAMES = {n: f"Some long species name {n}" for n in "ABCDEFGH"}


def _long_figure(loc, labels_first=True, **kw):
    figure = (plot(loads(_LONG_NWK), style=Style(width=700, height=400, margin_right=120))
              + color_branches({n: "k1" if n in "ABCD" else "k2" for n in "ABCDEFGH"},
                               palette={"k1": "#D55E00", "k2": "#0072B2"}))
    names = tip_labels(values=_LONG_NAMES)
    key = legend("kind", loc=loc, **kw)
    return (figure + names + key) if labels_first else (figure + key + names)


def test_a_key_on_the_tip_names_says_so():
    """The corner was free of branches and covered several names, and nothing said a word."""
    with pytest.warns(UserWarning, match="tip label") as caught:
        _long_figure("bottom-right").as_svg()
    assert "bottom-right" in str(caught[0].message)


def test_auto_now_counts_the_names_as_well_as_the_branches():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _long_figure("auto").as_svg()


def test_the_warning_names_both_when_it_covers_both():
    figure = (plot(loads(_HIDE_NWK), style=Style(width=420, height=260))
              + color_branches(_HIDE_VALUES, palette=_HIDE_PALETTE)
              + tip_labels(values={n: f"long name {n}" for n in "ABCDEF"})
              + legend("", loc="bottom-right", size=14))
    with pytest.warns(UserWarning) as caught:
        figure.as_svg()
    message = str(caught[0].message)
    assert "branch(es)" in message and "tip label(s)" in message


def test_a_key_added_before_the_names_cannot_know_about_them():
    """The names are measured by the layer that writes them, so one added later is not seen. The
    order is the natural one; this pins the behaviour rather than endorsing it."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _long_figure("bottom-right", labels_first=False).as_svg()
    assert not any("tip label" in str(w.message) for w in caught)


def test_the_canvas_keeps_the_boxes_it_is_given():
    from phylustrator.render import Canvas
    canvas = Canvas(Style(), (0.0, 1.0), (0.0, 1.0))
    assert canvas.obstacles() == []
    canvas.obstruct(30, 10, 10, 20)                 # given corner-first, kept as a box
    assert canvas.obstacles() == [(10.0, 10.0, 30.0, 20.0)]


# --- the scale bar can sit outside the panel too (issue #56) -------------------------------------


def _bar_line(svg):
    """The scale bar: the one 1.6-wide ink line."""
    found = re.findall(r'<path d="M ?([-\d.]+),([-\d.]+) L ?([-\d.]+),([-\d.]+)"'
                       r'[^>]*stroke="#333333" stroke-width="1.6"', svg)
    assert found, "no scale bar"
    return tuple(float(v) for v in found[-1])


def _turned(loc):
    style = Style(width=460, height=400, margin=50, margin_bottom=110)
    return (plot(loads("((A:1,B:1)ab:1,(C:1,D:1)cd:1)root:0.3;"), layout="diagonal",
                 orientation="down", style=style)
            + tip_labels() + scale_bar(loc=loc))


def test_a_scale_bar_below_clears_the_tip_names():
    """On a tree that grows down the page every tip is along the bottom, so both bottom corners
    hold a name and the bar lands beside one."""
    figure = _turned("below")
    svg = figure.as_svg()
    _, bar_y, _, _ = _bar_line(svg)
    lowest_name = max(float(m) for m in re.findall(r'<text x="[-\d.]+" y="([-\d.]+)"', svg))
    assert bar_y > lowest_name


def test_a_scale_bar_in_a_corner_is_where_it_always_was():
    figure = _turned("bottom-right")
    x0, y, x1, _ = _bar_line(figure.as_svg())
    assert x1 == pytest.approx(460 - 50)
    assert y == pytest.approx(400 - 110 * 0.5)


def test_a_left_corner_draws_on_the_left():
    x0, _, x1, _ = _bar_line(_turned("bottom-left").as_svg())
    assert x0 == pytest.approx(50.0), "the bar starts on the left margin"


def test_a_scale_bar_takes_the_same_places_the_key_does():
    assert callable(scale_bar(loc="right"))
    with pytest.raises(ValueError, match="loc must be one of"):
        scale_bar(loc="middle")


def test_the_command_line_puts_a_turned_tree_s_bar_below_it(tmp_path):
    from phylustrator.cli import main
    nwk = tmp_path / "t.nwk"
    nwk.write_text("((A:1,B:1)ab:1,(C:1,D:1)cd:1)root:0.3;\n")
    out = tmp_path / "t.svg"
    main([str(nwk), "--layout", "diagonal", "--orientation", "down", "-o", str(out)])
    svg = out.read_text()
    _, bar_y, _, _ = _bar_line(svg)
    lowest_name = max(float(m) for m in re.findall(r'<text x="[-\d.]+" y="([-\d.]+)"', svg))
    assert bar_y > lowest_name
