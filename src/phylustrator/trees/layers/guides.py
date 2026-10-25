"""Guide layers — the chrome that explains the colours and the scale.

``colorbar`` and ``legend`` read the scale a colouring layer recorded on the canvas (so they need no
data of their own — just add them after ``color_branches``); ``time_axis`` reads the layout extent.
All three draw in pixel space at a fixed spot on the page.
"""

from __future__ import annotations

import math
import warnings

#: A key drawn inside the plotting area sits on top of the tree, and a branch running under the
#: letters makes both unreadable. Every key here paints this behind itself first: the page colour,
#: no border, so it reads as a gap in the tree rather than as a box someone added.
_KEY_BACKDROP = "#ffffff"


def _clear_behind(canvas, x, y, w, h, pad: float = 6.0) -> None:
    canvas.raw_rect(x - pad, y - pad, w + 2 * pad, h + 2 * pad,
                    fill=_KEY_BACKDROP, stroke="none", stroke_width=0.0)


#: The corners a pinned layer may sit in — the four ``branch_events`` has always taken.
_CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")

#: The places **outside** the panel: a column in the right margin, or a row under the tree. A
#: corner is inside the plotting area, so on a tree whose tips reach the right edge at every row
#: and whose root sits low there is no free corner at all, whatever the measuring says.
_OUTSIDE = ("right", "below")

#: A colorbar is a wide block with its labels running left to right from its start, so it is
#: anchored on the left margin. A right-hand corner was accepted and then drawn on the left.
_BAR_CORNERS = ("top-left", "bottom-left")


def _branch_points(canvas, tree, layout, steps: int = 12) -> list:
    """Points along every branch, in pixels, as each layout draws it — enough to tell whether a
    block of chrome would sit on top of one."""
    pts: list = []

    def walk(x0, y0, x1, y1, name):
        for i in range(steps + 1):
            t = i / steps
            pts.append((name, canvas.px(x0 + (x1 - x0) * t), canvas.py(y0 + (y1 - y0) * t)))

    for node in tree.walk():
        if node.parent is None:
            continue
        name = node.name or "?"
        if layout.kind == "rectangular":
            y, yp = layout.y(node), layout.y(node.parent)
            walk(layout.x(node.parent), y, layout.x(node), y, name)            # the branch itself
            walk(layout.x(node.parent), yp, layout.x(node.parent), y, name)    # and its drop
        elif layout.kind == "radial" and layout.angle is not None:
            a, ap = layout.angle[node], layout.angle[node.parent]
            r = math.hypot(layout.x(node.parent), layout.y(node.parent))
            walk(r * math.cos(a), r * math.sin(a), layout.x(node), layout.y(node), name)
            for i in range(steps + 1):                                         # the arc it steps off
                ang = ap + (a - ap) * i / steps
                pts.append((name, canvas.px(r * math.cos(ang)), canvas.py(r * math.sin(ang))))
        else:
            walk(layout.x(node.parent), layout.y(node.parent), layout.x(node), layout.y(node), name)
    return pts


def _covered(points, box) -> list:
    """The branches a block would hide: those with more than one sampled point inside it. One point
    is a corner clipping a line; two is a stretch of branch nobody can see."""
    x, y, w, h = box
    seen: dict = {}
    for name, px_, py_ in points:
        if x <= px_ <= x + w and y <= py_ <= y + h:
            seen[name] = seen.get(name, 0) + 1
    return sorted(name for name, n in seen.items() if n > 1)


def _covered_labels(canvas, box) -> int:
    """How many of the boxes another layer has drawn this block would sit on.

    The tip names, chiefly. A key measures the branches itself, from the tree, but it cannot know
    what text another layer wrote or how wide it came out — so the layer that wrote it says so, and
    this counts what overlaps. A key added before ``tip_labels`` sees nothing, because nothing has
    been written yet."""
    x, y, w, h = box
    return sum(1 for (a, b, c, d) in canvas.obstacles()
               if not (c < x or a > x + w or d < y or b > y + h))


