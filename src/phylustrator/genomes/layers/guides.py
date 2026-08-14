"""Guide layers — the chrome that reads the coordinates.

``position_axis`` adapts to the layout: a horizontal ruler for ``linear``, and an inner coordinate
**ring** (base-position ticks around the circle) for ``circular`` — the standard reference on a
circular genome map.
"""

from __future__ import annotations

import math


def position_axis(label: str = "position", *, ticks: int = 6):
    """A coordinate axis in the layout's units: a horizontal ruler (``linear``) or an inner ring of
    base-position ticks (``circular``)."""

    def layer(canvas, primary, layout, style):
        if layout.kind == "circular":
            _circular(canvas, layout, style)
        else:
            _linear(canvas, layout, style, label, ticks)

    return layer


def _linear(canvas, layout, style, label, ticks) -> None:
    _, height = canvas.size
    m = style.margin
    x0, x1 = layout.xlim
    y = height - m * 0.62
    canvas.raw_line(canvas.px(x0), y, canvas.px(x1), y, "#333333", 1.2)
    small = style.font_size * 0.85
    for i in range(ticks):
        t = x0 + (x1 - x0) * i / (ticks - 1)
        tx = canvas.px(t)
        canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
        canvas.raw_text(tx, y + 12, f"{t:.0f}", anchor="middle", size=small)
    if label:
        mid = (canvas.px(x0) + canvas.px(x1)) / 2
        canvas.raw_text(mid, y + 24, label, anchor="middle", size=style.font_size)


def _circular(canvas, layout, style) -> None:
    total = layout.totals[0] if layout.totals else 1.0
    start, sweep = layout.angle_start, layout.angle_sweep
    # the axis sits inside the innermost circle — and on *its* centre, which a row of circles moves
    k = min(range(len(layout.rings)), key=lambda i: layout.rings[i]) if layout.rings else 0
    R0 = layout.rings[k] if layout.rings else 0.85
    cx, cy = layout.ring_centre(k)
    inner = R0 - layout.half_height(R0) - 0.06
    canvas.data_ring(inner, "#c7d0cc", 1.0, centre=(cx, cy))      # the coordinate ring
    step = _nice_step(total, 8)
    small = style.font_size * 0.9
    v = 0.0
    while v < total - step * 1e-6:
        a = start - (v / total) * sweep
        # y negated, as in track._polar: the page's y grows downward and the angles do not
        canvas.line(cx + inner * math.cos(a), cy - inner * math.sin(a),
                    cx + (inner - 0.03) * math.cos(a), cy - (inner - 0.03) * math.sin(a),
                    "#5a6763", 1.1)
        lx, ly = cx + (inner - 0.10) * math.cos(a), cy - (inner - 0.10) * math.sin(a)
        canvas.text(lx, ly, _fmt_bp(v), anchor="middle", size=small)
        v += step


def _nice_step(span: float, target: int) -> float:
    raw = span / max(target, 1)
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = raw / 10 ** exp
    nice = 1 if base < 1.5 else 2 if base < 3.5 else 5 if base < 7.5 else 10
    return float(nice * 10 ** exp)


def _fmt_bp(v: float) -> str:
    v = int(round(v))
    if v == 0:
        return "0"
    if v >= 1_000_000:
        return f"{v // 1_000_000} Mb" if v % 1_000_000 == 0 else f"{v / 1_000_000:.1f} Mb"
    if v >= 1_000:
        return f"{v // 1_000} kb" if v % 1_000 == 0 else f"{v / 1_000:.0f} kb"
    return str(v)
