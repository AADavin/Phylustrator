"""The diagonal layout, its orientations, and the LaTeX/TikZ style preset (issue #44).

A diagonal tree carries the same coordinates as a rectangular one — depth from the origin, tip order
across — and differs in the drawing: one straight segment per branch, no right-angle connector. It is
also the one layout that turns, which is why it is a layout and not a rotation of the finished
drawing: a rotation would lay every tip label on its side.
"""

from __future__ import annotations

import re
import warnings

import pytest

import phylustrator as ph
from phylustrator import Style
from phylustrator.trees import (
    branch_events,
    legend,
    loads,
    node_intervals,
    node_labels,
    plot,
    time_axis,
    tip_labels,
    tip_track,
)
from phylustrator.trees.layout import diagonal, rectangular

_NWK = "((A:1,B:1)ab:1,(C:1,D:1)cd:1)root:0.3;"
_EVENT_NWK = "(((A:0.45,B:0.45)ab:0.25,C:0.7)abc:0.3,(D:0.5,E:0.5)de:0.5)root:0.15;"


def _named(tree):
    return {n.name: n for n in tree.walk() if n.name}


# --- the geometry ---------------------------------------------------------------------------


def test_depth_and_tip_order_swap_axes_but_the_tree_does_not_change():
    tree = loads(_NWK)
    names = _named(tree)
    across, along = {}, {}
    for orientation in ("right", "down", "left", "up"):
        layout = diagonal(tree, orientation=orientation)
        a = names["A"]
        along[orientation] = layout.depth(a)
        across[orientation] = layout.x(a) if not layout.grows_along_x else layout.y(a)
    assert len(set(along.values())) == 1, "depth is the tree's, not the page's"
    assert len(set(across.values())) == 1, "and so is tip order: a turned tree is not a mirrored one"


def test_a_turned_tree_puts_depth_on_the_other_axis():
    tree = loads(_NWK)
    names = _named(tree)
    right, down = diagonal(tree, orientation="right"), diagonal(tree, orientation="down")
    assert right.x(names["A"]) == pytest.approx(down.y(names["A"]))
    assert right.y(names["A"]) == pytest.approx(down.x(names["A"]))
    assert right.grows_along_x and not down.grows_along_x


def test_left_and_up_flip_the_depth_rather_than_the_tip_order():
    tree = loads(_NWK)
    names = _named(tree)
    assert diagonal(tree, orientation="left").x(names["A"]) < 0
    assert diagonal(tree, orientation="up").y(names["A"]) < 0
    for orientation in ("left", "up"):
        layout = diagonal(tree, orientation=orientation)
        tips = [layout.y(leaf) if layout.grows_along_x else layout.x(leaf) for leaf in tree.leaves]
        assert tips == sorted(tips), "the tips stay in the order they were read"


def test_the_extent_reaches_back_to_the_start_of_the_stem():
    """The stem is drawn back from the root to depth 0; an extent that stopped at the root would
    run it off the page."""
    tree = loads(_NWK)                                   # root:0.3 — the stem is 0.3 long
    assert diagonal(tree, orientation="right").xlim[0] == 0.0
    assert diagonal(tree, orientation="down").ylim[0] == 0.0
    assert diagonal(tree, orientation="left").xlim[1] == 0.0


def test_the_coordinates_are_the_rectangular_ones():
    tree = loads(_NWK)
    flat, slant = rectangular(tree), diagonal(tree, orientation="right")
    for node in tree.walk():
        assert (flat.x(node), flat.y(node)) == pytest.approx((slant.x(node), slant.y(node)))


def test_a_cladogram_spaces_by_depth_here_too():
    tree = loads("((((a:1,b:1):0.01,(c:1,d:1):0.01):0.01,(e:1,f:1):0.01):0.01,g:1);")
    layout = diagonal(tree, cladogram=True, orientation="down")
    depths = {leaf.name: layout.depth(leaf) for leaf in tree.leaves}
    assert depths["a"] == pytest.approx(4.0) and depths["g"] == pytest.approx(1.0)


