"""Panels that line up with a tree's **x** axis, drawn under a rectangular tree by
:func:`~phylustrator.compose.below`.

A row panel (``genomes.heatmap``, ``genomes.bars``) is handed one pixel ``y`` per tip and sits beside
the tree. These go the other way: a panel is handed the tree's :class:`~phylustrator.trees.Geometry`
and a pixel band ``[top, bottom]``, and places each value at its node's pixel x — so a quantity
measured at a node sits directly under that node.
"""

from __future__ import annotations

import math

from .layers.guides import _round_step, _text_width


class NodePoints:
    """One point per named node, at the node's x and at a height set by its value.

    ``values`` is ``{node name: number}``. Internal nodes count, so they need names (a ZOMBI2 tree
    names every node). A name the tree does not have raises an error rather than dropping the point:
    a typo would otherwise read as a missing measurement.

    ``colors`` tints points per node, else the flat ``color``. ``line`` joins the points left to
    right. ``zero`` draws a light line at 0 when the range crosses it — the reference a difference is
    read against. ``vmin`` / ``vmax`` fix the y range; by default it is the values' range, widened
    to round numbers. ``label`` names the y axis.
    """

    def __init__(self, values: dict, *, color: str = "#3a6ea5", colors: dict | None = None,
                 shape: str = "circle", size: float = 4.5, line: bool = False,
                 line_color: str | None = None, zero: bool = True, vmin: float | None = None,
                 vmax: float | None = None, label: str = "", ticks: int = 5) -> None:
        if not values:
            raise ValueError("node_points() needs at least one value")
        self.values = {str(k): float(v) for k, v in values.items()}
        self.color = color
        self.colors = {str(k): v for k, v in colors.items()} if colors else {}
        self.shape = shape
        self.size = size
        self.line = line
        self.line_color = line_color
        self.zero = zero
        self.vmin = vmin
        self.vmax = vmax
        self.label = label
        self.ticks = ticks

    def _range(self) -> tuple[float, float, float]:
        """The y range and its tick step. An end the caller did not fix is pushed out to the next
        round tick, so the axis starts and stops on a labelled number."""
        lo = min(self.values.values()) if self.vmin is None else self.vmin
        hi = max(self.values.values()) if self.vmax is None else self.vmax
        if hi <= lo:                              # one value, or all equal: give it a band to sit in
            lo, hi = lo - 1.0, hi + 1.0
        step = _round_step(hi - lo, self.ticks)
        if self.vmin is None:
            lo = math.floor(lo / step + 1e-9) * step
        if self.vmax is None:
            hi = math.ceil(hi / step - 1e-9) * step
        return lo, hi, step

    def draw_below(self, canvas, geometry, top: float, bottom: float, style) -> None:
        at: dict[str, float] = {}
        for node in geometry.nodes:
            if node.name:
                at.setdefault(node.name, node.x)          # the first in preorder, as Tree.find
        missing = sorted(set(self.values) - set(at))
        if missing:
            shown = ", ".join(missing[:5]) + (", …" if len(missing) > 5 else "")
            raise ValueError(f"node_points: {len(missing)} name(s) not in the tree: {shown}")

        lo, hi, step = self._range()

        def py(v: float) -> float:
            return bottom - (v - lo) / (hi - lo) * (bottom - top)

        x0, x1 = geometry.x_pixels
        ts, ls = style.font_size * 0.85, style.font_size
        # the y axis stands a little left of time 0, so a point at the crown is not drawn on it
        ax = x0 - 10
        canvas.raw_line(ax, top, ax, bottom, "#333333", 1.2)
        widest = 0.0
        k = math.ceil(lo / step - 1e-9)
        while k * step <= hi + step * 1e-9:
            v = round(k * step, 10) + 0.0                 # + 0.0 turns a -0.0 into 0
            text = f"{v:g}"
            canvas.raw_line(ax - 5, py(v), ax, py(v), "#333333", 1.2)
            canvas.raw_text(ax - 8, py(v), text, anchor="end", size=ts)
            widest = max(widest, _text_width(text, ts))
            k += 1
        if self.label:
            canvas.raw_text(ax - 8 - widest - ls * 0.8, (top + bottom) / 2, self.label,
                            anchor="middle", size=ls, rotate=-90)
        if self.zero and lo < 0.0 < hi:
            canvas.raw_line(x0, py(0.0), x1, py(0.0), "#b8bec3", 1.0)

        points = sorted((at[name], py(v), name) for name, v in self.values.items())
        if self.line:
            for (xa, ya, _), (xb, yb, _) in zip(points, points[1:]):
                canvas.raw_line(xa, ya, xb, yb, self.line_color or self.color, 1.4)
        for x, y, name in points:
            canvas.raw_marker(x, y, self.shape, self.colors.get(name, self.color), self.size)


def node_points(values: dict, **kw) -> NodePoints:
    """A panel under a tree: one point per named node, placed at the node's time. Pass it to
    :func:`~phylustrator.compose.below`; see :class:`NodePoints` for the options."""
    return NodePoints(values, **kw)
