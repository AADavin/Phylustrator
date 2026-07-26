"""Layout geometry: rectangular and radial coordinate assignment."""

import math

from phylustrator import loads
from phylustrator.layout import radial, rectangular, unrooted


def test_rectangular_x_is_distance_root_at_zero():
    tree = loads("((A:2,B:2)C:1,D:3)R;")
    lay = rectangular(tree)
    assert lay.x(tree.root) == 0.0          # root at the left
    assert lay.x(tree.find("A")) == 3.0     # C(1)+A(2)
    assert lay.x(tree.find("D")) == 3.0     # tips of an ultrametric tree align


def test_rectangular_y_is_tip_order_internals_centered():
    tree = loads("((A,B)C,D)R;")
    lay = rectangular(tree)
    assert (lay.y(tree.find("A")), lay.y(tree.find("B")), lay.y(tree.find("D"))) == (0.0, 1.0, 2.0)
    assert lay.y(tree.find("C")) == 0.5     # mean of A(0) and B(1)
    assert lay.y(tree.root) == 1.25         # mean of C(0.5) and D(2)


def test_rectangular_cladogram_falls_back_to_rank():
    tree = loads("((A,B)C,D)R;")            # no branch lengths
    lay = rectangular(tree)
    assert lay.x(tree.root) == 0.0
    assert lay.x(tree.find("A")) == 2.0     # two edges from the root
    assert lay.x(tree.find("D")) == 1.0


def test_stem_shown_by_default():
    tree = loads("((A:2,B:2)C:1,D:3)R:5;")   # R carries a stem of 5
    lay = rectangular(tree)                    # stem=True by default
    assert lay.root_branch == 5.0
    assert lay.x(tree.root) == 5.0             # crown pushed out by the stem
    assert lay.x(tree.find("A")) == 8.0        # 5 (stem) + 1 (C) + 2 (A)
    assert lay.xlim[0] == 0.0                  # ...but the origin (stem start) is in frame


def test_stem_can_be_hidden():
    tree = loads("((A:2,B:2)C:1,D:3)R:5;")
    lay = rectangular(tree, stem=False)
    assert lay.root_branch == 0.0
    assert lay.x(tree.root) == 0.0             # tree starts at the crown
    assert lay.x(tree.find("A")) == 3.0


def test_radial_radius_is_distance():
    tree = loads("((A:2,B:2)C:1,D:3)R;")
    lay = radial(tree)
    for name in ("A", "B", "D"):
        node = tree.find(name)
        r = math.hypot(*lay.coords[node])
        assert math.isclose(r, 3.0, abs_tol=1e-9)   # all tips at distance 3
    assert lay.coords[tree.root] == (0.0, 0.0)       # root at the centre


def test_radial_centres_root_ignoring_stem():
    tree = loads("((A:2,B:2)C:1,D:3)R:5;")   # a big stem must not push the root off-centre
    lay = radial(tree)
    assert lay.coords[tree.root] == (0.0, 0.0)
    assert lay.root_branch == 0.0


def test_unrooted_root_at_origin_and_covers_all_nodes():
    tree = loads("((A:1,B:1)C:1,(D:1,E:1)F:1)R;")
    lay = unrooted(tree)
    assert lay.coords[tree.root] == (0.0, 0.0)
    assert set(lay.coords) == set(tree.walk())        # every node placed
