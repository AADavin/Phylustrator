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
    #: ``"down"``, ``"left"`` or ``"up"``. The flat layouts, ``rectangular`` and ``diagonal``, turn;
    #: the round ones face right by definition. A layer that places something beside a tip reads
    #: this rather than assuming the tips face right.
    orientation: str = "right"
    #: each node's depth from the origin, in the tree's own units, whatever direction it is drawn
    #: in. A turned layout has no one axis that carries time, so a layer that needs a distance
    #: along the tree (an event part-way down a branch, a tick on the time axis) asks for it here.
    depths: dict | None = None
    #: the length every branch was capped at, or ``None`` when the tree is drawn to scale.
    cut: float | None = None
    #: the nodes whose own branch is longer than :attr:`cut`, so is drawn shortened. A figure laid
    #: out like this has to say so on the branch, or it misstates its own data.
    cut_at: frozenset = frozenset()

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


def _cut_depths(tree: Tree, cut: float) -> dict[Node, float]:
    """Each node's distance from the crown with every branch capped at ``cut``.

    Capped branch by branch and accumulated, not capped at the end: one long branch deep in the
    tree holds up everything beyond it, and clipping the totals instead would pile those clades on
    top of each other at the cut."""
    depth = {tree.root: 0.0}
    for node in tree.walk():                                   # preorder: a parent before its child
        if node.parent is not None:
            depth[node] = depth[node.parent] + min(float(node.length or 0.0), cut)
    return depth


def cut_branches(tree: Tree, cut: float | None) -> frozenset:
    """The nodes whose own branch is longer than ``cut``, so is drawn shortened."""
    if cut is None:
        return frozenset()
    return frozenset(n for n in tree.walk()
                     if n.parent is not None and float(n.length or 0.0) > cut)


def along_branch(layout: "Layout", node: Node, at: float) -> tuple[float, float]:
    """Where a fraction ``at`` of the way along ``node``'s branch falls, in layout coordinates.

    The fraction runs from the parent (0) to the node (1), along the branch **as it is drawn**: the
    run of a rectangular branch, the radial step of a circular one, the slanted segment of a
    diagonal or unrooted one. A turned rectangular tree carries its depth down the page, so its run
    does too."""
    x, y = layout.x(node), layout.y(node)
    if node.parent is None:
        return x, y
    if layout.kind == "rectangular":
        if layout.grows_along_x:
            return layout.x(node.parent) + at * (x - layout.x(node.parent)), y
        return x, layout.y(node.parent) + at * (y - layout.y(node.parent))
    if layout.kind == "radial" and layout.angle is not None:
        a = layout.angle[node]
        r_parent = math.hypot(layout.x(node.parent), layout.y(node.parent))
        r = r_parent + at * (math.hypot(x, y) - r_parent)
        return r * math.cos(a), r * math.sin(a)
    return (layout.x(node.parent) + at * (x - layout.x(node.parent)),
            layout.y(node.parent) + at * (y - layout.y(node.parent)))


def _distance_from_crown(tree: Tree, cladogram: bool, align_tips: bool = False,
                         cut: float | None = None) -> dict[Node, float]:
    """Each node's distance from the crown (root node at 0): branch-length distance, or edge-rank when
    the tree carries no lengths (or a cladogram is asked for).

    ``cut`` caps every branch at that length, so one absurd branch does not take the whole page.

    ``align_tips`` then pushes every leaf out to the furthest one, so the tips end on a single row
    and the internal nodes keep their own depth. That is how a teaching diagram is drawn — the
    picture is about the topology, and a tip left short reads as a shallower lineage rather than as
    a shorter branch. It says nothing about the lengths, so it is a drawing choice and not a
    transformation of the tree."""
    depths = (_cut_depths(tree, cut) if cut is not None
              else {node: tree.depth(node) for node in tree.walk()})
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


#: The four ways a rooted tree may face. The name says where the tips are, as a reader describes
#: a figure: a ``"down"`` tree has its root at the top and its tips along the bottom.
ORIENTATIONS = ("right", "down", "left", "up")