def _warn_covered(canvas, tree, layout, who: str, corner: str, box, *, advice: str) -> list:
    """Warn if this block of chrome hides a branch or a tip name, naming the corner.

    A key paints the page colour behind itself so the letters stay readable, which means it can
    hide something instead: a clade whose branch is covered looks detached from the tree, and a
    covered name is simply gone."""
    hidden = _covered(_branch_points(canvas, tree, layout), box)
    labels = _covered_labels(canvas, box)
    if hidden or labels:
        parts = []
        if hidden:
            named = ", ".join(hidden[:4]) + (", …" if len(hidden) > 4 else "")
            parts.append(f"{len(hidden)} branch(es) ({named})")
        if labels:
            parts.append(f"{labels} tip label(s)")
        warnings.warn(f"{who}: the {corner} key covers {' and '.join(parts)}. {advice}",
                      stacklevel=2)
    return hidden


def _outside_box(canvas, style, loc: str, box_w: float, box_h: float, who: str) -> tuple:
    """The top-left pixel of a block placed outside the panel, past whatever the layers before it
    have written into that margin.

    The block claims the room it takes, so a note and a key both placed below stack instead of
    landing on each other, in the order the layers were added.

    It warns rather than silently running off the page: the canvas size is fixed before any layer
    runs, so a margin too thin to hold the key cannot be widened from here — only the caller can,
    and the warning says by how much."""
    w, h = canvas.size
    gap = 10.0
    if loc == "right":
        panel_edge = w - style.margin_at("right")
        x = canvas.claimed("right", panel_edge) + gap
        # centred on the plotting area, which is how a key beside a figure reads
        top, bottom = style.margin_at("top"), h - style.margin_at("bottom")
        y = (top + bottom) / 2 - box_h / 2
        if x + box_w > w:
            need = round(w - x + box_w - (w - panel_edge) + gap)
            warnings.warn(f"{who}: loc='right' needs about margin_right={need} to hold it; this "
                          f"figure has {round(style.margin_at('right'))}, so the block runs off the "
                          f"page. Widen the margin, or put it below.", stacklevel=3)
        canvas.claim("right", x + box_w)      # so a second block beside the figure clears this one
        return x, y
    panel_bottom = h - style.margin_at("bottom")
    y = canvas.claimed("bottom", panel_bottom) + gap
    x = (style.margin_at("left") + (w - style.margin_at("right"))) / 2 - box_w / 2
    if y + box_h > h:
        need = round(y + box_h - panel_bottom + gap)
        warnings.warn(f"{who}: loc='below' needs about margin_bottom={need} to hold it; this figure "
                      f"has {round(style.margin_at('bottom'))}, so the block runs off the page. "
                      f"Widen the margin, or put it to the right.", stacklevel=3)
    canvas.claim("bottom", y + box_h)         # a second block below stacks under this one
    return x, y


