"""The node-halves layer — a disc at a node, split in two, each half a colour or open.

Two things at once at every node: for example whether gene A (left half) and gene B (right half)
are inferred present at that ancestor. ``halves`` maps a node name to ``(left, right)``, each a
colour or ``None`` for an open half. Nodes not in the map get no disc. Leaves may be given too.
"""

from __future__ import annotations

import math


def node_halves(halves, *, radius: float = 4.0, empty: str = "#ffffff", stroke: str = "#9a9a9a",
                stroke_width: float = 0.5, opacity: float = 1.0):
    """Draw the discs of ``halves`` (``{node name: (left colour or None, right colour or None)}``).
    ``radius`` is in pixels; an open half is filled with ``empty`` and outlined with ``stroke``; a
    coloured half is outlined in its own colour. Returns a layer."""

    def layer(canvas, tree, layout, style):
        by_name = {n.name: n for n in tree.walk() if n.name}
        left_arc = (math.pi / 2, 3 * math.pi / 2)
        right_arc = (-math.pi / 2, math.pi / 2)
        for name, pair in halves.items():
            node = by_name.get(name)
            if node is None:
                continue
            cx, cy = canvas.px(layout.x(node)), canvas.py(layout.y(node))
            for colour, (a0, a1) in zip(pair, (left_arc, right_arc)):
                fill = colour or empty
                canvas.raw_annulus_sector(cx, cy, 0.0, radius, a0, a1, fill=fill,
                                          stroke=colour or stroke, stroke_width=stroke_width,
                                          opacity=opacity)

    return layer