def _turned(kind: str, tree: Tree, *, stem: bool, cladogram: bool, orientation: str,
            align_tips: bool, cut: float | None = None) -> Layout:
    """The coordinates of a rooted tree facing any of the four ways: depth along one axis of the
    page, tip order along the other.

    ``rectangular`` and ``diagonal`` share this. They are the same tree in the same places and
    differ only in how a branch is drawn between them — a right-angle pair or one slanted segment —
    so having two copies of the turning would be two chances to turn it differently."""
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation must be one of {', '.join(ORIENTATIONS)}, not {orientation!r}")
    offset = float(tree.root.length) if stem else 0.0
    depth = {node: d + offset
             for node, d in _distance_from_crown(tree, cladogram, align_tips, cut).items()}
    order = _tip_order_y(tree)
    # the depth axis points away from the root; the order axis is the page's other one. Flipping
    # depth (left/up) rather than reversing the tip order keeps the tips in the order they were
    # read, so a figure turned round is the same tree, not its mirror image.
    flip = -1.0 if orientation in ("left", "up") else 1.0
    along_x = orientation in ("right", "left")
    coords = {node: ((flip * depth[node], order[node]) if along_x
                     else (order[node], flip * depth[node]))
              for node in tree.walk()}
    # the stem is drawn back from the root to depth 0, so the extent has to reach it or the stem
    # runs off the page
    xs = [p[0] for p in coords.values()] + ([0.0] if along_x else [])
    ys = [p[1] for p in coords.values()] + ([] if along_x else [0.0])
    return Layout(kind, coords, (min(xs), max(xs)), (min(ys), max(ys)),
                  root_branch=offset, orientation=orientation, depths=depth,
                  cut=cut, cut_at=cut_branches(tree, cut))


def rectangular(tree: Tree, *, stem: bool = True, cladogram: bool = False,
                orientation: str = "right", align_tips: bool = False,
                cut: float | None = None) -> Layout:
    """Phylogram: distance from the origin along one axis, tip order along the other, with each
    branch drawn as a connector and a run meeting at a right angle. With ``stem`` (the default) the
    origin is the start of the root branch and the crown sits at ``root.length``; otherwise the
    origin is the crown. ``align_tips`` ends every lineage on the furthest tip's row.

    ``orientation`` says where the tips go: ``"right"`` (the default, root on the left), ``"down"``
    (root at the top, tips along the bottom — how a tree goes into a multi-panel figure beside
    another), ``"left"`` or ``"up"``. Text stays upright in all four, which is why this is a layout
    and not a rotation of the finished drawing."""
    return _turned("rectangular", tree, stem=stem, cladogram=cladogram, orientation=orientation,
                   align_tips=align_tips, cut=cut)


def radial(tree: Tree, *, stem: bool = False, start: float = 0.0, end: float = 350.0,
           cladogram: bool = False, align_tips: bool = False, cut: float | None = None) -> Layout:
    """Circular phylogram: **radius** = distance from the crown at the centre, **angle** = tip order
    over ``[start, end)`` degrees. Leaving a small gap (the default ``end=350``) keeps the first and
    last tips from colliding at the seam.

    The root sits at the centre — a stem would become a spurious little circle there — so ``stem`` is
    ignored (kept for a uniform layout interface). ``align_tips`` puts every tip on one circle."""
    base = _distance_from_crown(tree, cladogram, align_tips, cut)
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
                  root_branch=0.0, angle=angle, cut=cut, cut_at=cut_branches(tree, cut))


def diagonal(tree: Tree, *, stem: bool = True, cladogram: bool = False,
             orientation: str = "right", align_tips: bool = False,
             cut: float | None = None) -> Layout:
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
    return _turned("diagonal", tree, stem=stem, cladogram=cladogram, orientation=orientation,
                   align_tips=align_tips, cut=cut)


def _leaf_counts(tree: Tree) -> dict[Node, int]:
    counts: dict[Node, int] = {}
    for node in tree.walk("postorder"):
        counts[node] = 1 if node.is_leaf else sum(counts[c] for c in node.children)
    return counts


#: How many rounds of equal-daylight are run when it is simply asked for. Each round sweeps every
#: internal node; past about this many the picture stops changing in any way a reader would see.
_DAYLIGHT_PASSES = 5

#: A round that moves every subtree less than this, in radians, has converged.
_DAYLIGHT_SETTLED = math.radians(0.5)


def _neighbours(tree: Tree) -> dict:
    """Each node's neighbours with the root's direction forgotten — an unrooted tree has no up."""
    near: dict = {node: [] for node in tree.walk()}
    for node in tree.walk():
        for child in node.children:
            near[node].append(child)
            near[child].append(node)
    return near


def _beyond(near: dict, node: Node, through: Node) -> list:
    """Every node reachable from ``through`` without going back past ``node`` — the subtree that
    hangs off that one edge, which is what a rotation about ``node`` moves."""
    seen = {node, through}
    stack = [through]
    out = [through]
    while stack:
        here = stack.pop()
        for nxt in near[here]:
            if nxt not in seen:
                seen.add(nxt)
                out.append(nxt)
                stack.append(nxt)
    return out


