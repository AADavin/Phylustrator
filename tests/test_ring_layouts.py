"""#97: ``ring`` on the layouts its docstring recommends.

It read ``layout.angle``, which only the radial layout fills in, so it raised a bare ``TypeError``
on the three other layouts — including the unrooted one it recommends by name.
"""

from __future__ import annotations

import math
import re

import pytest

from phylustrator import Style
from phylustrator.trees import loads, plot, ring, tip_labels
from phylustrator.trees.layers.tracks import _bands, _tip_angles

_NWK = "(((A:1,B:1):1,(C:1,D:1):1):1,((E:1,F:1):1,(G:1,H:1):1):1);"
_SIDES = {n: ("left" if n in "ABCD" else "right") for n in "ABCDEFGH"}
_PALETTE = {"left": "#2B64A8", "right": "#2E7D3A"}


def _figure(kind, **kw):
    return (plot(loads(_NWK), layout=kind, style=Style(width=480, height=480), **kw)
            + ring(_SIDES, palette=_PALETTE, labels=True))


def _sectors(svg):
    """Every annulus sector, as (fill, the ``A`` arc commands of its path)."""
    out = []
    for d, fill in re.findall(r'<path d="([^"]+)"[^>]*fill="(#[0-9A-Fa-f]{6})"', svg):
        if d.count("A") == 2:
            out.append((fill, d))
    return out


# --- it draws on a round layout -------------------------------------------------------------------

def test_the_unrooted_layout_draws_instead_of_raising():
    svg = _figure("unrooted").as_svg()
    assert len(_sectors(svg)) == 8, "one sector per tip"


def test_both_round_layouts_draw_the_same_number_of_sectors():
    assert len(_sectors(_figure("unrooted").as_svg())) == len(_sectors(_figure("radial").as_svg()))


def test_daylight_is_laid_out_and_ringed_without_complaint():
    svg = _figure("unrooted", daylight=True).as_svg()
    assert len(_sectors(svg)) == 8


_ARC = re.compile(r"M\s*([-\d.]+),([-\d.]+)\s*A[^,]+,[^,]+,0,0,1,([-\d.]+),([-\d.]+)")


def _facing(sector, cx, cy):
    """The middle of a sector's outer arc, as an angle from the tree's centre."""
    x0, y0, x1, y1 = (float(v) for v in _ARC.match(sector).groups())
    return math.atan2((y0 + y1) / 2 - cy, (x0 + x1) / 2 - cx)


def test_a_sector_sits_at_its_own_tip_s_direction():
    """The point of the fix: the angle is read off the coordinates, so each arc faces its tip."""
    figure = _figure("unrooted")
    geometry = figure.geometry()
    root = min(geometry.nodes, key=lambda p: math.hypot(p.x - 240, p.y - 240))
    sectors = _sectors(figure.as_svg())
    for tip in geometry.tips:
        want = math.atan2(tip.y - root.y, tip.x - root.x)
        turn, fill = min((abs(math.atan2(math.sin(want - _facing(d, root.x, root.y)),
                                        math.cos(want - _facing(d, root.x, root.y)))), fill)
                         for fill, d in sectors)
        assert fill == _PALETTE[_SIDES[tip.name]], f"{tip.name} sits in the wrong band"
        assert turn < math.pi / 8, f"{tip.name}'s own arc should be the one facing it"


# --- it refuses on a flat one ---------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["rectangular", "diagonal"])
def test_a_flat_layout_is_refused_in_words(kind):
    with pytest.raises(ValueError) as complaint:
        _figure(kind).as_svg()
    said = str(complaint.value)
    assert kind in said and "radial" in said and "unrooted" in said
    assert "centre" in said, "it should say why, not just which"


# --- the angles -----------------------------------------------------------------------------------

def test_the_radial_layout_keeps_its_own_angles():
    """Monotonic, with no atan2 wrap: the fix must not take that away from it."""
    from phylustrator.trees.layout import radial

    tree = loads(_NWK)
    layout = radial(tree)
    assert _tip_angles(layout, tree.leaves) == {lf.name: layout.angle[lf] for lf in tree.leaves}


def test_an_unrooted_angle_is_the_tip_s_direction_from_the_root():
    from phylustrator.trees.layout import unrooted

    tree = loads(_NWK)
    layout = unrooted(tree)
    angles = _tip_angles(layout, tree.leaves)
    for leaf in tree.leaves:
        want = math.atan2(layout.y(leaf), layout.x(leaf)) % (2 * math.pi)
        assert angles[leaf.name] == pytest.approx(want)
    assert all(0.0 <= a < 2 * math.pi for a in angles.values()), "one turn, so sorting is cyclic"


# --- a band that straddles the wrap ---------------------------------------------------------------

class _Leaf:
    def __init__(self, name):
        self.name = name


def _runs(order, values, **kw):
    tips = [_Leaf(n) for n in order]
    colors = dict.fromkeys(order, "#000000")
    return _bands(tips, colors, values, **kw)


def test_an_open_ring_keeps_the_two_end_runs_apart():
    """A radial tree leaves a seam, so the first and last tips are not neighbours."""
    values = {"A": "x", "B": "y", "C": "y", "D": "x"}
    assert [r[0] for r in _runs("ABCD", values)] == ["x", "y", "x"]


def test_a_closed_ring_joins_a_band_that_straddles_the_wrap():
    values = {"A": "x", "B": "y", "C": "y", "D": "x"}
    runs = _runs("ABCD", values, closed=True)
    assert [r[0] for r in runs] == ["y", "x"]
    assert runs[-1] == ("x", 3, 4), "D..A, its last index one turn past the start"


def test_a_closed_ring_leaves_unlike_ends_alone():
    values = {"A": "x", "B": "x", "C": "y", "D": "y"}
    assert [r[0] for r in _runs("ABCD", values, closed=True)] == ["x", "y"]


def test_one_band_all_the_way_round_is_not_merged_with_itself():
    assert _runs("ABCD", dict.fromkeys("ABCD", "x"), closed=True) == [("x", 0, 3)]


def test_a_straddling_band_is_named_once_on_the_tree():
    """The band running across the zero direction is one band, so it is named once and not twice."""
    from phylustrator.trees.layout import unrooted

    tree = loads(_NWK)
    layout = unrooted(tree, daylight=True)
    angles = _tip_angles(layout, tree.leaves)
    order = sorted((lf.name for lf in tree.leaves), key=lambda n: angles[n])
    straddling = {order[-2], order[-1], order[0]}      # over the wrap, on purpose
    sides = {n: ("one" if n in straddling else "two") for n in order}
    svg = (plot(tree, layout="unrooted", daylight=True, style=Style(width=480, height=480))
           + ring(sides, palette={"one": "#2B64A8", "two": "#2E7D3A"}, labels=True)).as_svg()
    assert svg.count(">one</text>") == 1, "one band, one name"
    assert svg.count(">two</text>") == 1


def test_the_ring_and_the_names_compose_on_an_unrooted_tree():
    svg = (_figure("unrooted", daylight=True) + tip_labels()).as_svg()
    for name in "ABCDEFGH":
        assert f">{name}</text>" in svg
