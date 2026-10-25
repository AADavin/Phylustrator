"""Layouts — pure geometry, no drawing.

A layout turns a :class:`~phylustrator.tree.Tree` into a :class:`Layout`: an ``(x, y)`` for every node
in an abstract coordinate space that the renderer later maps onto the page. Keeping this separate from
rendering is what lets a figure swap ``rectangular`` for ``radial`` without any layer changing.

- ``rectangular`` — the classic phylogram: x is origin-to-tip distance, y is tip order. The default.
- ``radial`` — the same, bent into a circle: radius is distance, angle is tip order.
- ``unrooted`` — Felsenstein's equal-angle: each subtree gets an angular wedge set by its leaf count;
  branches radiate as straight lines, with no imposed root direction.
- ``diagonal`` — the rooted tree of a textbook diagram: the same depth and tip-order coordinates as
  ``rectangular``, but every parent is joined to its child by one straight slanted segment instead of
  a right-angle pair, and it is the one layout that turns: ``orientation`` puts the root at the left,
  top, right or bottom.

**Stem-aware.** ZOMBI2 trees carry a *stem* — the branch before the first split (``root.length``). By
default the layout **includes** it: the origin sits at distance 0 and the crown at ``root.length``, so
the stem is drawn to scale like any other branch. ``stem=False`` starts the tree at the crown instead.
The stem length actually laid out is reported as :attr:`Layout.root_branch` for the renderer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .tree import Node, Tree


@dataclass
class Layout:
    """Node coordinates plus the overall extent, ready for the renderer."""

    kind: str
    coords: dict[Node, tuple[float, float]]
    xlim: tuple[float, float]
    ylim: tuple[float, float]
    root_branch: float = 0.0  # length of the root's stem as laid out (0 when stem is hidden/absent)
    angle: dict | None = None  # radial only: each node's angle in radians, monotonic (no atan2 wrap)
    #: which way the tree grows from its root — ``"right"`` (the default everywhere else),
    #: ``"down"``, ``"left"`` or ``"up"``. Only ``diagonal`` turns; a layer that places something
    #: beside a tip reads this rather than assuming the tips face right.
    orientation: str = "right"
    #: each node's depth from the origin, in the tree's own units, whatever direction it is drawn
    #: in. A turned layout has no one axis that carries time, so a layer that needs a distance
    #: along the tree (an event part-way down a branch, a tick on the time axis) asks for it here.
    depths: dict | None = None

    def x(self, node: Node) -> float:
        return self.coords[node][0]

    def y(self, node: Node) -> float:
        return self.coords[node][1]

    def depth(self, node: Node) -> float:
        """How far ``node`` sits from the origin along the tree, in the tree's own units."""
        if self.depths is not None:
            return float(self.depths[node])
        if self.kind in ("radial", "unrooted"):
            return math.hypot(*self.coords[node])
        return self.coords[node][0]

    @property
    def grows_along_x(self) -> bool:
        """Whether depth runs along the page's x axis (``"right"``/``"left"``) or its y axis."""
        return self.orientation in ("right", "left")


def _ranks(tree: Tree) -> dict[Node, int]:
    """Topological depth (edges from the root) — the x-source for a length-less cladogram."""
    rank = {tree.root: 0}
    for node in tree.walk("preorder"):
        for child in node.children:
            rank[child] = rank[node] + 1
    return rank


def _distance_from_crown(tree: Tree, cladogram: bool, align_tips: bool = False) -> dict[Node, float]:
    """Each node's distance from the crown (root node at 0): branch-length distance, or edge-rank when
    the tree carries no lengths (or a cladogram is asked for).

    ``align_tips`` then pushes every leaf out to the furthest one, so the tips end on a single row
    and the internal nodes keep their own depth. That is how a teaching diagram is drawn — the
    picture is about the topology, and a tip left short reads as a shallower lineage rather than as
    a shorter branch. It says nothing about the lengths, so it is a drawing choice and not a
    transformation of the tree."""
    depths = {node: tree.depth(node) for node in tree.walk()}
    if cladogram or max(depths.values(), default=0.0) == 0.0:
        depths = {node: float(r) for node, r in _ranks(tree).items()}
    if align_tips:
        furthest = max((depths[leaf] for leaf in tree.leaves), default=0.0)
        depths = {node: (furthest if node.is_leaf else d) for node, d in depths.items()}
    return depths


def _tip_order_y(tree: Tree) -> dict[Node, float]:
    """y for every node: leaves at 0, 1, 2, … (top to bottom); each internal node at the mean of its
    children."""
    y = {leaf: float(i) for i, leaf in enumerate(tree.leaves)}
    for node in tree.walk("postorder"):
        if not node.is_leaf:
            y[node] = sum(y[c] for c in node.children) / len(node.children)
    return y


def rectangular(tree: Tree, *, stem: bool = True, cladogram: bool = False,
                align_tips: bool = False) -> Layout:
    """Phylogram: ``x`` = distance from the origin, ``y`` = tip order. With ``stem`` (the default) the
    origin is the start of the root branch and the crown sits at ``root.length``; otherwise the origin
    is the crown. ``align_tips`` ends every lineage on the furthest tip's row."""
    offset = float(tree.root.length) if stem else 0.0
    base = _distance_from_crown(tree, cladogram, align_tips)
    y = _tip_order_y(tree)
    coords = {node: (base[node] + offset, y[node]) for node in tree.walk()}
    x_max = max(p[0] for p in coords.values())
    y_vals = [p[1] for p in coords.values()]
    return Layout("rectangular", coords, (0.0, x_max), (min(y_vals), max(y_vals)), root_branch=offset)


