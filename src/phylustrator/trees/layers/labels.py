"""Text layers — names beside tips and internal nodes."""

from __future__ import annotations

import math


def tip_labels(*, size=None, color=None, offset: float = 6.0):
    """Write each leaf's name just past its tip. On a rectangular tree the names sit to the right; on a
    radial or unrooted tree they are rotated to run along the branch (flipped on the left side so they
    stay upright). Returns a layer."""

    def layer(canvas, tree, layout, style):
        for leaf in tree.leaves:
            if not leaf.name:
                continue
            if layout.kind == "rectangular":
                canvas.text(layout.x(leaf), layout.y(leaf), leaf.name,
                            dx=offset, anchor="start", size=size, color=color)
                continue
            # radial/unrooted: point outward — from the centre (radial) or the parent (unrooted).
            lx, ly = canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf))
            if layout.kind == "radial":
                ax, ay = canvas.px(0.0), canvas.py(0.0)
            else:
                ax, ay = canvas.px(layout.x(leaf.parent)), canvas.py(layout.y(leaf.parent))
            dx, dy = lx - ax, ly - ay
            dist = math.hypot(dx, dy) or 1.0
            ox, oy = lx + offset * dx / dist, ly + offset * dy / dist
            angle = math.degrees(math.atan2(dy, dx))
            if -90 <= angle <= 90:
                canvas.raw_text(ox, oy, leaf.name, anchor="start", rotate=angle, size=size, color=color)
            else:
                canvas.raw_text(ox, oy, leaf.name, anchor="end", rotate=angle + 180, size=size, color=color)

    return layer


def node_labels(*, size=None, color="#888888", offset: float = 4.0):
    """Write each internal node's name just above-left of the node. Returns a layer."""

    def layer(canvas, tree, layout, style):
        for node in tree.walk():
            if not node.is_leaf and node.name:
                canvas.text(layout.x(node), layout.y(node), node.name,
                            dx=-offset, dy=-offset, anchor="end",
                            size=size or style.font_size * 0.85, color=color)

    return layer
