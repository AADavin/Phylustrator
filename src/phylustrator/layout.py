"""Layouts — pure geometry, no drawing.

A layout turns a :class:`~phylustrator.tree.Tree` into a :class:`Layout`: an ``(x, y)`` for every node
in an abstract coordinate space that the renderer later maps onto the page. Keeping this separate from
rendering is what lets a figure swap ``rectangular`` for ``radial`` without any layer changing.

- ``rectangular`` — the classic phylogram: x is origin-to-tip distance, y is tip order. The default.
- ``radial`` — the same, bent into a circle: radius is distance, angle is tip order.
- ``unrooted`` — Felsenstein's equal-angle: each subtree gets an angular wedge set by its leaf count;
  branches radiate as straight lines, with no imposed root direction.

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

    def x(self, node: Node) -> float:
        return self.coords[node][0]

    def y(self, node: Node) -> float:
        return self.coords[node][1]


def _ranks(tree: Tree) -> dict[Node, int]:
    """Topological depth (edges from the root) — the x-source for a length-less cladogram."""
    rank = {tree.root: 0}
    for node in tree.walk("preorder"):
        for child in node.children:
            rank[child] = rank[node] + 1
    return rank


def _distance_from_crown(tree: Tree, cladogram: bool) -> dict[Node, float]:
    """Each node's distance from the crown (root node at 0): branch-length distance, or edge-rank when
    the tree carries no lengths (or a cladogram is asked for)."""
    depths = {node: tree.depth(node) for node in tree.walk()}
    if cladogram or max(depths.values(), default=0.0) == 0.0:
        return {node: float(r) for node, r in _ranks(tree).items()}
    return depths


def _tip_order_y(tree: Tree) -> dict[Node, float]:
    """y for every node: leaves at 0, 1, 2, … (top to bottom); each internal node at the mean of its
    children."""
    y = {leaf: float(i) for i, leaf in enumerate(tree.leaves)}
    for node in tree.walk("postorder"):
        if not node.is_leaf:
            y[node] = sum(y[c] for c in node.children) / len(node.children)
    return y


def rectangular(tree: Tree, *, stem: bool = True, cladogram: bool = False) -> Layout:
    """Phylogram: ``x`` = distance from the origin, ``y`` = tip order. With ``stem`` (the default) the
    origin is the start of the root branch and the crown sits at ``root.length``; otherwise the origin
    is the crown."""
    offset = float(tree.root.length) if stem else 0.0
    base = _distance_from_crown(tree, cladogram)
    y = _tip_order_y(tree)
    coords = {node: (base[node] + offset, y[node]) for node in tree.walk()}
    x_max = max(p[0] for p in coords.values())
    y_vals = [p[1] for p in coords.values()]
    return Layout("rectangular", coords, (0.0, x_max), (min(y_vals), max(y_vals)), root_branch=offset)


def radial(tree: Tree, *, stem: bool = True, start: float = 0.0, end: float = 360.0,
           cladogram: bool = False) -> Layout:
    """Circular phylogram: radius = distance from the origin (centre), angle = tip order over
    ``[start, end)`` degrees. A full 360° sweep spaces tips by ``i / n`` (so first and last don't
    collide); a partial sweep uses ``i / (n - 1)`` to reach both ends."""
    offset = float(tree.root.length) if stem else 0.0
    base = _distance_from_crown(tree, cladogram)
    leaves = tree.leaves
    n = len(leaves)
    full = abs(end - start) >= 360.0
    denom = n if full else max(n - 1, 1)
    angle = {leaf: math.radians(start + (end - start) * i / denom) for i, leaf in enumerate(leaves)}
    for node in tree.walk("postorder"):
        if not node.is_leaf:
            angle[node] = sum(angle[c] for c in node.children) / len(node.children)
    coords = {node: ((base[node] + offset) * math.cos(angle[node]),
                     (base[node] + offset) * math.sin(angle[node]))
              for node in tree.walk()}
    xs = [p[0] for p in coords.values()]
    ys = [p[1] for p in coords.values()]
    return Layout("radial", coords, (min(xs), max(xs)), (min(ys), max(ys)), root_branch=offset)


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
