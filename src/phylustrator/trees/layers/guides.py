"""Guide layers — the chrome that explains the colours and the scale.

``colorbar`` and ``legend`` read the scale a colouring layer recorded on the canvas (so they need no
data of their own — just add them after ``color_branches``); ``time_axis`` reads the layout extent.
All three draw in pixel space at a fixed spot on the page.
"""

from __future__ import annotations

#: A key drawn inside the plotting area sits on top of the tree, and a branch running under the
#: letters makes both unreadable. Every key here paints this behind itself first: the page colour,
#: no border, so it reads as a gap in the tree rather than as a box someone added.
_KEY_BACKDROP = "#ffffff"


def _clear_behind(canvas, x, y, w, h, pad: float = 6.0) -> None:
    canvas.raw_rect(x - pad, y - pad, w + 2 * pad, h + 2 * pad,
                    fill=_KEY_BACKDROP, stroke="none", stroke_width=0.0)


def _text_width(text: str, size: float) -> float:
    """A serviceable width for a string at this font size — the canvas has no font metrics, and this
    only has to be close enough to clear the tree behind it."""
    return len(text) * size * 0.58


def colorbar(title: str = "", *, loc: str = "top-left", width: float = 130.0, height: float = 10.0,
             size: float | None = None, labels: tuple[str, str] | None = None,
             inset: float | None = None):
    """A gradient bar for a continuous scale, pinned to a left corner (``"top-left"`` default or
    ``"bottom-left"`` — to clear the tree). ``size`` sets the label font (default the style's). ``inset`` anchors the corner at a fixed distance instead of the style margin, so a large-margin figure can still tuck its guides into the corner. No-op
    unless a continuous scale was set.

    ``labels`` replaces the two end labels. The bar otherwise prints the values it was coloured by,
    which is wrong whenever those are a transform of the quantity the reader cares about: colour a
    tree by ``log10(rate)`` and the ends read ``-1.31`` and ``-0.33`` rather than the rates
    themselves. Pass the strings you want instead."""

    def layer(canvas, tree, layout, style):
        scale = canvas.scale
        if not scale or scale.get("kind") != "continuous":
            return
        _, h = canvas.size
        left, top, bottom = ((inset, inset, inset) if inset is not None else
                             (style.margin_at("left"), style.margin_at("top"), style.margin_at("bottom")))
        fs = size if size is not None else style.font_size
        x = left
        if "bottom" in loc:
            y = h - bottom * 0.5 - height - fs * 0.9   # bar top, leaving room for the min/max labels
            title_y = y - fs * 0.6 - 2
        else:
            y, title_y = top + fs, top - 2
        lo, hi = labels if labels else (f"{scale['vmin']:.2f}", f"{scale['vmax']:.2f}")
        top = min(title_y - fs, y) if title else y
        bottom = y + height + fs * 1.1
        wide = max(width, _text_width(title, fs) if title else 0.0)
        _clear_behind(canvas, x, top, wide, bottom - top)
        if title:
            canvas.raw_text(x, title_y, title, anchor="start", weight="bold", size=fs)
        canvas.gradient_bar(scale["cmap"], x, y, width, height)
        canvas.raw_text(x, y + height + fs * 0.9, lo, anchor="start", size=fs * 0.9)
        canvas.raw_text(x + width, y + height + fs * 0.9, hi, anchor="end", size=fs * 0.9)

    return layer