def _corner(loc: str, who: str) -> str:
    """Check a corner name at the point it is written. ``"top-centre"`` used to fall through the
    ``"left" in loc`` test and print as though it had been asked for on the right, which is worse
    than an error."""
    allowed = (_CORNERS + ("auto",) + _OUTSIDE if who == "legend" else
               _BAR_CORNERS if who == "colorbar" else
               _CORNERS + _OUTSIDE if who == "note" else _CORNERS)
    if loc not in allowed:
        centred = " (a centred title is `title()`)" if "cent" in loc.lower() else ""
        raise ValueError(f"{who}: loc must be one of {', '.join(allowed)}, not {loc!r}{centred}")
    return loc


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
    themselves. Pass the strings you want instead.

    Like ``legend``, the bar paints the page colour behind itself, so a branch running through its
    corner is hidden rather than scribbled over: it warns and names the branches when that happens.
    Only the two left corners are accepted, since the bar is anchored on the left margin whatever it
    is given."""
    _corner(loc, "colorbar")

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
        pad = 6.0
        other = "bottom-left" if "top" in loc else "top-left"
        _warn_covered(canvas, tree, layout, "colorbar", loc,
                      (x - pad, top - pad, wide + 2 * pad, (bottom - top) + 2 * pad),
                      advice=f"Move it to {other}.")
        _clear_behind(canvas, x, top, wide, bottom - top)
        if title:
            canvas.raw_text(x, title_y, title, anchor="start", weight="bold", size=fs)
        canvas.gradient_bar(scale["cmap"], x, y, width, height)
        canvas.raw_text(x, y + height + fs * 0.9, lo, anchor="start", size=fs * 0.9)
        canvas.raw_text(x + width, y + height + fs * 0.9, hi, anchor="end", size=fs * 0.9)

    return layer


def legend(title: str = "", *, loc: str = "top-left", swatch: float | None = None,
           size: float | None = None, entries: dict | None = None, dy: float = 0.0,
           inset: float | None = None):
    """A category swatch list pinned to a corner — ``"top-left"`` by default, or any of the four
    ``branch_events`` takes. A rectangular tree fills the upper left of its panel, so the top left
    is often the one corner a legend cannot share; a right corner right-aligns the block on the
    right margin, and a bottom corner ends it on the bottom margin.

    The key paints the page colour behind itself, so that a branch running under the letters does not
    make both unreadable — which means it can hide a branch or a tip name instead. ``loc="auto"``
    measures all four corners and takes the one covering the least — branches **and** the names
    written beside the tips, which a layer added before it has recorded — and any corner that still
    covers something warns and says what. A clade whose branch is covered looks detached from the
    tree; a covered name is simply gone.

    ``loc="right"`` or ``loc="below"`` puts the key **outside** the panel instead — a column in
    the right margin, past the tip labels, or a row under the tree, below the time axis. Which
    corner is free depends on the tree, and on one whose tips reach the right edge at every row and
    whose root sits low there is no free corner at all; outside, nothing is covered whatever the
    tree's shape. The margin has to be wide enough, and the warning says by how much when it is not.

    ``size`` sets the label font (default the style's) and the swatch scales with it. Reads the
    recorded categorical scale, or ``entries`` (``{label: colour}``) to draw an explicit list — a
    figure whose scale slot is taken by a continuous ring still gets its categorical legend that
    way. ``dy`` shifts the list down, so it can sit below a ``colorbar`` in the same corner. No-op
    without a source of entries."""
    _corner(loc, "legend")

    def layer(canvas, tree, layout, style):
        palette = entries
        if palette is None:
            scale = canvas.scale
            if not scale or scale.get("kind") != "categorical":
                return
            palette = scale["palette"]
        w, h = canvas.size
        fs = size if size is not None else style.font_size
        sw = swatch if swatch is not None else fs * 0.95
        rows = len(palette) + (1 if title else 0)
        widest = max([_text_width(str(k), fs) for k in palette] +
                     [_text_width(title, fs) if title else 0.0])
        box_w = sw + 8 + widest

        def side(name):
            return inset if inset is not None else style.margin_at(name)

        # the drop from the first row's baseline to the last one's; a title row is the taller one
        drop = (fs * 1.7 if title else 0.0) + max(len(palette) - 1, 0) * fs * 1.6
        tall = rows * fs * 1.65

        def place(where):
            px_ = side("left") if "left" in where else w - side("right") - box_w
            py_ = (side("top") if "top" in where else h - side("bottom") - drop - fs * 0.5) + dy
            return px_, py_

        def patch(where):          # what the backdrop will cover, padding included
            px_, py_ = place(where)
            return (px_ - 6, py_ - fs - 6, box_w + 12, tall + 12)

        if loc in _OUTSIDE:
            # outside the panel there is nothing to cover, so there is nothing to measure either
            x, y = _outside_box(canvas, style, loc, box_w, tall, "legend")
            y += fs + dy
        else:
            ink = _branch_points(canvas, tree, layout)

            def cost(where):
                """What a corner would cover: branches and tip names alike. Measuring the branches
                alone put the key on the names of the long tips, with nothing said (#36)."""
                box = patch(where)
                return len(_covered(ink, box)) + _covered_labels(canvas, box)

            corner = (min(_CORNERS, key=lambda c: (cost(c), _CORNERS.index(c)))
                      if loc == "auto" else loc)
            _warn_covered(canvas, tree, layout, "legend", corner, patch(corner),
                          advice=("Move it, pass loc='auto', or put it outside the panel with "
                                  "loc='right' or loc='below'"
                                  f"{' (every corner covers something)' if loc == 'auto' else ''}."))
            x, y = place(corner)
            _clear_behind(canvas, x, y - fs, box_w, tall)
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
    ``"bottom-right"``), or outside the panel with ``"right"`` / ``"below"`` — e.g. to name the
    model or clock a figure was drawn under.

    ``dy`` nudges it in pixels, negative up. The corner is fixed to the margin, which is the right
    place for a note *about* the figure; a note read as a **title** wants a little more air between
    it and the tree than a margin the tree also uses can give, so a centred title is :func:`title`."""
    _corner(loc, "note")

    def layer(canvas, tree, layout, style):
        w, h = canvas.size
        fs = size if size is not None else style.font_size
        if loc in _OUTSIDE:
            x, y = _outside_box(canvas, style, loc, _text_width(text, fs), fs, "note")
            canvas.raw_text(x, y + fs * 0.5 + dy, text, anchor="start", size=fs,
                            color=color or style.label_color, weight=weight)
            return
        x = style.margin_at("left") if "left" in loc else w - style.margin_at("right")
        y = (style.margin_at("top") * 0.6 + fs) if "top" in loc else (h - style.margin_at("bottom") * 0.5)
        y += dy
        anchor = "start" if "left" in loc else "end"
        canvas.raw_text(x, y, text, anchor=anchor, size=fs,
                        color=color or style.label_color, weight=weight)

    return layer


def title(text: str, *, size: float | None = None, dy: float = 0.0, color: str | None = None,
          weight: str = "bold"):
    """A title centred over the panel, in the top margin above the tree.

    ``note`` pins text to a corner, which is where something *about* a figure belongs; a title
    belongs over the middle of it. ``size`` defaults to half again the style's font, ``dy`` nudges
    it in pixels (negative up), and the title stays on the page even on a thin top margin. Give the
    figure a larger ``margin_top`` when the title sits too close to the tree."""

    def layer(canvas, tree, layout, style):
        w, _ = canvas.size
        fs = size if size is not None else style.font_size * 1.4
        # halfway up the top margin, but never so high that the page edge cuts it
        y = max(style.margin_at("top") * 0.5, fs * 0.75) + dy
        canvas.raw_text(w / 2, y, text, anchor="middle", size=fs,
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


def _stepped(span: float, step: float) -> list[float]:
    """Ticks every ``step`` from 0, up to ``span``."""
    if step <= 0:
        raise ValueError(f"step must be positive, not {step!r}")
    out, k = [], 0
    while k * step <= span + step * 1e-9:
        out.append(round(k * step, 10))
        k += 1
    return out


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


def time_axis(label: str = "Time", *, ticks: int = 5, step: float | None = None,
              at=None, labels=None, before_present: bool = False, tick_size: float | None = None,
              label_size: float | None = None, bold: bool | None = None):
    """A horizontal scale along the bottom, in the layout's distance units (0 at the origin).
    Rectangular only (distance maps to x); use ``scale_bar`` for radial/unrooted. ``tick_size`` /
    ``label_size`` set the tick-number and axis-label font sizes (default: the style's font size);
    the vertical spacing follows the font, so give the figure enough bottom margin for big text.
    ``bold`` sets the label weight (default: bold only when a ``label_size`` is given).

    ``before_present`` counts the other way, which is how a dated tree is read: 0 under the tips and
    the root at its age. The ticks are then anchored at the tips, so they land on round ages rather
    than on round distances from the root. ``step`` fixes the interval between ticks instead of
    choosing about ``ticks`` round ones.

    ``at`` places the ticks itself: a list of distances, or ``"nodes"`` for one under every internal
    node. ``labels`` is what each one says, one per tick — with ``at="nodes"`` they are numbered from
    the oldest node by default, so the axis reads as the order of the nodes rather than as a
    distance. ``at`` and ``step`` are two ways to place the same ticks, so giving both raises."""
    if at is not None and step is not None:
        raise ValueError("give at= or step=, not both: they are two ways to place the same ticks")
    if labels is not None and at is None:
        raise ValueError("labels= needs at=, so that each label has a tick of its own")

    def layer(canvas, tree, layout, style):
        if layout.kind == "diagonal" and not layout.grows_along_x:
            warnings.warn(f"time_axis: a {layout.orientation} tree carries its time down the page, "
                          f"and the axis is drawn along the bottom. Nothing was drawn. Use "
                          f"orientation='right' or 'left' for a tree with a time axis.", stacklevel=2)
            return
        if layout.kind not in ("rectangular", "diagonal"):
            return
        _, height = canvas.size
        ts = tick_size if tick_size is not None else style.font_size * 0.85
        ls = label_size if label_size is not None else style.font_size
        is_bold = (label_size is not None) if bold is None else bold
        y = height - style.margin_at("bottom") + 14  # just below the tree area, inside the bottom margin
        places, texts = at, labels
        if at == "nodes":
            places = sorted({round(layout.x(n), 10) for n in tree.walk() if not n.is_leaf})
            texts = labels if labels is not None else [str(i + 1) for i in range(len(places))]
        # the axis, its numbers and its own label all sit in the bottom margin
        canvas.claim("bottom", y + ls * (2.4 if label else 1.4))
        draw_time_axis(canvas, canvas.px, layout.xlim[1], y, label, ticks=ticks, step=step,
                       at=places, labels=texts, before_present=before_present, tick_size=ts,
                       label_size=ls, weight="bold" if is_bold else "normal")

    return layer


def draw_time_axis(canvas, px, x_end: float, y: float, label: str | None, *, ticks: int = 5,
                   step: float | None = None, at=None, labels=None, before_present: bool = False,
                   tick_size: float, label_size: float, weight: str = "normal") -> None:
    """Draw a time axis from 0 to ``x_end`` at pixel height ``y``, with ``px`` mapping a time to a
    pixel x. Shared by :func:`time_axis` and :func:`~phylustrator.compose.below`, so an axis under a
    panel is the same axis a tree draws under itself. ``before_present`` counts back from ``x_end``,
    ``step`` fixes the tick interval, and ``at`` (with optional ``labels``) places the ticks
    outright."""
    canvas.raw_line(px(0.0), y, px(x_end), y, "#333333", 1.2)
    if at is None:
        # ticks at round numbers (a 1 / 2 / 2.5 / 5 step), not at even fractions of the
        # height: dividing a height of 3.96 into quarters gave "0, 0.99, 2, 3, 4",
        # where the "2" was really 1.98 — ugly and, worse, slightly wrong
        values = _round_ticks(x_end, ticks) if step is None else _stepped(x_end, step)
        # the number written, and where it goes: counting back, a round age sits where that age is
        places = [x_end - v if before_present else v for v in values]
        texts = [f"{v:g}" for v in values]
    else:
        places = [float(p) for p in at]
        texts = ([str(t) for t in labels] if labels is not None
                 else [f"{(x_end - p) if before_present else p:g}" for p in places])
        if len(texts) != len(places):
            raise ValueError(f"at= has {len(places)} ticks but labels= has {len(texts)}")
    for place, text in zip(places, texts):
        tx = px(place)
        canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
        canvas.raw_text(tx, y + tick_size + 3, text, anchor="middle", size=tick_size)
    if label:
        mid = (px(0.0) + px(x_end)) / 2
        canvas.raw_text(mid, y + tick_size + label_size + 4, label, anchor="middle", size=label_size,
                        weight=weight)
