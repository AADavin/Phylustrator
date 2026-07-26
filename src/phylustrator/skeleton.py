"""Branch drawing — the one place that knows how each layout renders its branches.

Both the base skeleton and the ``color_branches`` layer draw through :func:`draw_branches`, so a new
layout is taught to draw once, here, and every branch-drawing layer follows for free. A branch whose
node is in ``dashed`` is drawn dashed (used for extinct lineages).
"""

from __future__ import annotations

import math


def draw_branches(canvas, tree, layout, *, color, width, gradient: bool = False, dashed=None) -> None:
    """Draw the tree's branches. ``color(node) -> hex``. When ``gradient`` is set, each branch runs
    from its parent's colour to its own. Any node whose name is in ``dashed`` has its branch (and its
    connector) drawn dashed and solid-coloured."""
    dashed = dashed or set()
    dispatch = {"rectangular": _rectangular, "radial": _radial, "unrooted": _unrooted}
    draw = dispatch.get(layout.kind)
    if draw is None:
        raise ValueError(f"no branch drawer for layout {layout.kind!r}")
    draw(canvas, tree, layout, color, width, gradient, dashed)


def _branch(canvas, x1, y1, x2, y2, c_from, c_to, width, gradient, dash=False) -> None:
    if dash:
        canvas.line(x1, y1, x2, y2, c_to, width, dash=True)
    elif gradient and c_from != c_to:
        canvas.gradient_line(x1, y1, x2, y2, c_from, c_to, width)
    else:
        canvas.line(x1, y1, x2, y2, c_to, width)


def _rectangular(canvas, tree, layout, color, width, gradient, dashed) -> None:
    for node in tree.walk():
        x, y, cn = layout.x(node), layout.y(node), color(node)
        d = node.name in dashed
        if node.is_root:
            if layout.root_branch > 0:
                canvas.line(x - layout.root_branch, y, x, y, cn, width, dash=d)     # stem
        else:
            _branch(canvas, layout.x(node.parent), y, x, y, color(node.parent), cn, width, gradient, dash=d)
        if not node.is_leaf:
            child_ys = [layout.y(c) for c in node.children]
            canvas.line(x, min(child_ys), x, max(child_ys), cn, width, dash=d)       # connector


def _radial(canvas, tree, layout, color, width, gradient, dashed) -> None:
    # Use the layout's monotonic angles (0→2π), NOT atan2 (which wraps at ±π and would make a node
    # straddling the 9-o'clock direction draw a huge arc the long way round).
    ang = layout.angle

    def radius(node):
        return math.hypot(layout.x(node), layout.y(node))

    for node in tree.walk():
        x, y, cn = layout.x(node), layout.y(node), color(node)
        r, d = radius(node), node.name in dashed
        if node.is_root:
            if layout.root_branch > 0:
                canvas.line(0.0, 0.0, x, y, cn, width, dash=d)                        # stem from centre
        else:
            a = ang[node]
            r_parent = radius(node.parent)
            sx, sy = r_parent * math.cos(a), r_parent * math.sin(a)                   # step out radially
            _branch(canvas, sx, sy, x, y, color(node.parent), cn, width, gradient, dash=d)
        if not node.is_leaf and r > 1e-9:                                             # (skip root at centre)
            child_angles = [ang[c] for c in node.children]
            _arc(canvas, r, min(child_angles), max(child_angles), cn, width, dash=d)  # angular connector


def _arc(canvas, r, a0, a1, color, width, steps: int = 24, dash: bool = False) -> None:
    prev = (r * math.cos(a0), r * math.sin(a0))
    for i in range(1, steps + 1):
        a = a0 + (a1 - a0) * i / steps
        cur = (r * math.cos(a), r * math.sin(a))
        canvas.line(prev[0], prev[1], cur[0], cur[1], color, width, dash=dash)
        prev = cur


def _unrooted(canvas, tree, layout, color, width, gradient, dashed) -> None:
    for node in tree.walk():
        if node.is_root:
            continue
        _branch(canvas, layout.x(node.parent), layout.y(node.parent),
                layout.x(node), layout.y(node), color(node.parent), color(node), width, gradient,
                dash=node.name in dashed)