def legend(title: str = "", *, swatch: float | None = None, size: float | None = None,
           entries: dict | None = None, dy: float = 0.0, inset: float | None = None):
    """A category swatch list, top-left. ``size`` sets the label font (default the style's) and the
    swatch scales with it. Reads the recorded categorical scale, or ``entries``
    (``{label: colour}``) to draw an explicit list — a figure whose scale slot is taken by a
    continuous ring still gets its categorical legend that way. ``dy`` shifts the list down, so it
    can sit below a ``colorbar`` on the same corner. No-op without a source of entries."""

    def layer(canvas, tree, layout, style):
        palette = entries
        if palette is None:
            scale = canvas.scale
            if not scale or scale.get("kind") != "categorical":
                return
            palette = scale["palette"]
        fs = size if size is not None else style.font_size
        sw = swatch if swatch is not None else fs * 0.95
        x = inset if inset is not None else style.margin_at("left")
        y = (inset if inset is not None else style.margin_at("top")) + dy
        rows = len(palette) + (1 if title else 0)
        widest = max([_text_width(str(k), fs) for k in palette] +
                     [_text_width(title, fs) if title else 0.0])
        _clear_behind(canvas, x, y - fs, sw + 8 + widest, rows * fs * 1.65)
        if title:
            canvas.raw_text(x, y, title, anchor="start", weight="bold", size=fs)
            y += fs * 1.7
        for label, color in palette.items():
            canvas.raw_rect(x, y - sw / 2, sw, sw, fill=color, stroke="#666", stroke_width=0.5)
            canvas.raw_text(x + sw + 8, y, str(label), anchor="start", size=fs)
            y += fs * 1.6

    return layer


def time_marker(*times, color: str = "#444444", width: float = 1.5, dash: bool = True,
                label: str | None = None, label_size: float | None = None):
    """Reference marker(s) at the given distance/time value(s) — e.g. a mass-extinction moment or a
    rate shift. Rectangular: a vertical line crossing the tree. Radial: a circle at that distance
    from the centre, which is what a depth threshold looks like on a tree too big to read as a
    rectangle. The unrooted layout places branches by angle and has no distance-from-origin axis, so
    it raises rather than drawing nothing. ``label`` (if given) is written above the first marker.

    Times come on the stem-inclusive scale of the rectangular layout, the same scale
    ``branch_events`` takes. The radial layout starts at the crown, so the stem comes off there."""

    def layer(canvas, tree, layout, style):
        ls = label_size if label_size is not None else style.font_size
        if layout.kind == "unrooted":
            raise ValueError("time_marker needs a layout with a distance axis, and the unrooted "
                             "layout has none: it places branches by angle, so a distance from the "
                             "origin is not a place on it. Use rectangular or radial.")
        if layout.kind == "radial":
            # the radial layout drops the stem and starts at the crown, so shift the times by it —
            # branch_events shifts the same way, for the same reason
            stem = float(tree.root.length or 0.0)
            for i, t in enumerate(times):
                r = t - stem
                if r < 0:
                    raise ValueError(f"time_marker at {t:g} falls inside the root stem, which the "
                                     f"radial layout does not draw: its centre is the crown, at {stem:g}")
                canvas.data_ring(r, color, width, dash=dash)
                if label and i == 0:
                    canvas.text(0.0, -r, label, dy=-8, anchor="middle", color=color, size=ls)
            return
        y0, y1 = layout.ylim
        for i, t in enumerate(times):
            canvas.line(t, y0, t, y1, color, width, dash=dash)
            if label and i == 0:
                canvas.text(t, min(y0, y1), label, dy=-8, anchor="middle", color=color, size=ls)

    return layer


def note(text: str, *, loc: str = "top-left", size: float | None = None,
         color: str | None = None, weight: str = "bold", dy: float = 0.0):
    """A short text note pinned to a corner (``"top-left"`` / ``"top-right"`` / ``"bottom-left"`` /
    ``"bottom-right"``) — e.g. to name the model or clock a figure was drawn under.

    ``dy`` nudges it in pixels, negative up. The corner is fixed to the margin, which is the right
    place for a note *about* the figure; a note read as a **title** wants a little more air between
    it and the tree than a margin the tree also uses can give."""

    def layer(canvas, tree, layout, style):
        w, h = canvas.size
        fs = size if size is not None else style.font_size
        x = style.margin_at("left") if "left" in loc else w - style.margin_at("right")
        y = (style.margin_at("top") * 0.6 + fs) if "top" in loc else (h - style.margin_at("bottom") * 0.5)
        y += dy
        anchor = "start" if "left" in loc else "end"
        canvas.raw_text(x, y, text, anchor=anchor, size=fs,
                        color=color or style.label_color, weight=weight)

    return layer


