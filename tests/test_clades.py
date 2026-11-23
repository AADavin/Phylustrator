"""highlight_clade: a box, a wedge or a hull, and the pixel corners a zoom line is drawn to."""
import re

import pytest

from phylustrator import Style
from phylustrator.trees import highlight_clade, loads, plot

NWK = "(((a:1,b:1)ab:1,(c:1,d:1)cd:1)abcd:1,((e:1,f:1)ef:1.2,(g:1,h:1)gh:0.8)efgh:0.9)r:0.3;"


def _points(d):
    return [(float(x), float(y)) for x, y in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)]


class _Recorder:
    """A canvas stand-in that records the shapes a layer asks for, in layout coordinates."""

    def __init__(self):
        self.sectors, self.polygons = [], []
        self.regions = []

    def px(self, x):
        return x

    def py(self, y):
        return y

    def raw_annulus_sector(self, cx, cy, r_in, r_out, a0, a1, **kw):
        self.sectors.append((r_in, r_out, a0, a1))

    def raw_polygon(self, points, **kw):
        self.polygons.append(list(points))

    def region(self, *a, **kw):
        self.regions.append(a)


def _drawn(clade, layout_kind):
    from phylustrator.style import Style
    from phylustrator.trees.layout import radial, unrooted

    tree = loads(NWK)
    layout = radial(tree) if layout_kind == "radial" else unrooted(tree)
    canvas = _Recorder()
    highlight_clade(clade, color="#FDBF6F")(canvas, tree, layout, Style())
    return canvas


def _area(points):
    """The polygon's area, by the shoelace formula."""
    total = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        total += x0 * y1 - x1 * y0
    return abs(total) / 2


def test_a_clade_is_marked_in_every_layout():
    """It drew on the rectangular layout and returned silently on the other two."""
    for layout in ("rectangular", "radial", "unrooted"):
        svg = (plot(loads(NWK), layout=layout) + highlight_clade("ab", color="#FDBF6F")).as_svg()
        assert "#FDBF6F" in svg, f"nothing was drawn on the {layout} layout"


def test_a_clade_can_be_outlined_instead_of_filled():
    """An outline is the usual mark for 'this clade is drawn enlarged in the next panel'."""
    svg = (plot(loads(NWK)) + highlight_clade("ab", color="none", stroke="#c1443c",
                                              stroke_width=1.4)).as_svg()
    assert 'stroke="#c1443c"' in svg and 'fill="none"' in svg


def test_the_box_a_zoom_line_points_at_is_the_box_on_the_page():
    fig = (plot(loads(NWK), style=Style(width=400, height=300))
           + highlight_clade("ab", color="#FDBF6F"))
    box = fig.clade_box("ab")
    drawn = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" '
                      r'fill="#FDBF6F"', fig.as_svg())
    assert drawn, "the clade was not drawn as a box"
    x, y, w, h = (float(v) for v in drawn.groups())
    assert (x, y) == pytest.approx((box.x0, box.y0))
    assert (x + w, y + h) == pytest.approx((box.x1, box.y1))
    assert box.corners[0] == (box.x0, box.y0) and len(box.corners) == 4


def test_a_clade_box_needs_the_layout_that_has_one():
    with pytest.raises(ValueError, match="rectangular"):
        plot(loads(NWK), layout="radial").clade_box("ab")


def test_a_name_that_is_not_in_the_tree_is_refused():
    """It drew nothing at all, which reads as a clade not worth marking rather than as a typo."""
    with pytest.raises(ValueError, match="no node named"):
        (plot(loads(NWK)) + highlight_clade("zz")).as_svg()
    with pytest.raises(ValueError, match="no node named"):
        plot(loads(NWK)).clade_box("zz")


