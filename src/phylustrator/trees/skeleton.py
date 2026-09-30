"""Branch drawing — the one place that knows how each layout renders its branches.

Both the base skeleton and the ``color_branches`` layer draw through :func:`draw_branches`, so a new
layout is taught to draw once, here, and every branch-drawing layer follows for free. A branch whose
node is in ``dashed`` is drawn dashed (used for extinct lineages).
"""

from __future__ import annotations

import math


def draw_branches(canvas, tree, layout, *, color, width, gradient: bool = False, dashed=None,
                  include=None) -> None:
    """Draw the tree's branches. ``color(node) -> hex``. When ``gradient`` is set, each branch runs
    from its parent's colour to its own. Any node whose name is in ``dashed`` has its branch (and its
    connector) drawn dashed and solid-coloured.

    ``width`` is a number or ``width(node) -> number``, so one lineage can be drawn thicker than the
    rest. ``include(node) -> bool`` keeps a branch out of this pass, leaving it as the base skeleton
    drew it — without it a layer that paints a few branches repaints all the others as well."""
    dashed = dashed or set()
    w = width if callable(width) else (lambda node: width)
    keep = include or (lambda node: True)
    dispatch = {"rectangular": _rectangular, "radial": _radial, "unrooted": _unrooted}
    draw = dispatch.get(layout.kind)
    if draw is None:
        raise ValueError(f"no branch drawer for layout {layout.kind!r}")
    draw(canvas, tree, layout, color, w, gradient, dashed, keep)


def _drop(color, node, child, node_color, gradient):
    """The colour of the connector from ``node`` down into ``child``.

    That segment is where the child's branch begins, so it is the child's — a map covering every
    branch but not the root left the root's bar unpainted, and the two clades floated apart. Under a
    gradient the child's branch *starts* in this node's colour, so there the node's colour is the
    continuous one."""
    return node_color if gradient else color(child)


def _branch(canvas, x1, y1, x2, y2, c_from, c_to, width, gradient, dash=False) -> None:
    if dash:
        canvas.line(x1, y1, x2, y2, c_to, width, dash=True)
    elif gradient and c_from != c_to:
        canvas.gradient_line(x1, y1, x2, y2, c_from, c_to, width)
    else:
        canvas.line(x1, y1, x2, y2, c_to, width)


def _rectangular(canvas, tree, layout, color, width, gradient, dashed, keep) -> None:
    for node in tree.walk():
        x, y, cn = layout.x(node), layout.y(node), color(node)
        d = node.name in dashed
        if node.is_root:
            if layout.root_branch > 0 and keep(node):
                canvas.line(x - layout.root_branch, y, x, y, cn, width(node), dash=d)     # stem
        elif keep(node):
            _branch(canvas, layout.x(node.parent), y, x, y, color(node.parent), cn, width(node),
                    gradient, dash=d)
        if not node.is_leaf:
            # Split the vertical connector per child: the segment descending into an extinct
            # (dashed) clade is dashed too, instead of one solid bar drawn straight across an
            # extinction. Each segment runs from this node's y to the child's y (they meet at y).
            for c in node.children:
                if keep(c):                # the drop is the child's, so it follows the child's width
                    canvas.line(x, y, x, layout.y(c), _drop(color, node, c, cn, gradient), width(c),
                                dash=(c.name in dashed))                               # connector


def _radial(canvas, tree, layout, color, width, gradient, dashed, keep) -> None:
    # Use the layout's monotonic angles (0→2π), NOT atan2 (which wraps at ±π and would make a node
    # straddling the 9-o'clock direction draw a huge arc the long way round).
    ang = layout.angle

    def radius(node):
        return math.hypot(layout.x(node), layout.y(node))

    for node in tree.walk():
        x, y, cn = layout.x(node), layout.y(node), color(node)
        r, d = radius(node), node.name in dashed
        if node.is_root:
            if layout.root_branch > 0 and keep(node):
                canvas.line(0.0, 0.0, x, y, cn, width(node), dash=d)                  # stem from centre
        elif keep(node):
            a = ang[node]
            r_parent = radius(node.parent)
            sx, sy = r_parent * math.cos(a), r_parent * math.sin(a)                   # step out radially
            _branch(canvas, sx, sy, x, y, color(node.parent), cn, width(node), gradient, dash=d)
        if not node.is_leaf and r > 1e-9:                                             # (skip root at centre)
            kids = [c for c in node.children if keep(c)]
            drops = [(_drop(color, node, c, cn, gradient), width(c)) for c in kids]
            if kids and len(kids) == len(node.children) and set(drops) == {(cn, width(node))}:
                # one colour and one width: one arc, exactly as it has always been drawn
                _arc(canvas, r, min(ang[c] for c in kids), max(ang[c] for c in kids), cn,
                     width(node), dash=d)
            else:                       # each child's stretch of the ring, in the child's own style
                for c, (drop, wd) in zip(kids, drops):
                    _arc(canvas, r, ang[node], ang[c], drop, wd, dash=d)


def _arc(canvas, r, a0, a1, color, width, steps: int = 24, dash: bool = False) -> None:
    prev = (r * math.cos(a0), r * math.sin(a0))
    for i in range(1, steps + 1):
        a = a0 + (a1 - a0) * i / steps
        cur = (r * math.cos(a), r * math.sin(a))
        canvas.line(prev[0], prev[1], cur[0], cur[1], color, width, dash=dash)
        prev = cur


def _unrooted(canvas, tree, layout, color, width, gradient, dashed, keep) -> None:
    for node in tree.walk():
        if node.is_root or not keep(node):
            continue
        _branch(canvas, layout.x(node.parent), layout.y(node.parent),
                layout.x(node), layout.y(node), color(node.parent), color(node), width(node),
                gradient, dash=node.name in dashed)
