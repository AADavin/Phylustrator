"""The branch-events layer — mark gene-family events on the species tree.

Point events sit on a branch as a glyph; a **transfer** is drawn as an arrow from the donor lineage
to the recipient lineage at the transfer time. Event shapes:

- ``duplication`` — a square
- ``loss`` — a cross (✕)
- ``transfer`` — an arrow (donor → recipient)

Each event is a dict: ``{"kind": "duplication"|"loss", "node": name, "x": time}`` or
``{"kind": "transfer", "donor": name, "recipient": name, "x": time}``. A plain ``(node, x, kind)``
tuple still works for point events. The x-axis is the layout's distance axis (absolute time under the
stem-aware rectangular layout), so pass event times straight through.
"""

from __future__ import annotations

# kind -> (glyph, colour). glyph: square / cross (point markers) or arrow (donor -> recipient).
DEFAULT_EVENT_STYLES = {
    "duplication": ("square", "#3a7ca5"),
    "loss": ("cross", "#c1443c"),
    "transfer": ("arrow", "#2e8b57"),
    "origination": ("diamond", "#7b5ea7"),
}


def _unpack(ev):
    if isinstance(ev, dict):
        kind = ev.get("kind")
        x = float(ev.get("x", ev.get("time")))
        if "recipient" in ev or "donor" in ev:
            return {"kind": kind, "x": x, "donor": ev.get("donor"), "recipient": ev.get("recipient")}
        return {"kind": kind, "x": x, "node": ev.get("node", ev.get("lineage"))}
    node, x, kind = ev
    return {"kind": kind, "x": float(x), "node": node}


def branch_events(events, *, styles: dict | None = None, size: float = 5.5,
                  legend: bool = True, legend_title: str = "events",
                  legend_loc: str = "top-right", legend_size: float | None = None,
                  clamp: bool = True):
    """Mark ``events`` on the tree. ``styles`` maps a kind to ``(glyph, colour)`` (merged over the
    D/T/L/O default). ``legend_loc`` is a corner; ``legend_size`` sets the legend font size (glyphs
    scale with it). ``clamp`` keeps a point marker within its branch's span."""
    styles = {**DEFAULT_EVENT_STYLES, **(styles or {})}

    def layer(canvas, tree, layout, style):
        by_name = {n.name: n for n in tree.walk() if n.name}
        used: dict[str, tuple] = {}
        for raw in events:
            ev = _unpack(raw)
            glyph, color = styles.get(ev["kind"], ("circle", "#8a8f94"))
            if glyph == "arrow":                                    # transfer: donor -> recipient
                donor, recip = by_name.get(ev.get("donor")), by_name.get(ev.get("recipient"))
                if donor is None or recip is None:
                    continue
                # scale the arrow with `size` (as the point glyphs do) so the head reads as an arrow,
                # not a tick, on a large figure
                canvas.arrow(ev["x"], layout.y(donor), ev["x"], layout.y(recip), color,
                             width=max(1.8, size * 0.42), head=max(9.0, size * 2.4))
            else:
                node = by_name.get(ev.get("node"))
                if node is None:
                    continue
                x = ev["x"]
                if clamp and node.parent is not None:
                    lo, hi = sorted((layout.x(node.parent), layout.x(node)))
                    x = min(max(x, lo), hi)
                canvas.marker(x, layout.y(node), glyph, color, size)
            used[ev["kind"]] = (glyph, color)
        if legend and used:
            _draw_legend(canvas, style, used, legend_title, size, legend_loc, legend_size)

    return layer


def _draw_legend(canvas, style, used, title, marker, loc, fsize) -> None:
    width, height = canvas.size
    m = style.margin
    fs = fsize if fsize is not None else style.font_size
    ms = marker * (fs / style.font_size)                            # glyphs scale with the legend text
    row_h = fs * 1.7
    labels = ([title] if title else []) + list(used)
    box_w = ms * 2 + 14 + max(len(s) for s in labels) * fs * 0.62
    n_rows = len(used) + (1 if title else 0)
    x = (m + ms + 6) if "left" in loc else (width - m - box_w)
    y = (m * 0.6 + fs) if "top" in loc else (height - m - row_h * n_rows)
    if title:
        canvas.raw_text(x, y, title, anchor="start", weight="bold", size=fs)
        y += fs * 1.8
    for kind, (glyph, color) in used.items():
        if glyph == "arrow":
            canvas.raw_line(x - ms, y, x + ms, y, color, 2.0)
            canvas.raw_line(x + ms, y, x + ms - ms * 0.7, y - ms * 0.6, color, 2.0)
            canvas.raw_line(x + ms, y, x + ms - ms * 0.7, y + ms * 0.6, color, 2.0)
        else:
            canvas.raw_marker(x, y, glyph, color, ms, stroke="#ffffff", stroke_width=0.8)
        canvas.raw_text(x + ms + 12, y, kind, anchor="start", size=fs)
        y += row_h