def _arc(angles: list[float]) -> tuple[float, float]:
    """The smallest arc holding every angle, as ``(start, width)`` going anticlockwise.

    Found as the complement of the widest empty gap, since a set of angles has no least and no
    greatest — a subtree straddling the far side of zero would otherwise measure as nearly the
    whole circle."""
    if len(angles) == 1:
        return angles[0], 0.0
    ordered = sorted(angles)
    widest, after = 0.0, 0
    for i, here in enumerate(ordered):
        nxt = ordered[(i + 1) % len(ordered)]
        gap = (nxt - here) % (2 * math.pi)
        if gap > widest:
            widest, after = gap, (i + 1) % len(ordered)
    return ordered[after], 2 * math.pi - widest


def _equal_daylight(tree: Tree, coords: dict, passes: int) -> None:
    """Spread the tree over the whole circle, in place — Felsenstein's equal-daylight refinement.

    The equal-angle layout gives each subtree a wedge in proportion to its leaves, measured at the
    root; further out, that wedge is no longer where the subtree actually sits, so a long backbone
    bends into a half circle and one side of the picture stays empty. This looks at each internal
    node in turn, measures the arc each of its subtrees really covers as seen from *that* node, and
    turns them until the daylight between them is shared equally.

    The first subtree of each node is left where it is, so the turning spreads the tree rather than
    spinning it. Every node is swept each pass, and the passes stop early once nothing moves."""
    near = _neighbours(tree)
    nodes = [n for n in tree.walk() if len(near[n]) >= 3]
    # which nodes hang off each edge never changes — only where they are does — so the walk that
    # finds them is done once rather than once per node per pass
    beyond = {(node, side): _beyond(near, node, side) for node in nodes for side in near[node]}
    for _ in range(max(0, passes)):
        moved = 0.0
        for node in nodes:
            vx, vy = coords[node]
            groups = []
            for side in near[node]:
                points = beyond[(node, side)]
                angles = [math.atan2(coords[p][1] - vy, coords[p][0] - vx) for p in points]
                start, width = _arc(angles)
                groups.append((start, width, points))
            if len(groups) < 3:
                continue
            daylight = 2 * math.pi - sum(w for _, w, _ in groups)
            if daylight <= 0.0:                     # already crowded; turning cannot help
                continue
            share = daylight / len(groups)
            groups.sort(key=lambda g: g[0])
            cursor = groups[0][0]
            for start, width, points in groups:
                turn = (cursor - start + math.pi) % (2 * math.pi) - math.pi
                if abs(turn) > 1e-12:
                    moved = max(moved, abs(turn))
                    cos, sin = math.cos(turn), math.sin(turn)
                    for point in points:
                        dx, dy = coords[point][0] - vx, coords[point][1] - vy
                        coords[point] = (vx + dx * cos - dy * sin, vy + dx * sin + dy * cos)
                cursor += width + share
        if moved < _DAYLIGHT_SETTLED:
            break


def unrooted(tree: Tree, *, stem: bool = False, cladogram: bool = False,
             cut: float | None = None, daylight: bool | int = False) -> Layout:
    """Equal-angle layout: place the root at the origin and give each subtree an angular wedge
    proportional to its leaf count, stepping out along each branch. Rootless by nature, so ``stem`` is
    ignored (kept in the signature for a uniform layout interface).

    ``daylight=True`` then runs Felsenstein's **equal-daylight** refinement over it, which spreads
    the tree over the whole circle. Equal-angle measures every wedge at the root, and further out
    that wedge is no longer where the subtree sits, so a tree with a long backbone bends into a
    half circle and leaves one side of the picture empty. Equal-daylight looks at each internal
    node in turn and turns its subtrees until the gaps between them are equal. Pass a number for
    that many rounds instead of the usual five; they stop early once nothing moves.

    It costs a sweep of every subtree of every node per round: measured at 0.1 s for 200 tips,
    0.4 s for 400 and 2.5 s for 1000, which is why it is asked for rather than always done."""
    counts = _leaf_counts(tree)
    coords: dict[Node, tuple[float, float]] = {}

    def place(node: Node, x: float, y: float, a0: float, a1: float) -> None:
        coords[node] = (x, y)
        a = a0
        for child in node.children:
            span = (a1 - a0) * counts[child] / counts[node]
            mid = a + span / 2
            length = 1.0 if cladogram else (child.length or 1.0)
            if cut is not None:
                length = min(length, cut)
            place(child, x + length * math.cos(mid), y + length * math.sin(mid), a, a + span)
            a += span

    place(tree.root, 0.0, 0.0, 0.0, 2 * math.pi)
    if daylight:
        _equal_daylight(tree, coords,
                        _DAYLIGHT_PASSES if daylight is True else int(daylight))
    xs = [p[0] for p in coords.values()]
    ys = [p[1] for p in coords.values()]
    return Layout("unrooted", coords, (min(xs), max(xs)), (min(ys), max(ys)), root_branch=0.0,
                  cut=cut, cut_at=cut_branches(tree, cut))