def scale_bar(length: float | None = None, label: str | None = None):
    """A short bar of a fixed distance, bottom-right — the branch-length key for any layout. Defaults
    to a round fraction of the tree's extent. Returns a layer."""

    def layer(canvas, tree, layout, style):
        width, height = canvas.size
        span = layout.xlim[1] - layout.xlim[0]
        L = length if length is not None else _round_nice(span / 5 or 1.0)
        px_len = abs(canvas.px(L) - canvas.px(0.0))
        x1, y = width - style.margin_at("right"), height - style.margin_at("bottom") * 0.5
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


def _round_ticks(span: float, target: int) -> list[float]:
    """About ``target`` tick positions from 0 to at most ``span``, at multiples of a
    round step (1, 2, 2.5 or 5 times a power of ten). The last tick may stop short
    of the axis end; a round number short of the edge beats an exact ugly one."""
    if span <= 0:
        return [0.0]
    step = _round_step(span, target)
    n = int(span / step + 1e-9)
    return [round(i * step, 10) for i in range(n + 1)]


def _round_step(span: float, target: int) -> float:
    """The round step (1, 2, 2.5 or 5 times a power of ten) that cuts ``span`` into at most
    ``target - 1`` intervals. ``span`` must be positive."""
    import math
    raw = span / max(target - 1, 1)
    mag = 10.0 ** math.floor(math.log10(raw))
    for mult in (1, 2, 2.5, 5, 10):
        if span / (mult * mag) <= target - 1 + 1e-9:
            return mult * mag
    return 10 * mag


def time_axis(label: str = "Time", *, ticks: int = 5, tick_size: float | None = None,
              label_size: float | None = None, bold: bool | None = None):
    """A horizontal scale along the bottom, in the layout's distance units (0 at the origin).
    Rectangular only (distance maps to x); use ``scale_bar`` for radial/unrooted. ``tick_size`` /
    ``label_size`` set the tick-number and axis-label font sizes (default: the style's font size);
    the vertical spacing follows the font, so give the figure enough bottom margin for big text.
    ``bold`` sets the label weight (default: bold only when a ``label_size`` is given)."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            return
        _, height = canvas.size
        ts = tick_size if tick_size is not None else style.font_size * 0.85
        ls = label_size if label_size is not None else style.font_size
        is_bold = (label_size is not None) if bold is None else bold
        y = height - style.margin_at("bottom") + 14  # just below the tree area, inside the bottom margin
        draw_time_axis(canvas, canvas.px, layout.xlim[1], y, label, ticks=ticks, tick_size=ts,
                       label_size=ls, weight="bold" if is_bold else "normal")

    return layer


def draw_time_axis(canvas, px, x_end: float, y: float, label: str | None, *, ticks: int = 5,
                   tick_size: float, label_size: float, weight: str = "normal") -> None:
    """Draw a time axis from 0 to ``x_end`` at pixel height ``y``, with ``px`` mapping a time to a
    pixel x. Shared by :func:`time_axis` and :func:`~phylustrator.compose.below`, so an axis under a
    panel is the same axis a tree draws under itself."""
    canvas.raw_line(px(0.0), y, px(x_end), y, "#333333", 1.2)
    # ticks at round numbers (a 1 / 2 / 2.5 / 5 step), not at even fractions of the
    # height: dividing a height of 3.96 into quarters gave "0, 0.99, 2, 3, 4",
    # where the "2" was really 1.98 — ugly and, worse, slightly wrong
    for t in _round_ticks(x_end, ticks):
        tx = px(t)
        canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
        canvas.raw_text(tx, y + tick_size + 3, f"{t:g}", anchor="middle", size=tick_size)
    if label:
        mid = (px(0.0) + px(x_end)) / 2
        canvas.raw_text(mid, y + tick_size + label_size + 4, label, anchor="middle", size=label_size,
                        weight=weight)
