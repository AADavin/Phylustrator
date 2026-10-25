"""The node-intervals layer — the uncertainty on a node's age.

A dated tree usually comes with an interval on each node age: an HPD from a molecular clock, or
bounds from any other method. The bar runs along the layout's distance axis at the node's own row,
on the same scale ``time_marker`` and ``branch_events`` take.
"""

from __future__ import annotations

import math


def node_intervals(spans, *, color: str = "#6a9bd8", colors: dict | None = None,
                   width: float = 6.0, opacity: float = 0.45, cap: str = "butt",
                   before_present: bool = False):
    """Draw ``spans`` (``{node name: (low, high)}``) as a bar at each node.

    ``colors`` tints one node's own bar, the way ``branch_events`` lets one event carry its own
    colour — to tell apart the intervals that do and do not contain a known value. ``opacity`` lets
    the branch show through, since a bar wider than the branch is the normal case and should not
    hide the tree; ``cap`` squares the ends off, so a wide bar does not read as longer than it is.
    To put the bars behind the tree entirely, plot with ``skeleton=False`` and add this layer before
    the colouring layer.

    ``spans`` are distances from the root, the scale ``time_marker`` and ``branch_events`` take.
    ``before_present=True`` reads them as **ages** instead, counted back from the furthest tip, which
    is how a clock quotes an HPD and how ``time_axis(before_present=True)`` labels its ticks. Pass
    ages to a layer expecting distances and every bar lands somewhere else on the tree.

    Rectangular: a horizontal bar at the node's row. Radial: the same span of distance along the
    node's own angle, since there the radius is the time axis — an arc at fixed radius would span
    tip order instead. The unrooted layout has no distance axis and raises.
    """
    table = {str(k): (float(lo), float(hi)) for k, (lo, hi) in spans.items()}
    tint = {str(k): v for k, v in (colors or {}).items()}

    def layer(canvas, tree, layout, style):
        if layout.kind == "unrooted":
            raise ValueError("node_intervals needs a layout with a distance axis, and the unrooted "
                             "layout has none: it places branches by angle, so an age is not a place "
                             "on it. Use the rectangular or radial layout.")
        if layout.kind == "diagonal":
            raise ValueError("node_intervals cannot be drawn on the diagonal layout yet: a bar at a "
                             "node's row needs an axis the bar can run along, and a slanted branch "
                             "has none. Use the rectangular layout for a dated tree with intervals.")
        by_name = {n.name: n for n in tree.walk() if n.name}
        missing = sorted(set(table) - set(by_name))
        if missing:
            shown = ", ".join(missing[:5]) + (", …" if len(missing) > 5 else "")
            raise ValueError(f"node_intervals: {len(missing)} name(s) not in the tree: {shown}")
        # the radial layout starts at the crown and drops the stem, as branch_events does
        stem_off = float(tree.root.length or 0.0) if layout.kind == "radial" else 0.0
        if layout.kind == "rectangular":
            end = layout.xlim[1]
        else:
            end = stem_off + max(math.hypot(layout.x(n), layout.y(n)) for n in tree.walk())
        for name, (lo, hi) in table.items():
            node = by_name[name]
            paint = tint.get(name, color)
            if before_present:                     # ages run the other way: the older end is first
                lo, hi = end - hi, end - lo
            if layout.kind == "rectangular":
                y = layout.y(node)
                canvas.line(lo, y, hi, y, paint, width, opacity=opacity, cap=cap)
            else:
                a = layout.angle[node]
                r0, r1 = max(lo - stem_off, 0.0), max(hi - stem_off, 0.0)
                canvas.line(r0 * math.cos(a), r0 * math.sin(a), r1 * math.cos(a), r1 * math.sin(a),
                            paint, width, opacity=opacity, cap=cap)

    return layer
