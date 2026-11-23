"""Bars for numeric measurements aligned with rectangular tree tips."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ...render import Canvas, text_width
from ...style import Style
from ..layout import Layout
from ..tree import Tree


def tip_bars(values: dict[str, float], *, width: float = 220.0, gap: float = 10.0,
             vmax: float | None = None, color: str = "#6a9bd8",
             ticks: Sequence[float] | None = None,
             label: str = "") -> Callable[[Canvas, Tree, Layout, Style], None]:
    """Draw proportional bars beside the tips on one shared numeric scale.

    Args:
        values: Nonnegative, finite measurements keyed by tip name. Missing tips have no bar.
        width: Maximum bar length in pixels.
        gap: Space beyond the outermost tip or an earlier layer's labels, in pixels.
        vmax: Value at the end of the axis. Defaults to the largest measurement (or 1 for
            all-zero data). Values above an explicit maximum are clipped.
        color: Fill colour for the bars.
        ticks: Positions of grid lines and labelled ticks. Defaults to zero, half and maximum.
            Explicit ticks outside the axis range are omitted.
        label: Text below the numeric axis.

    Returns:
        A layer for a rectangular tree growing right or left. Add ``tip_labels`` before this
        layer to place the bars beyond the names. Bar height is 65% of the minimum row spacing;
        a single-tip tree uses the style's font size to choose its row height.

    Raises:
        ValueError: For invalid measurements, dimensions, unknown tip names or unsupported layouts.
    """
    numbers = {str(name): float(value) for name, value in values.items()}
    if not numbers or any(not math.isfinite(value) or value < 0 for value in numbers.values()):
        raise ValueError("tip_bars: supply at least one finite, nonnegative value")
    if not math.isfinite(width) or width <= 0 or not math.isfinite(gap) or gap < 0:
        raise ValueError("tip_bars: width must be positive and gap nonnegative, both finite")
    maximum = (max(numbers.values()) or 1.0) if vmax is None else float(vmax)
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError("tip_bars: vmax must be finite and positive")
    tick_values = [float(value) for value in ticks] if ticks is not None else [0.0, maximum / 2, maximum]
    if any(not math.isfinite(value) or value < 0 for value in tick_values):
        raise ValueError("tip_bars: ticks must be finite and nonnegative")

    def layer(canvas: Canvas, tree: Tree, layout: Layout, style: Style) -> None:
        if layout.kind != "rectangular" or layout.orientation not in ("right", "left"):
            raise ValueError("tip_bars needs a rectangular tree growing right or left")
        leaves = list(tree.leaves)
        missing = set(numbers) - {leaf.name for leaf in leaves}
        if missing:
            raise ValueError(f"tip_bars: unknown tip names: {', '.join(sorted(missing))}")
        rows = [(leaf.name, canvas.py(layout.y(leaf))) for leaf in leaves]
        ys = sorted(y for _, y in rows)
        spacing = min((b - a for a, b in zip(ys, ys[1:]) if b > a), default=style.font_size * 1.6)
        bar_height = spacing * 0.65
        direction = 1 if layout.orientation == "right" else -1
        farther = max if direction > 0 else min
        edge = farther(canvas.px(layout.x(leaf)) for leaf in leaves)
        edge = farther(edge, canvas.claimed(layout.orientation, edge))
        origin, end = edge + direction * gap, edge + direction * (gap + width)
        top, bottom = ys[0] - bar_height / 2, ys[-1] + bar_height / 2
        axis_y = bottom + 12
        tick_size = style.font_size * 0.85

        for value in sorted(set(tick_values)):
            if value > maximum:
                continue
            x = origin + direction * width * value / maximum
            canvas.raw_line(x, top, x, bottom, "#d9dee3", 0.8)
            canvas.raw_line(x, axis_y, x, axis_y + 5, "#555555", 1.0)
            written = f"{value:g}"
            y = axis_y + tick_size + 3
            canvas.raw_text(x, y, written, anchor="middle", size=tick_size)
            canvas.claim_text(x, y, text_width(written, family=style.font_family, size=tick_size),
                              tick_size, anchor="middle")
        for name, y in rows:
            if name in numbers:
                length = width * min(numbers[name] / maximum, 1.0)
                left = origin if direction > 0 else origin - length
                canvas.raw_rect(left, y - bar_height / 2, length, bar_height, fill=color)
        canvas.raw_line(origin, axis_y, end, axis_y, "#555555", 1.0)
        canvas.claim_box(origin, top, end, axis_y + 5)
        canvas.obstruct(min(origin, end), top, max(origin, end), axis_y + 5)
        if label:
            x, y = (origin + end) / 2, axis_y + tick_size + style.font_size + 6
            canvas.raw_text(x, y, label, anchor="middle", size=style.font_size)
            canvas.claim_text(x, y, text_width(label, family=style.font_family, size=style.font_size),
                              style.font_size, anchor="middle")

    return layer