def radial(tree: Tree, *, stem: bool = False, start: float = 0.0, end: float = 350.0,
           cladogram: bool = False, align_tips: bool = False) -> Layout:
    """Circular phylogram: **radius** = distance from the crown at the centre, **angle** = tip order
    over ``[start, end)`` degrees. Leaving a small gap (the default ``end=350``) keeps the first and
    last tips from colliding at the seam.

    The root sits at the centre — a stem would become a spurious little circle there — so ``stem`` is
    ignored (kept for a uniform layout interface). ``align_tips`` puts every tip on one circle."""
    base = _distance_from_crown(tree, cladogram, align_tips)
    leaves = tree.leaves
    n = len(leaves)
    denom = max(n - 1, 1)
    angle = {leaf: math.radians(start + (end - start) * i / denom) for i, leaf in enumerate(leaves)}
    for node in tree.walk("postorder"):
        if not node.is_leaf:
            angle[node] = sum(angle[c] for c in node.children) / len(node.children)
    coords = {node: (base[node] * math.cos(angle[node]), base[node] * math.sin(angle[node]))
              for node in tree.walk()}
    xs = [p[0] for p in coords.values()]
    ys = [p[1] for p in coords.values()]
    return Layout("radial", coords, (min(xs), max(xs)), (min(ys), max(ys)),
                  root_branch=0.0, angle=angle)


#: The four ways a rooted tree may face. The name says where the tips are, as a reader describes
#: a figure: a ``"down"`` tree has its root at the top and its tips along the bottom.
ORIENTATIONS = ("right", "down", "left", "up")


def diagonal(tree: Tree, *, stem: bool = True, cladogram: bool = False,
             orientation: str = "right", align_tips: bool = False) -> Layout:
    """Rooted tree whose branches are straight slanted segments from parent to child — the shape of a
    textbook or TikZ diagram, rather than the right-angle connectors of ``rectangular``.

    The coordinates are the rectangular ones: depth from the origin, and tip order across. What
    differs is the drawing, so a diagonal **phylogram** still carries its lengths — the depth
    projection of a segment is its length, which is what a reader measures off the axis, while the
    slanted segment itself is longer. ``cladogram=True`` spaces by topological depth instead, and
    ``align_tips=True`` ends every lineage on the row of the furthest tip, which is how a teaching
    diagram lines its taxa up.

    ``orientation`` says where the tips go: ``"right"`` (the default, root on the left), ``"down"``
    (root at the top, the usual teaching diagram), ``"left"`` or ``"up"``. Text stays upright in all
    four, which is why this is a layout and not a rotation of the finished drawing."""
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation must be one of {', '.join(ORIENTATIONS)}, not {orientation!r}")
    offset = float(tree.root.length) if stem else 0.0
    depth = {node: d + offset
             for node, d in _distance_from_crown(tree, cladogram, align_tips).items()}
    order = _tip_order_y(tree)
    # the depth axis points away from the root; the order axis is the page's other one. Flipping
    # depth (left/up) rather than reversing the tip order keeps the tips in the order they were
    # read, so a figure turned round is the same tree, not its mirror image.
    flip = -1.0 if orientation in ("left", "up") else 1.0
    coords = {node: ((flip * depth[node], order[node]) if orientation in ("right", "left")
                     else (order[node], flip * depth[node]))
              for node in tree.walk()}
    # the stem is drawn back from the root to depth 0, so the extent has to reach it or the stem
    # runs off the page (rectangular includes it by starting its xlim at 0 for the same reason)
    xs = [p[0] for p in coords.values()] + ([0.0] if orientation in ("right", "left") else [])
    ys = [p[1] for p in coords.values()] + ([] if orientation in ("right", "left") else [0.0])
    return Layout("diagonal", coords, (min(xs), max(xs)), (min(ys), max(ys)),
                  root_branch=offset, orientation=orientation, depths=depth)


def _leaf_counts(tree: Tree) -> dict[Node, int]:
    counts: dict[Node, int] = {}
    for node in tree.walk("postorder"):
        counts[node] = 1 if node.is_leaf else sum(counts[c] for c in node.children)
    return counts


def unrooted(tree: Tree, *, stem: bool = False, cladogram: bool = False) -> Layout:
    """Equal-angle layout: place the root at the origin and give each subtree an angular wedge
    proportional to its leaf count, stepping out along each branch. Rootless by nature, so ``stem`` is
    ignored (kept in the signature for a uniform layout interface)."""
    counts = _leaf_counts(tree)
    coords: dict[Node, tuple[float, float]] = {}

    def place(node: Node, x: float, y: float, a0: float, a1: float) -> None:
        coords[node] = (x, y)
        a = a0
        for child in node.children:
            span = (a1 - a0) * counts[child] / counts[node]
            mid = a + span / 2
            length = 1.0 if cladogram else (child.length or 1.0)
            place(child, x + length * math.cos(mid), y + length * math.sin(mid), a, a + span)
            a += span

    place(tree.root, 0.0, 0.0, 0.0, 2 * math.pi)
    xs = [p[0] for p in coords.values()]
    ys = [p[1] for p in coords.values()]
    return Layout("unrooted", coords, (min(xs), max(xs)), (min(ys), max(ys)), root_branch=0.0)
