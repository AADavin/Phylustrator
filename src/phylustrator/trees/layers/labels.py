"""Text layers — names, or any per-node value, beside tips and internal nodes.

Both layers write a node's name by default. ``values`` (a dict keyed by node name, spelled like
``color_branches``) or ``text`` (a callable) writes something else instead: an ancestral estimate, a
support value, a node age. The library could colour by a dict and not label by one, which is an odd
pair of capabilities.
"""

from __future__ import annotations

import math


def _as_text(value) -> str | None:
    """A value as label text. Numbers are written plainly — 81, not 81.0."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return f"{value:g}"


def _labeller(values, text):
    """What to write at a node: ``text`` if given, else ``values`` by name, else the node's name."""
    if text is not None:
        return text
    if values is not None:
        table = {str(k): v for k, v in values.items()}
        return lambda node: _as_text(table.get(node.name))
    return lambda node: node.name


def tip_labels(*, size=None, color=None, offset: float = 6.0, values=None, text=None):
    """Write each leaf's name just past its tip. On a rectangular tree the names sit to the right; on a
    radial or unrooted tree they are rotated to run along the branch (flipped on the left side so they
    stay upright). ``values`` (``{tip name: value}``) or ``text`` (``text(node) -> str``) writes
    something else; a tip with no value of its own is left unlabelled. Returns a layer."""
    say = _labeller(values, text)

    def layer(canvas, tree, layout, style):
        for leaf in tree.leaves:
            written = say(leaf)
            if not written:
                continue
            if layout.kind == "rectangular":
                canvas.text(layout.x(leaf), layout.y(leaf), written,
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
                canvas.raw_text(ox, oy, written, anchor="start", rotate=angle, size=size, color=color)
            else:
                canvas.raw_text(ox, oy, written, anchor="end", rotate=angle + 180, size=size, color=color)

    return layer


def node_labels(*, size=None, color="#888888", offset: float = 4.0, values=None, text=None,
                leaves: bool = False):
    """Write each internal node's name just above-left of the node. ``values``
    (``{node name: value}``) or ``text`` (``text(node) -> str``) writes something else — an
    ancestral estimate, a support value, a node age — and a node with no value is left unlabelled.
    ``leaves`` also labels the tips, for a value that every node carries. Returns a layer."""
    say = _labeller(values, text)

    def layer(canvas, tree, layout, style):
        for node in tree.walk():
            if node.is_leaf and not leaves:
                continue
            written = say(node)
            if written:
                canvas.text(layout.x(node), layout.y(node), written,
                            dx=-offset, dy=-offset, anchor="end",
                            size=size or style.font_size * 0.85, color=color)

    return layer
