"""Panels that line up with a tree's **x** axis, drawn under a rectangular tree by
:func:`~phylustrator.compose.below`.

A row panel (``genomes.heatmap``, ``genomes.bars``) is handed one pixel ``y`` per tip and sits beside
the tree. These go the other way: a panel is handed the tree's :class:`~phylustrator.trees.Geometry`
and a pixel band ``[top, bottom]``, and places each value at its node's pixel x — so a quantity
measured at a node sits directly under that node.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from .layers.guides import _round_step, _text_width


class _TimePanel:
    """What every panel under a tree shares: a y range, its axis, and the pixel mapping onto it.

    The range, the rounded ticks, the label turned on its side and the line at zero are the same
    whatever is drawn in the band, and two panels under one tree have to agree about them or they
    cannot be read together."""

    def __init__(self, *, vmin, vmax, label, ticks, zero) -> None:
        self.vmin = vmin
        self.vmax = vmax
        self.label = label
        self.ticks = ticks
        self.zero = zero

    def _reach(self) -> list:
        """Every number the panel has to fit between its top and its bottom."""
        raise NotImplementedError

    def r_range(self) -> tuple[float, float, float]:
        """The y range this panel will draw itself on: ``(low, high, tick step)``.

        Two panels under one tree have to agree about it, and a caller comparing figures may want
        to fix it with ``vmin``/``vmax``, so it is answerable without drawing anything."""
        return self._range()

    def _range(self) -> tuple[float, float, float]:
        """The y range and its tick step. An end the caller did not fix is pushed out to the next
        round tick, so the axis starts and stops on a labelled number."""
        reach = self._reach()
        lo = min(reach) if self.vmin is None else self.vmin
        hi = max(reach) if self.vmax is None else self.vmax
        if hi <= lo:                              # one value, or all equal: give it a band to sit in
            lo, hi = lo - 1.0, hi + 1.0
        step = _round_step(hi - lo, self.ticks)
        if self.vmin is None:
            lo = math.floor(lo / step + 1e-9) * step
        if self.vmax is None:
            hi = math.ceil(hi / step - 1e-9) * step
        return lo, hi, step

    def _draw_axis(self, canvas, geometry, top: float, bottom: float,
                   style) -> tuple[Callable[[float], float], float, float]:
        """The y axis, its ticks and its label. Returns the value-to-pixel mapping for the body."""
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
        return py, lo, hi


class NodePoints(_TimePanel):
    """One point per named node, at the node's x and at a height set by its value.

    ``values`` is ``{node name: number}``. Internal nodes count, so they need names (a ZOMBI2 tree
    names every node). A name the tree does not have raises an error rather than dropping the point:
    a typo would otherwise read as a missing measurement.

    ``intervals`` is ``{node name: (low, high)}`` — the uncertainty on that node's value, drawn as
    a whisker through its point. A value measured on a tree usually comes with one, and a panel that
    could draw the estimate and not its interval left the interval nowhere to go. The y range grows
    to hold the whiskers, so a bar is never cut off at the edge of the panel.

    ``colors`` tints points per node, else the flat ``color``. ``line`` joins the points left to
    right. ``zero`` draws a light line at 0 when the range crosses it — the reference a difference is
    read against. ``vmin`` / ``vmax`` fix the y range; by default it is the values' range, widened
    to round numbers. ``label`` names the y axis.
    """

    def __init__(self, values: dict, *, color: str = "#3a6ea5", colors: dict | None = None,
                 shape: str = "circle", size: float = 4.5, line: bool = False,
                 line_color: str | None = None, zero: bool = True, vmin: float | None = None,
                 vmax: float | None = None, label: str = "", ticks: int = 5,
                 intervals: dict | None = None, interval_width: float = 1.4,
                 interval_cap: float = 4.0) -> None:
        super().__init__(vmin=vmin, vmax=vmax, label=label, ticks=ticks, zero=zero)
        if not values:
            raise ValueError("node_points() needs at least one value")
        self.values = {str(k): float(v) for k, v in values.items()}
        self.intervals = {}
        for name, pair in (intervals or {}).items():
            low, high = (float(v) for v in pair)
            if low > high:
                raise ValueError(f"node_points: the interval for {name!r} is ({low:g}, {high:g}), "
                                 f"which runs backwards. Give it as (low, high).")
            if str(name) not in self.values:
                raise ValueError(f"node_points: {name!r} has an interval but no value. An interval "
                                 f"is drawn through its point, so the point has to be there.")
            self.intervals[str(name)] = (low, high)
        self.interval_width = interval_width
        self.interval_cap = interval_cap
        self.color = color
        self.colors = {str(k): v for k, v in colors.items()} if colors else {}
        self.shape = shape
        self.size = size
        self.line = line
        self.line_color = line_color

    def _reach(self) -> list:
        # the whiskers count: a range taken from the estimates alone cuts the bars off at the
        # edge of the panel, which reads as an interval that stops there
        reach = list(self.values.values())
        for low, high in self.intervals.values():
            reach += [low, high]
        return reach

    def draw_below(self, canvas, geometry, top: float, bottom: float, style) -> None:
        at: dict[str, float] = {}
        for node in geometry.nodes:
            if node.name:
                at.setdefault(node.name, node.x)          # the first in preorder, as Tree.find
        missing = sorted(set(self.values) - set(at))
        if missing:
            shown = ", ".join(missing[:5]) + (", …" if len(missing) > 5 else "")
            raise ValueError(f"node_points: {len(missing)} name(s) not in the tree: {shown}")

        py, lo, hi = self._draw_axis(canvas, geometry, top, bottom, style)

        # the whiskers go under the points, so a point is never half-hidden by its own bar
        for name, (low, high) in self.intervals.items():
            x, paint = at[name], self.colors.get(name, self.color)
            y_low, y_high = py(max(low, lo)), py(min(high, hi))
            canvas.raw_line(x, y_low, x, y_high, paint, self.interval_width)
            for y, end in ((y_low, low), (y_high, high)):
                if lo <= end <= hi:              # no cap on an end that runs past the axis
                    canvas.raw_line(x - self.interval_cap, y, x + self.interval_cap, y, paint,
                                    self.interval_width)

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


class Band(_TimePanel):
    """A shaded region between a low and a high series, on the tree's time axis.

    ``values`` is ``{time: (low, high)}`` — a quantity sampled along the tree rather than measured
    at its nodes: a rate through time, a posterior band, a running count with its credible interval.
    :class:`NodePoints` is keyed by node and says nothing between the nodes, so a quantity sampled
    on a grid of times had nowhere to go.

    ``middle`` (``{time: value}``) draws the estimate as a line through the band. It is given
    separately because the middle of an interval is not usually the estimate, and drawing it as one
    would put a line where no number is.

    ``color`` fills the band, ``opacity`` fades it, ``line_color`` draws the middle (the fill colour
    by default). The y axis is :class:`NodePoints`'s, so a band and a set of points under the same
    tree can be read against each other.
    """

    def __init__(self, values: dict, *, middle: dict | None = None, color: str = "#3a6ea5",
                 opacity: float = 0.25, line_color: str | None = None, line_width: float = 1.6,
                 edge: bool = False, vmin: float | None = None, vmax: float | None = None,
                 label: str = "", ticks: int = 5, zero: bool = True) -> None:
        super().__init__(vmin=vmin, vmax=vmax, label=label, ticks=ticks, zero=zero)
        self.values = {}
        for t, pair in values.items():
            low, high = (float(v) for v in pair)
            if low > high:
                raise ValueError(f"band: the pair at time {float(t):g} is ({low:g}, {high:g}), "
                                 f"which runs backwards. Give it as (low, high).")
            self.values[float(t)] = (low, high)
        if len(self.values) < 2:
            raise ValueError("band() needs at least two times: one is a bar, not a band. "
                             "node_points(intervals=…) draws a value and its interval at a node.")
        self.middle = {float(t): float(v) for t, v in (middle or {}).items()}
        self.color = color
        self.opacity = opacity
        self.line_color = line_color
        self.line_width = line_width
        self.edge = edge

    def _reach(self) -> list:
        reach = [v for pair in self.values.values() for v in pair]
        return reach + list(self.middle.values())

    def draw_below(self, canvas, geometry, top: float, bottom: float, style) -> None:
        py, lo, hi = self._draw_axis(canvas, geometry, top, bottom, style)
        times = sorted(self.values)

        def at(v: float) -> float:
            return py(min(max(v, lo), hi))        # a series running past a fixed range is clamped

        lows = [(geometry.px(t), at(self.values[t][0])) for t in times]
        highs = [(geometry.px(t), at(self.values[t][1])) for t in times]
        # out along the top and back along the bottom: one closed shape, so the band is filled
        # between the two series rather than being two lines with a guess in between
        canvas.raw_polygon(highs + lows[::-1], fill=self.color, opacity=self.opacity,
                           stroke=self.color if self.edge else "none",
                           stroke_width=0.8 if self.edge else 0.0)
        if self.middle:
            paint = self.line_color or self.color
            drawn = sorted(self.middle)
            for ta, tb in zip(drawn, drawn[1:]):
                canvas.raw_line(geometry.px(ta), at(self.middle[ta]),
                                geometry.px(tb), at(self.middle[tb]), paint, self.line_width)


def band(values: dict, **kw) -> Band:
    """A panel under a tree: a shaded region between a low and a high series, on the tree's time
    axis. Pass it to :func:`~phylustrator.compose.below`; see :class:`Band` for the options."""
    return Band(values, **kw)