# --- the drawing ----------------------------------------------------------------------------


def _lines(svg):
    return re.findall(r'<path d="M([-\d.]+),([-\d.]+) L([-\d.]+),([-\d.]+)"', svg)


def test_a_diagonal_tree_has_one_segment_per_branch_and_no_connectors():
    """The rectangular drawing spends a line on each branch and another on each drop into a child;
    the diagonal one joins parent to child directly, which is the whole difference."""
    tree = loads(_NWK)
    slant = len(_lines(plot(tree, layout="diagonal").as_svg()))
    flat = len(_lines(plot(tree).as_svg()))
    branches = sum(1 for node in tree.walk() if not node.is_root)
    assert slant == branches + 1, "every branch, plus the stem"
    assert flat > slant


def test_every_segment_ends_on_its_parent():
    tree = loads(_NWK)
    figure = plot(tree, layout="diagonal", orientation="down")
    seen = {(round(float(a), 3), round(float(b), 3), round(float(c), 3), round(float(d), 3))
            for a, b, c, d in _lines(figure.as_svg())}
    nodes = {n.name: (round(p.x, 3), round(p.y, 3))
             for n, p in zip(tree.walk(), figure.geometry().nodes)}
    assert (*nodes["root"], *nodes["ab"]) in seen
    assert (*nodes["ab"], *nodes["A"]) in seen


def test_only_the_diagonal_layout_turns():
    with pytest.raises(ValueError, match="always grows to the right"):
        plot(loads(_NWK), layout="rectangular", orientation="down")
    with pytest.raises(ValueError, match="orientation must be one of"):
        plot(loads(_NWK), layout="diagonal", orientation="sideways").as_svg()


def test_the_orientation_survives_adding_layers():
    figure = plot(loads(_NWK), layout="diagonal", orientation="down") + tip_labels()
    assert figure.orientation == "down"
    assert figure.with_style(Style(width=300, height=300)).orientation == "down"


# --- what the layers do with a turned tree ----------------------------------------------------


