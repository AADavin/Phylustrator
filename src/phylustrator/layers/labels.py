"""Text layers — names beside tips and internal nodes."""

from __future__ import annotations


def tip_labels(*, size=None, color=None, offset: float = 6.0):
    """Write each leaf's name just to the right of its tip. Returns a layer."""

    def layer(canvas, tree, layout, style):
        for leaf in tree.leaves:
            if leaf.name:
                canvas.text(layout.x(leaf), layout.y(leaf), leaf.name,
                            dx=offset, anchor="start", size=size, color=color)

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