def test_a_wedge_spans_its_own_tips_and_no_more():
    """The wedge runs between the clade's first and last tip, not across the whole circle."""
    import math

    from phylustrator.trees.layout import radial

    tree = loads(NWK)
    layout = radial(tree)
    (_, _, a0, a1), = _drawn("ab", "radial").sectors
    (_, _, b0, b1), = _drawn("efgh", "radial").sectors
    tips = {"a", "b", "e", "f", "g", "h"}
    angles = {n.name: layout.angle[n] for n in tree.leaves if n.name in tips}
    assert a1 - a0 >= angles["b"] - angles["a"], "the wedge is narrower than its own clade"
    assert b1 - b0 >= angles["h"] - angles["e"]
    assert b1 - b0 > a1 - a0, "four tips must take more of the circle than two"
    assert b1 - b0 < 2 * math.pi


def test_a_wedge_reaches_from_the_clades_node_out_to_its_tips():
    r_in, r_out, _, _ = _drawn("ab", "radial").sectors[0]
    assert 0 <= r_in < r_out


def test_an_unrooted_hull_wraps_the_clade_and_nothing_else():
    small, = _drawn("ab", "unrooted").polygons
    large, = _drawn("efgh", "unrooted").polygons
    assert len(small) >= 3 and _area(large) > _area(small)


@pytest.mark.parametrize("kind", ["rectangular", "diagonal"])
@pytest.mark.parametrize("orientation", ["right", "left", "down", "up"])
@pytest.mark.parametrize("clade", ["a", "ab"])
def test_clades_start_at_a_shared_cut_in_every_flat_orientation(kind, orientation, clade):
    from phylustrator.trees import layout as layouts

    tree = loads(NWK)
    layout = getattr(layouts, kind)(tree, orientation=orientation, stem=False)
    canvas = _Recorder()
    highlight_clade(clade, start=0.5)(canvas, tree, layout, Style())
    x0, y0, x1, y1 = canvas.regions[0]
    depth_range = (x0, x1) if layout.grows_along_x else (y0, y1)
    expected = (-3.0, -0.5) if orientation in ("left", "up") else (0.5, 3.0)
    assert depth_range == pytest.approx(expected)
    assert x1 > x0 and y1 > y0


def test_explicit_radial_start_uses_the_time_marker_stem_scale_without_padding():
    from phylustrator.trees.layout import radial

    tree = loads(NWK)
    canvas = _Recorder()
    highlight_clade("a", start=0.8, pad_px=0.2)(canvas, tree, radial(tree), Style())
    r_in, r_out, _, _ = canvas.sectors[0]
    assert r_in == pytest.approx(0.5)  # 0.8 minus the root's 0.3 stem
    assert r_out == pytest.approx(3.2)


def test_clade_box_tracks_the_explicit_start_on_the_page():
    fig = plot(loads(NWK)) + highlight_clade("a", start=0.5, color="#FDBF6F")
    box = fig.clade_box("a", start=0.5)
    drawn = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" '
                      r'fill="#FDBF6F"', fig.as_svg())
    assert drawn
    x, y, width, height = map(float, drawn.groups())
    assert (x, y, x + width, y + height) == pytest.approx((box.x0, box.y0, box.x1, box.y1))


def test_start_stays_exact_even_when_a_short_tip_ends_before_it():
    from phylustrator.trees.layout import rectangular

    tree = loads("((a:1,b:3)ab:1,c:4);")
    canvas = _Recorder()
    highlight_clade("ab", start=3)(canvas, tree, rectangular(tree), Style())
    x0, _, x1, _ = canvas.regions[0]
    assert (x0, x1) == (3, 4)


@pytest.mark.parametrize("start", [-1.0, float("inf"), float("nan"), 4.0])
def test_invalid_start_depth_is_rejected(start):
    with pytest.raises(ValueError, match="start"):
        (plot(loads(NWK)) + highlight_clade("a", start=start)).as_svg()


def test_radial_start_inside_the_hidden_stem_is_rejected():
    with pytest.raises(ValueError, match="stem"):
        (plot(loads(NWK), layout="radial") + highlight_clade("ab", start=0.1)).as_svg()


def test_unrooted_start_is_rejected_because_it_has_no_depth_axis():
    with pytest.raises(ValueError, match="unrooted"):
        (plot(loads(NWK), layout="unrooted") + highlight_clade("ab", start=0.5)).as_svg()