def _label_of(svg, name):
    return re.search(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>' + name + r"</text>", svg)


def test_a_turned_tree_keeps_its_names_upright_and_under_the_tips():
    """Rotating the finished drawing would turn the names on their side. This is why the turn is a
    layout: the geometry moves and the text does not."""
    figure = plot(loads(_NWK), layout="diagonal", orientation="down") + tip_labels()
    svg = figure.as_svg()
    written = [line for line in svg.splitlines() if ">A</text>" in line][0]
    assert "rotate(" not in written
    assert 'text-anchor="middle"' in written
    tip = next(p for p in figure.geometry().tips if p.name == "A")
    assert float(_label_of(svg, "A").group(2)) > tip.y, "below the tip, not beside it"


def test_names_sit_beside_the_tips_of_a_right_facing_tree():
    figure = plot(loads(_NWK), layout="diagonal") + tip_labels()
    svg = figure.as_svg()
    tip = next(p for p in figure.geometry().tips if p.name == "A")
    assert float(_label_of(svg, "A").group(1)) > tip.x
    assert 'text-anchor="start"' in [line for line in svg.splitlines() if ">A</text>" in line][0]


def test_a_node_name_clears_the_fork_on_a_turned_tree():
    """Above-left of a node is on top of its own branch once the tree runs down the page."""
    figure = plot(loads(_NWK), layout="diagonal", orientation="down") + node_labels()
    svg = figure.as_svg()
    node = next(p for p in figure.geometry().nodes if p.name == "ab")
    assert float(_label_of(svg, "ab").group(1)) > node.x


def test_chips_go_under_the_tips_of_a_turned_tree():
    tree = loads(_NWK)
    values = {"A": "yes", "B": "no", "C": "yes", "D": "no"}
    palette = {"yes": "#2a78d6", "no": "#ffffff"}
    figure = plot(tree, layout="diagonal", orientation="down") + tip_track(values, palette=palette)
    chips = re.findall(r'<rect x="([-\d.]+)" y="([-\d.]+)"[^>]*fill="#2a78d6"', figure.as_svg())
    tip = next(p for p in figure.geometry().tips if p.name == "A")
    assert any(float(y) > tip.y for _, y in chips)


def test_a_column_header_is_dropped_on_a_turned_tree():
    """Down the page the chips are a row, and a row has no column to head."""
    figure = (plot(loads(_NWK), layout="diagonal", orientation="down")
              + tip_track({"A": 1, "B": 2, "C": 3, "D": 4}, label="truth"))
    with pytest.warns(UserWarning, match="row and not a column"):
        assert "truth" not in figure.as_svg()


def test_a_right_facing_tree_still_heads_its_column():
    figure = (plot(loads(_NWK), layout="diagonal")
              + tip_track({"A": 1, "B": 2, "C": 3, "D": 4}, label="truth"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert "truth" in figure.as_svg()


def test_a_legend_still_measures_the_branches_it_covers():
    """The coverage check walks parent to child for any layout it does not know, which is what a
    diagonal branch is, so the key keeps working without a case of its own."""
    figure = (plot(loads(_NWK), layout="diagonal", style=Style(width=300, height=200))
              + legend("k", entries={"a very long category label indeed": "#111111"},
                       loc="bottom-left", size=14))
    with pytest.warns(UserWarning, match="covers"):
        figure.as_svg()


# --- events on a slanted branch ---------------------------------------------------------------


def _square(svg):
    found = re.search(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)"[^>]*fill="#3a7ca5"', svg)
    assert found, "no duplication marker"
    x, y, side = (float(v) for v in found.groups())
    return x + side / 2, y + side / 2          # the marker's centre, not its corner


def _on_the_branch(figure, tree, name, depth):
    """Where an event at ``depth`` on ``name``'s branch belongs, in pixels."""
    nodes = {n.name: p for n, p in zip(tree.walk(), figure.geometry().nodes)}
    node = _named(tree)[name]
    layout = diagonal(tree, orientation=figure.orientation)
    lo, hi = layout.depth(node.parent), layout.depth(node)
    f = (depth - lo) / (hi - lo)
    start, end = nodes[node.parent.name], nodes[name]
    return start.x + f * (end.x - start.x), start.y + f * (end.y - start.y)


@pytest.mark.parametrize("orientation", ["right", "down", "left", "up"])
def test_a_point_event_lands_on_the_slanted_branch(orientation):
    tree = loads(_EVENT_NWK)
    figure = (plot(tree, layout="diagonal", orientation=orientation)
              + branch_events([{"kind": "duplication", "node": "A", "x": 0.9}], legend=False))
    drawn = _square(figure.as_svg())
    assert drawn == pytest.approx(_on_the_branch(figure, tree, "A", 0.9), abs=1.0)


def test_an_event_past_the_end_of_its_branch_is_pulled_back_onto_it():
    """The clamp reads the branch's depth range. Reading it off the x coordinate was right only for
    a rectangular tree: on a turned one x is the tip order, so every marker clamped to a tip index
    and landed off the tree entirely."""
    tree = loads(_EVENT_NWK)
    figure = (plot(tree, layout="diagonal", orientation="down")
              + branch_events([{"kind": "duplication", "node": "A", "x": 9.0}], legend=False))
    drawn = _square(figure.as_svg())
    tip = next(p for p in figure.geometry().tips if p.name == "A")
    assert drawn == pytest.approx((tip.x, tip.y), abs=1.0), "clamped to the end of its own branch"


def test_a_radial_point_event_still_clamps():
    """The same clamp serves every layout now; the radial branch of it used to be its own code,
    reading a radius the rest of the layer no longer computes."""
    tree = loads(_EVENT_NWK)
    figure = (plot(tree, layout="radial", style=Style(width=400, height=400))
              + branch_events([{"kind": "duplication", "node": "A", "x": 9.0}], legend=False))
    drawn = _square(figure.as_svg())
    tip = next(p for p in figure.geometry().tips if p.name == "A")
    assert drawn == pytest.approx((tip.x, tip.y), abs=1.0), "clamped to the end of A's branch"


def test_a_transfer_crosses_between_two_slanted_branches():
    tree = loads(_EVENT_NWK)
    figure = (plot(tree, layout="diagonal", orientation="down")
              + branch_events([{"kind": "transfer", "donor": "C", "recipient": "D", "x": 0.9}],
                              legend=False))
    assert "#2e8b57" in figure.as_svg()


def test_a_transfer_outside_the_window_is_still_refused():
    tree = loads(_EVENT_NWK)
    with pytest.raises(ValueError, match="outside"):
        (plot(tree, layout="diagonal")
         + branch_events([{"kind": "transfer", "donor": "A", "recipient": "D", "x": 0.2}])).as_svg()


# --- the layers that cannot draw on a turned tree say so --------------------------------------


def test_node_intervals_draws_on_a_diagonal_tree_that_grows_across_the_page():
    """The diagonal layout carries the rectangular coordinates, so the bar runs along the same
    axis it runs along there (#55)."""
    figure = plot(loads(_NWK), layout="diagonal") + node_intervals({"ab": (0.5, 1.5)})
    assert "#6a9bd8" in figure.as_svg()


def test_node_intervals_refuses_a_turned_tree():
    """There the time runs down the page and the bar at a node's row would run across it."""
    with pytest.raises(ValueError, match="carries its time down the page"):
        (plot(loads(_NWK), layout="diagonal", orientation="down")
         + node_intervals({"ab": (0.5, 1.5)})).as_svg()


def test_an_interval_on_a_left_facing_tree_runs_the_other_way():
    """Depth counts the other way along the axis there, and a bar drawn without that lands on the
    far side of the tree."""
    import re
    for orientation, inside in (("right", True), ("left", False)):
        svg = (plot(loads(_NWK), layout="diagonal", orientation=orientation)
               + node_intervals({"ab": (0.5, 1.5)})).as_svg()
        xs = [float(m) for m in re.findall(r'<path d="M ?([-\d.]+),', svg)]
        node_x = next(p.x for p in plot(loads(_NWK), layout="diagonal",
                                        orientation=orientation).geometry().nodes
                      if p.name == "ab")
        bar = [x for x in xs if abs(x - node_x) < 200]
        assert bar, f"a bar is drawn near the node on a {orientation} tree"


def test_a_clade_box_follows_the_orientation():
    """A clade is a box on a diagonal tree too; which axis the tips are spaced along turns."""
    tree = loads("((A:3,B:3)x:1,C:4)r;")
    across = plot(tree, layout="diagonal").clade_box("x")
    down = plot(tree, layout="diagonal", orientation="down").clade_box("x")
    assert across.x1 > across.x0 and across.y1 > across.y0
    assert down.x1 > down.x0 and down.y1 > down.y0


def test_a_clade_box_still_needs_a_tip_order_axis():
    with pytest.raises(ValueError, match="rectangular or diagonal"):
        plot(loads(_NWK), layout="radial").clade_box("ab")


def test_a_time_axis_draws_on_a_right_facing_tree_and_warns_on_a_turned_one():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert "0" in (plot(loads(_NWK), layout="diagonal") + time_axis()).as_svg()
    with pytest.warns(UserWarning, match="down the page"):
        (plot(loads(_NWK), layout="diagonal", orientation="down") + time_axis()).as_svg()


# --- the TikZ preset ------------------------------------------------------------------------


def test_the_preset_is_a_style_with_the_look_already_set():
    style = ph.styles.tikz()
    assert style.branch_color == "#000000" and style.line_cap == "butt"
    assert style.background == "white"


def test_the_preset_takes_overrides():
    assert ph.styles.tikz(branch_width=2.5, font_size=13).branch_width == 2.5
    assert ph.styles.tikz(width=360).width == 360


def test_the_preset_names_one_font_family_not_a_stack():
    """cairosvg takes the whole family string as one name, so a CSS stack misses every entry and
    falls back to a *sans* face — the wrong half of the look, silently, in PNG and PDF."""
    assert "," not in ph.styles.tikz().font_family
    assert "," not in ph.styles.LATEX_SERIF


def test_a_squared_off_branch_reaches_the_page_as_a_butt_cap():
    svg = plot(loads(_NWK), layout="diagonal", style=ph.styles.tikz()).as_svg()
    assert 'stroke-linecap="butt"' in svg
    assert 'stroke-linecap="round"' in plot(loads(_NWK), layout="diagonal").as_svg()


def test_a_dashed_branch_is_squared_off_whatever_the_style_says():
    """Each dash would otherwise grow a cap of its own and the gaps would close up."""
    svg = plot(loads(_NWK), dashed={"A"}, style=Style(line_cap="round")).as_svg()
    dashed = [line for line in svg.splitlines() if "stroke-dasharray" in line]
    assert dashed and all('stroke-linecap="butt"' in line for line in dashed)


def test_the_preset_works_with_every_layout():
    for layout in ("rectangular", "radial", "unrooted", "diagonal"):
        assert plot(loads(_NWK), layout=layout, style=ph.styles.tikz()).as_svg()


# --- the diagram's furniture: dots, maths labels, a tip row ------------------------------------

_DOT_NWK = "((a,b)ab,(c,(d,e)de)cde)r;"


def _dots(svg, color="#333333"):
    return re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([\d.]+)"[^>]*fill="'
                      + color + r'"', svg)


def test_a_dot_goes_on_every_tip_by_default():
    from phylustrator.trees import node_dots
    tree = loads(_DOT_NWK)
    svg = (plot(tree, layout="diagonal", orientation="down") + node_dots()).as_svg()
    assert len(_dots(svg)) == len(tree.leaves)


def test_where_picks_the_group_and_nodes_picks_them_by_name():
    from phylustrator.trees import node_dots
    tree = loads(_DOT_NWK)
    internal = sum(1 for n in tree.walk() if not n.is_leaf)
    assert len(_dots((plot(tree) + node_dots(where="internal")).as_svg())) == internal
    assert len(_dots((plot(tree) + node_dots(where="all")).as_svg())) == len(list(tree.walk()))
    assert len(_dots((plot(tree) + node_dots(where="root")).as_svg())) == 1
    assert len(_dots((plot(tree) + node_dots(["a", "r"])).as_svg())) == 2


def test_a_dot_sits_exactly_on_its_node():
    from phylustrator.trees import node_dots
    tree = loads(_DOT_NWK)
    figure = plot(tree, layout="diagonal", orientation="down") + node_dots(["r"])
    (x, y, _), = _dots(figure.as_svg())
    root = next(p for p in figure.geometry().nodes if p.name == "r")
    assert (float(x), float(y)) == pytest.approx((root.x, root.y), abs=0.5)


def test_a_name_that_is_not_in_the_tree_is_refused():
    from phylustrator.trees import node_dots
    with pytest.raises(ValueError, match="not in the tree"):
        (plot(loads(_DOT_NWK)) + node_dots(["nowhere"])).as_svg()
    with pytest.raises(ValueError, match="where must be one of"):
        node_dots(where="everywhere")


def test_one_node_can_be_starred_out_of_the_rest():
    from phylustrator.trees import node_dots
    svg = (plot(loads(_DOT_NWK), layout="unrooted")
           + node_dots() + node_dots(["ab"], shape="star", size=6)).as_svg()
    stars = [line for line in svg.splitlines() if "<path" in line and line.count(" L") >= 9]
    assert len(stars) == 1, "a five-pointed star is ten points: one path with nine line segments"
    assert len(_dots(svg)) == 5, "and the plain dots are still on the tips"


def test_the_preset_sets_the_names_in_maths_and_leaves_the_title_roman():
    """A LaTeX figure's taxon names are italic and its title is not. The face belongs to the label,
    so the chrome does not come with it."""
    figure = (plot(loads(_DOT_NWK), style=ph.styles.tikz()) + tip_labels()
              + ph.trees.title("Rooted gene tree", weight="normal"))
    svg = figure.as_svg()
    name = [line for line in svg.splitlines() if ">a</text>" in line][0]
    heading = [line for line in svg.splitlines() if "Rooted gene tree" in line][0]
    assert 'font-style="italic"' in name
    assert "font-style" not in heading


def test_a_plain_style_writes_no_font_style_at_all():
    svg = (plot(loads(_DOT_NWK)) + tip_labels()).as_svg()
    assert "font-style" not in svg


def test_aligned_tips_end_every_lineage_on_one_row():
    tree = loads(_DOT_NWK)                               # d and e are one split deeper than a and b
    figure = plot(tree, layout="diagonal", orientation="down", align_tips=True)
    rows = {round(p.y, 3) for p in figure.geometry().tips}
    assert len(rows) == 1
    ragged = {round(p.y, 3) for p in plot(tree, layout="diagonal", orientation="down").geometry().tips}
    assert len(ragged) > 1


def test_aligning_the_tips_leaves_the_internal_nodes_where_they_were():
    """It is a drawing choice, not a transformation of the tree: only the leaves move."""
    tree = loads(_DOT_NWK)
    plain = {p.name: p.x for p in plot(tree).geometry().nodes if not p.is_leaf}
    aligned = {p.name: p.x for p in plot(tree, align_tips=True).geometry().nodes if not p.is_leaf}
    assert plain == aligned


def test_the_unrooted_layout_has_no_tip_row_to_align_to():
    with pytest.raises(ValueError, match="no tip row"):
        plot(loads(_DOT_NWK), layout="unrooted", align_tips=True)


def test_upright_names_on_an_unrooted_tree_do_not_turn():
    """Turned names are what a large circular tree needs; a five-taxon diagram reads straight."""
    svg = (plot(loads(_DOT_NWK), layout="unrooted") + tip_labels(upright=True)).as_svg()
    turned = (plot(loads(_DOT_NWK), layout="unrooted") + tip_labels()).as_svg()
    assert "rotate(" not in svg
    assert "rotate(" in turned


def test_an_upright_name_still_grows_away_from_its_tip():
    tree = loads(_DOT_NWK)
    figure = plot(tree, layout="unrooted") + tip_labels(upright=True)
    svg = figure.as_svg()
    for leaf in tree.leaves:
        written = [line for line in svg.splitlines() if f">{leaf.name}</text>" in line][0]
        x = float(re.search(r'<text x="([-\d.]+)"', written).group(1))
        tip = next(p for p in figure.geometry().tips if p.name == leaf.name)
        anchor = "start" if x >= tip.x else "end"
        assert f'text-anchor="{anchor}"' in written


# --- the maths alphabet, and a font that is not there -------------------------------------------


def test_maths_writes_the_italic_letters_latex_uses():
    assert ph.styles.maths("abc") == "\U0001D44E\U0001D44F\U0001D450"
    assert ph.styles.maths("Z") == "\U0001D44D"


def test_the_h_that_is_not_where_the_arithmetic_says():
    """The slot for italic h is reserved; the character is U+210E, PLANCK CONSTANT. Without this a
    label containing an h comes out blank."""
    assert ph.styles.maths("h") == "ℎ"
    assert ph.styles.maths("hi") == "ℎ\U0001D456"


def test_anything_that_is_not_a_letter_is_left_alone():
    assert ph.styles.maths("H. sapiens 12_3") == ph.styles.maths("H") + ". " + \
        ph.styles.maths("sapiens") + " 12_3"


def test_the_maths_preset_uses_one_font_for_both_faces():
    style = ph.styles.tikz_math()
    assert style.font_family == ph.styles.LATEX_MATH
    assert style.label_style == "normal", "the italic comes from the characters, not from the face"
    assert style.line_cap == "butt", "and the rest of the tikz look is still there"
    assert ph.styles.tikz_math(font_size=20).font_size == 20


def test_a_label_can_be_set_in_its_own_family():
    """A LaTeX figure takes its title from the text font and its names from the maths font."""
    svg = (plot(loads(_DOT_NWK), style=ph.styles.tikz(label_family="Latin Modern Math"))
           + tip_labels() + ph.trees.title("Rooted gene tree")).as_svg()
    name = [line for line in svg.splitlines() if ">a</text>" in line][0]
    heading = [line for line in svg.splitlines() if "Rooted gene tree" in line][0]
    assert 'font-family="Latin Modern Math"' in name
    assert 'font-family="Times New Roman"' in heading


def test_a_missing_font_is_reported_rather_than_quietly_swapped():
    """A family the renderer cannot find is substituted in silence, and the figure comes back in a
    sans face. The probe itself is stubbed here: the point is that save() acts on the answer."""
    from phylustrator import render
    canvas = render.Canvas(Style(font_family="No Such Family 8f3a"), (0.0, 1.0), (0.0, 1.0))
    render._FONT_SEEN.clear()
    render._FONT_SEEN["No Such Family 8f3a"] = False
    with pytest.warns(UserWarning, match="not installed"):
        canvas._warn_about_missing_fonts()
    render._FONT_SEEN.clear()


def test_the_label_family_is_checked_as_well_as_the_title_family():
    from phylustrator import render
    canvas = render.Canvas(Style(font_family="Helvetica", label_family="No Such Family 8f3a"),
                           (0.0, 1.0), (0.0, 1.0))
    render._FONT_SEEN.clear()
    render._FONT_SEEN.update({"Helvetica": True, "No Such Family 8f3a": False})
    with pytest.warns(UserWarning, match="No Such Family"):
        canvas._warn_about_missing_fonts()
    render._FONT_SEEN.clear()


def test_a_font_that_is_there_says_nothing():
    from phylustrator import render
    canvas = render.Canvas(Style(font_family="Some Installed Face"), (0.0, 1.0), (0.0, 1.0))
    render._FONT_SEEN.clear()
    render._FONT_SEEN["Some Installed Face"] = True
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        canvas._warn_about_missing_fonts()
    render._FONT_SEEN.clear()


def test_the_fallback_face_itself_is_not_called_missing():
    """A missing family is drawn in the fallback face, so asking for that face draws the same
    pixels for an honest reason. Reporting it would fire on nearly every default figure."""
    from phylustrator import render
    render._FONT_SEEN.clear()
    for name in ("Helvetica", "helvetica", "DejaVu Sans", "sans-serif"):
        assert render.font_is_available(name) is True
    assert not any(k.startswith("No Such") for k in render._FONT_SEEN)
    render._FONT_SEEN.clear()


def test_an_svg_carries_the_name_and_says_nothing(tmp_path):
    """It is resolved wherever the file is opened, so there is nothing to warn about here."""
    from phylustrator import render
    render._FONT_SEEN.clear()
    render._FONT_SEEN["No Such Family 8f3a"] = False
    figure = plot(loads(_DOT_NWK), style=Style(font_family="No Such Family 8f3a")) + tip_labels()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        figure.save(tmp_path / "out.svg")
    render._FONT_SEEN.clear()


def test_a_probe_that_breaks_answers_yes(monkeypatch):
    """A check that cannot run must not stop a figure from being saved, or a broken renderer
    probe would cost you the figure as well."""
    import cairosvg

    from phylustrator import render
    render._FONT_SEEN.clear()

    def boom(**kw):
        raise RuntimeError("probe broke")

    monkeypatch.setattr(cairosvg, "svg2png", boom)
    assert render.font_is_available("No Such Family 8f3a") is True
    render._FONT_SEEN.clear()


def test_a_family_is_probed_once(monkeypatch):
    """A figure drawn in a loop must not pay for the check every time."""
    import cairosvg

    from phylustrator import render
    render._FONT_SEEN.clear()
    calls = []

    def counted(**kw):
        calls.append(1)
        return b"pretend-png-" + str(len(calls)).encode()

    monkeypatch.setattr(cairosvg, "svg2png", counted)
    render.font_is_available("No Such Family 8f3a")
    first = len(calls)
    assert first == 2, "the family as asked, and the fallback to compare it against"
    render.font_is_available("No Such Family 8f3a")
    assert len(calls) == first, "the answer is remembered"
    render._FONT_SEEN.clear()
