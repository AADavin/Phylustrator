"""Clade layers — shade, outline or wrap a subtree.

Shading sits *behind* the branches, so add ``highlight_clade`` **before** the colouring layer:
``plot(tree) + highlight_clade("n5") + color_branches(...)``.

The shape follows the layout, because a clade is a different shape in each: a box in the
rectangular layout, a wedge between the clade's first and last tip angles in the radial one, and a
hull wrapped around the clade's branches in the unrooted one, which has no axis to box against.
"""

from __future__ import annotations

import math


def _subtree(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(n.children)


def clade_node(tree, clade: str):
    """The node named ``clade``. Raises if the tree has none: a name that is not there drew nothing
    at all before, which reads as a clade that is not worth marking rather than as a typo."""
    node = tree.find(clade)
    if node is None:
        raise ValueError(f"no node named {clade!r} in this tree")
    return node


def clade_extent(tree, layout, clade: str, pad: float = 0.4):
    """The clade's extent in *layout* coordinates: ``(x0, y0, x1, y1)`` from the clade's node to its
    furthest tip, ``pad`` tip rows above and below. Rectangular layouts only, where y is tip order.

    :func:`highlight_clade` draws this, and :meth:`~phylustrator.trees.figure.Figure.clade_box` maps
    it to pixels, so the box a zoom line points at is the box on the page."""
    if layout.kind != "rectangular":
        raise ValueError(f"a clade box needs the rectangular layout, where y is tip order; "
                         f"got {layout.kind!r}. highlight_clade itself draws on every layout")
    node = clade_node(tree, clade)
    leaves = [n for n in _subtree(node) if n.is_leaf]
    ys = [layout.y(leaf) for leaf in leaves]
    return (layout.x(node), min(ys) - pad, max(layout.x(leaf) for leaf in leaves), max(ys) + pad)


def _hull(points):
    """The convex hull of ``points``, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def half(seq):
        out: list = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out

    lower, upper = half(pts), half(reversed(pts))
    return lower[:-1] + upper[:-1]


def highlight_clade(clade: str, *, color: str = "#FDBF6F", opacity: float = 0.35, pad: float = 0.4,
                    stroke: str | None = None, stroke_width: float = 0.8, pad_px: float = 4.0):
    """Mark the clade rooted at the node named ``clade``: a box (rectangular), a wedge (radial) or a
    hull around its branches (unrooted). Returns a layer.

    ``color`` fills it and ``stroke`` outlines it. ``color="none"`` with a ``stroke`` leaves an
    outline alone, which is the usual mark for "this clade is drawn enlarged in the next panel";
    :meth:`~phylustrator.trees.figure.Figure.clade_box` gives the pixel corners to run zoom lines to.

    ``pad`` is in tip rows (rectangular) or tip angles (radial), the spacing each layout has.
    ``pad_px`` is the room left in the direction that has no such spacing: outwards from the wedge,
    and all the way around the hull."""

    def layer(canvas, tree, layout, style):
        node = clade_node(tree, clade)
        leaves = [n for n in _subtree(node) if n.is_leaf]
        if not leaves:
            return
        edge = {"stroke": stroke, "stroke_width": stroke_width} if stroke else {}
        if layout.kind == "rectangular":
            x0, y0, x1, y1 = clade_extent(tree, layout, clade, pad)
            canvas.region(x0, y0, x1, y1, fill=color, opacity=opacity, **edge)
            return
        if layout.kind == "radial":
            cx, cy = canvas.px(0.0), canvas.py(0.0)

            def r_px(n):
                return abs(canvas.px(math.hypot(layout.x(n), layout.y(n))) - cx)

            angles = [layout.angle[leaf] for leaf in leaves]
            step = _tip_step(tree, layout)
            canvas.raw_annulus_sector(cx, cy, max(r_px(node) - pad_px, 0.0),
                                      max(r_px(leaf) for leaf in leaves) + pad_px,
                                      min(angles) - pad * step, max(angles) + pad * step,
                                      fill=color, opacity=opacity,
                                      stroke=stroke or "none", stroke_width=stroke_width if stroke else 0.0)
            return
        # unrooted: no axis to box against, so wrap the clade's own branches
        pts = [(canvas.px(layout.x(n)), canvas.py(layout.y(n))) for n in _subtree(node)]
        hull = _hull(pts)
        if len(hull) < 3:
            return
        mx = sum(p[0] for p in hull) / len(hull)
        my = sum(p[1] for p in hull) / len(hull)
        grown = []
        for x, y in hull:                      # push each corner away from the middle, to leave room
            dx, dy = x - mx, y - my
            d = math.hypot(dx, dy) or 1.0
            grown.append((x + dx / d * pad_px, y + dy / d * pad_px))
        canvas.raw_polygon(grown, fill=color, opacity=opacity,
                           stroke=stroke or "none", stroke_width=stroke_width if stroke else 0.0)

    return layer


def _tip_step(tree, layout) -> float:
    """The angle between neighbouring tips, so ``pad`` means the same thing it means in a box."""
    angles = sorted(layout.angle[leaf] for leaf in tree.leaves)
    gaps = [b - a for a, b in zip(angles, angles[1:])]
    return min(gaps) if gaps else 0.1
