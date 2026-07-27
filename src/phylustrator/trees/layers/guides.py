"""Guide layers — the chrome that explains the colours and the scale.

``colorbar`` and ``legend`` read the scale a colouring layer recorded on the canvas (so they need no
data of their own — just add them after ``color_branches``); ``time_axis`` reads the layout extent.
All three draw in pixel space at a fixed spot on the page.
"""

from __future__ import annotations


def colorbar(title: str = "", *, width: float = 130.0, height: float = 10.0,
             size: float | None = None):
    """A gradient bar for a continuous scale, top-left. ``size`` sets the label font (default the
    style's). No-op unless a continuous scale was set."""

    def layer(canvas, tree, layout, style):
        scale = canvas.scale
        if not scale or scale.get("kind") != "continuous":
            return
        m = style.margin
        fs = size if size is not None else style.font_size
        x, y = m, m + fs
        if title:
            canvas.raw_text(x, m - 2, title, anchor="start", weight="bold", size=fs)
        canvas.gradient_bar(scale["cmap"], x, y, width, height)
        canvas.raw_text(x, y + height + fs * 0.9, f"{scale['vmin']:.2f}", anchor="start", size=fs * 0.9)
        canvas.raw_text(x + width, y + height + fs * 0.9, f"{scale['vmax']:.2f}", anchor="end", size=fs * 0.9)

    return layer


def legend(title: str = "", *, swatch: float | None = None, size: float | None = None):
    """A category swatch list, top-left. ``size`` sets the label font (default the style's) and the
    swatch scales with it. No-op unless a categorical scale was set."""

    def layer(canvas, tree, layout, style):
        scale = canvas.scale
        if not scale or scale.get("kind") != "categorical":
            return
        m = style.margin
        fs = size if size is not None else style.font_size
        sw = swatch if swatch is not None else fs * 0.95
        x, y = m, m
        if title:
            canvas.raw_text(x, y, title, anchor="start", weight="bold", size=fs)
            y += fs * 1.7
        for label, color in scale["palette"].items():
            canvas.raw_rect(x, y - sw / 2, sw, sw, fill=color, stroke="#666", stroke_width=0.5)
            canvas.raw_text(x + sw + 8, y, str(label), anchor="start", size=fs)
            y += fs * 1.6

    return layer


def time_marker(*times, color: str = "#444444", width: float = 1.5, dash: bool = True,
                label: str | None = None, label_size: float | None = None):
    """Vertical reference line(s) crossing the tree at the given distance/time value(s) — e.g. to mark
    a mass-extinction moment or a rate shift. Rectangular only (distance maps to x). ``label`` (if
    given) is written above the first line."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            return
        y0, y1 = layout.ylim
        ls = label_size if label_size is not None else style.font_size
        for i, t in enumerate(times):
            canvas.line(t, y0, t, y1, color, width, dash=dash)
            if label and i == 0:
                canvas.text(t, min(y0, y1), label, dy=-8, anchor="middle", color=color, size=ls)

    return layer


def note(text: str, *, loc: str = "top-left", size: float | None = None,
         color: str | None = None, weight: str = "bold"):
    """A short text note pinned to a corner (``"top-left"`` / ``"top-right"`` / ``"bottom-left"`` /
    ``"bottom-right"``) — e.g. to name the model or clock a figure was drawn under."""

    def layer(canvas, tree, layout, style):
        w, h = canvas.size
        m = style.margin
        fs = size if size is not None else style.font_size
        x = m if "left" in loc else w - m
        y = (m * 0.6 + fs) if "top" in loc else (h - m * 0.5)
        anchor = "start" if "left" in loc else "end"
        canvas.raw_text(x, y, text, anchor=anchor, size=fs,
                        color=color or style.label_color, weight=weight)

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
    return float(nice * (10 ** exp))


def time_axis(label: str = "Time", *, ticks: int = 5, tick_size: float | None = None,
              label_size: float | None = None, bold: bool | None = None):
    """A horizontal scale along the bottom, in the layout's distance units (0 at the origin).
    Rectangular only (distance maps to x); use ``scale_bar`` for radial/unrooted. ``tick_size`` /
    ``label_size`` set the tick-number and axis-label font sizes (default: the style's font size);
    the vertical spacing follows the font, so give the figure enough bottom ``margin`` for big text.
    ``bold`` sets the label weight (default: bold only when a ``label_size`` is given)."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            return
        _, height = canvas.size
        m = style.margin
        x0, x1 = 0.0, layout.xlim[1]
        ts = tick_size if tick_size is not None else style.font_size * 0.85
        ls = label_size if label_size is not None else style.font_size
        y = height - m + 14  # just below the tree area, inside the bottom margin
        canvas.raw_line(canvas.px(x0), y, canvas.px(x1), y, "#333333", 1.2)
        for i in range(ticks):
            t = x0 + (x1 - x0) * i / (ticks - 1)
            tx = canvas.px(t)
            canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
            canvas.raw_text(tx, y + ts + 3, f"{t:.2g}", anchor="middle", size=ts)
        if label:
            mid = (canvas.px(x0) + canvas.px(x1)) / 2
            is_bold = (label_size is not None) if bold is None else bold
            weight = "bold" if is_bold else "normal"
            canvas.raw_text(mid, y + ts + ls + 4, label, anchor="middle", size=ls, weight=weight)

    return layer
