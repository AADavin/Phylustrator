"""Guide layers — the chrome that explains the colours and the scale.

``colorbar`` and ``legend`` read the scale a colouring layer recorded on the canvas (so they need no
data of their own — just add them after ``color_branches``); ``time_axis`` reads the layout extent.
All three draw in pixel space at a fixed spot on the page.
"""

from __future__ import annotations


def colorbar(title: str = "", *, width: float = 130.0, height: float = 10.0):
    """A gradient bar for a continuous scale, top-left. No-op unless a continuous scale was set."""

    def layer(canvas, tree, layout, style):
        scale = canvas.scale
        if not scale or scale.get("kind") != "continuous":
            return
        m = style.margin
        x, y = m, m + 10
        if title:
            canvas.raw_text(x, m - 2, title, anchor="start", weight="bold", size=style.font_size)
        canvas.gradient_bar(scale["cmap"], x, y, width, height)
        small = style.font_size * 0.85
        canvas.raw_text(x, y + height + 9, f"{scale['vmin']:g}", anchor="start", size=small)
        canvas.raw_text(x + width, y + height + 9, f"{scale['vmax']:g}", anchor="end", size=small)

    return layer


def legend(title: str = "", *, swatch: float = 11.0):
    """A category swatch list, top-left. No-op unless a categorical scale was set."""

    def layer(canvas, tree, layout, style):
        scale = canvas.scale
        if not scale or scale.get("kind") != "categorical":
            return
        m = style.margin
        x, y = m, m
        if title:
            canvas.raw_text(x, y, title, anchor="start", weight="bold", size=style.font_size)
            y += style.font_size * 1.6
        for label, color in scale["palette"].items():
            canvas.raw_rect(x, y - swatch / 2, swatch, swatch, fill=color, stroke="#666", stroke_width=0.5)
            canvas.raw_text(x + swatch + 6, y, str(label), anchor="start")
            y += style.font_size * 1.5

    return layer


def scale_bar(length: float | None = None, label: str | None = None):
    """A short bar of a fixed distance, bottom-right — the branch-length key for any layout. Defaults
    to a round fraction of the tree's extent. Returns a layer."""

    def layer(canvas, tree, layout, style):
        width, height = canvas.size
        m = style.margin
        span = layout.xlim[1] - layout.xlim[0]
        L = length if length is not None else _round_nice(span / 5 or 1.0)
        px_len = abs(canvas.px(L) - canvas.px(0.0))
        x1, y = width - m, height - m * 0.5
        x0 = x1 - px_len
        canvas.raw_line(x0, y, x1, y, "#333333", 1.6)
        canvas.raw_text((x0 + x1) / 2, y - 8, label or f"{L:.2g}",
                        anchor="middle", size=style.font_size * 0.85)

    return layer


def _round_nice(v: float) -> float:
    """Round to the nearest 1, 2 or 5 times a power of ten."""
    import math
    if v <= 0:
        return 1.0
    exp = math.floor(math.log10(v))
    base = v / (10 ** exp)
    nice = 1 if base < 1.5 else 2 if base < 3.5 else 5 if base < 7.5 else 10
    return nice * (10 ** exp)


def time_axis(label: str = "Time", *, ticks: int = 5):
    """A horizontal scale along the bottom, in the layout's distance units (0 at the origin).
    Rectangular only (distance maps to x); use ``scale_bar`` for radial/unrooted."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            return
        _, height = canvas.size
        m = style.margin
        x0, x1 = 0.0, layout.xlim[1]
        y = height - m + 14  # just below the tree area, inside the bottom margin
        canvas.raw_line(canvas.px(x0), y, canvas.px(x1), y, "#333333", 1.2)
        small = style.font_size * 0.85
        for i in range(ticks):
            t = x0 + (x1 - x0) * i / (ticks - 1)
            tx = canvas.px(t)
            canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
            canvas.raw_text(tx, y + 13, f"{t:.2g}", anchor="middle", size=small)
        if label:
            mid = (canvas.px(x0) + canvas.px(x1)) / 2
            canvas.raw_text(mid, y + 26, label, anchor="middle", size=style.font_size)

    return layer
