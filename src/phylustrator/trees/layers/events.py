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

**One event may carry its own style.** ``weight`` (0-1) is the one to reach for when a mark stands
for a count: it scales the arrow's width, the glyph's size and the opacity of both, between a floor
and the kind's full style, so hundreds of transfers summed over gene families read as a few strong
arcs and many faint ones. Divide by the largest count to get it: ``weight = n / n_max``. ``color``
and ``size`` override the kind's colour and the layer's size for that one event. An event with none
of them is drawn exactly as before, and the legend always shows the kind's own colour.

**An event has to be able to happen.** A point marker outside its branch is pulled back onto it, and
a transfer whose time is outside the window where donor and recipient both exist is refused: it
would be drawn on a row where that lineage's branch has already ended, which reads as a transfer
that never happened. Both are the ``clamp`` argument, on by default; ``clamp=False`` places every
event exactly where it says.
"""

from __future__ import annotations

# kind -> (glyph, colour). glyph: square / cross (point markers) or arrow (donor -> recipient).
DEFAULT_EVENT_STYLES = {
    "duplication": ("square", "#3a7ca5"),
    "loss": ("cross", "#c1443c"),
    "transfer": ("arrow", "#2e8b57"),
    "origination": ("diamond", "#7b5ea7"),
}


#: What one event may say about its own drawing, on top of what its kind says.
_OVERRIDES = ("weight", "color", "size")


def _unpack(ev):
    """One event as a dict, keeping any per-event override it carries and dropping the rest."""
    if isinstance(ev, dict):
        kind = ev.get("kind")
        x = float(ev.get("x", ev.get("time")))
        out = {"kind": kind, "x": x}
        if "recipient" in ev or "donor" in ev:
            out.update({"donor": ev.get("donor"), "recipient": ev.get("recipient")})
        else:
            out["node"] = ev.get("node", ev.get("lineage"))
        out.update({k: ev[k] for k in _OVERRIDES if k in ev})
        return out
    node, x, kind = ev
    return {"kind": kind, "x": float(x), "node": node}


def _weight_scale(weight, floor: float) -> float:
    """An event's ``weight`` (0-1, clamped) as a multiplier between ``floor`` and 1.

    No weight is 1, so an unweighted figure is drawn exactly as it was. The floor is what keeps the
    lightest arc on the page: scaling straight to 0 would erase the pair seen twice, and the point of
    a weighted figure is that it is still there, thin, beside the pair seen three hundred times."""
    if weight is None:
        return 1.0
    return floor + (1.0 - floor) * min(max(float(weight), 0.0), 1.0)


def _impossible(ev, lo: float, hi: float) -> str:
    """Why this transfer cannot be drawn. It names the window rather than the offending time alone:
    a whole figure of times measured from the present, or without the root stem, misses it the same
    way, and the window is what says so."""
    pair = f"{ev.get('donor')} -> {ev.get('recipient')}"
    if lo > hi:
        return (f"branch_events: the transfer {pair} at {ev['x']:g} cannot be drawn — those two "
                f"lineages never exist at the same time")
    return (f"branch_events: the transfer {pair} at {ev['x']:g} is outside [{lo:g}, {hi:g}], the "
            f"window where donor and recipient both exist. Event times are distances from the root, "
            f"on the same scale as the tree's branch lengths; pass clamp=False to draw it anyway")


def branch_events(events, *, styles: dict | None = None, size: float = 5.5,
                  legend: bool = True, legend_title: str = "events",
                  legend_loc: str = "top-right", legend_size: float | None = None,
                  clamp: bool = True, weight_floor: float = 0.25):
    """Mark ``events`` on the tree. ``styles`` maps a kind to ``(glyph, colour)`` (merged over the
    D/T/L/O default). ``legend_loc`` is a corner; ``legend_size`` sets the legend font size (glyphs
    scale with it). ``clamp`` keeps a point marker within its branch's span.

    An event may carry its own ``weight`` (0-1), ``color`` and ``size`` — see the module docstring.
    ``weight_floor`` is how much of the kind's style a weight of 0 keeps, so the lightest mark is
    still visible.

    ``clamp`` also refuses a transfer whose time falls outside the window where the donor and the
    recipient both exist, naming that window. Drawing it would put the arrow on a row whose branch
    has already ended, and the usual cause is a time measured on another scale — from the present
    rather than the root, or without the root stem."""
    styles = {**DEFAULT_EVENT_STYLES, **(styles or {})}

    def layer(canvas, tree, layout, style):
        import math

        by_name = {n.name: n for n in tree.walk() if n.name}
        radial = layout.kind == "radial"
        # events carry distance on the stem-inclusive scale (the rectangular default); the radial
        # layout drops the stem (its radius starts at the crown), so shift by the stem's length
        stem_off = float(tree.root.length or 0.0) if radial else 0.0

        def rad(node):
            return math.hypot(layout.x(node), layout.y(node))

        def span(node):
            """The distance range over which this lineage's own branch is drawn."""
            here = rad(node) if radial else layout.x(node)
            if node.parent is None:                      # the root: its branch is the stem, if drawn
                return 0.0, here
            up = rad(node.parent) if radial else layout.x(node.parent)
            return min(up, here), max(up, here)

        # branch lengths come from a reconstruction, so let a time sit on a branch end
        tol = 1e-6 * max(layout.xlim[1] - layout.xlim[0], 1.0)

        def place(node, t):
            """An event at distance ``t`` on ``node``'s branch, in layout coordinates."""
            if not radial:
                return t, layout.y(node)
            a = layout.angle[node]                       # the distance is the radius
            return t * math.cos(a), t * math.sin(a)

        used: dict[str, tuple] = {}
        for raw in events:
            ev = _unpack(raw)
            glyph, kind_color = styles.get(ev["kind"], ("circle", "#8a8f94"))
            # the kind says how an event is drawn; the event itself may say more
            color = ev.get("color") or kind_color
            weight = _weight_scale(ev.get("weight"), weight_floor)
            marked = float(ev.get("size", size)) * weight
            if glyph == "arrow":                                    # transfer: donor -> recipient
                donor, recip = by_name.get(ev.get("donor")), by_name.get(ev.get("recipient"))
                if donor is None or recip is None:
                    continue
                x = ev["x"] - stem_off       # onto the layout's own distance scale
                if clamp:
                    lo = max(span(donor)[0], span(recip)[0])
                    hi = min(span(donor)[1], span(recip)[1])
                    if not lo - tol <= x <= hi + tol:
                        raise ValueError(_impossible(ev, lo + stem_off, hi + stem_off))
                # scale the arrow with `size` (as the point glyphs do) so the head reads as an arrow,
                # not a tick, on a large figure
                dx, dy = place(donor, x)
                rx, ry = place(recip, x)
                canvas.arrow(dx, dy, rx, ry, color,
                             width=max(1.8, float(ev.get("size", size)) * 0.42) * weight,
                             head=max(9.0, float(ev.get("size", size)) * 2.4) * weight,
                             opacity=weight)
            else:
                node = by_name.get(ev.get("node"))
                if node is None:
                    continue
                x = ev["x"] - stem_off        # onto the layout's own distance scale
                if clamp and node.parent is not None:
                    if radial:
                        lo, hi = sorted((rad(node.parent), rad(node)))
                    else:
                        lo, hi = sorted((layout.x(node.parent), layout.x(node)))
                    x = min(max(x, lo), hi)
                mx, my = place(node, x)
                if radial:
                    # the glyph's "forward" must follow the branch: rotate by the branch
                    # direction in PIXEL space (py may flip y, so measure it there)
                    ax, ay = place(node, max(x - 1e-6, 0.0))
                    px, py = canvas.px(mx), canvas.py(my)
                    ang = math.atan2(py - canvas.py(ay), px - canvas.px(ax))
                    if glyph == "triangle_right":
                        # tip AT the event's instant, body trailing over the state it leaves:
                        # centred, the glyph swallows a short old-state segment and reads as a
                        # switch inside its own destination colour
                        px -= marked * math.cos(ang)
                        py -= marked * math.sin(ang)
                    # an ink outline, not white: the tip sits against a branch of its own
                    # colour, and without a silhouette the flared base reads as the point
                    canvas.raw_marker(px, py, glyph, color, marked, angle=ang,
                                      stroke="#1a1a1a", stroke_width=1.1, opacity=weight)
                else:
                    canvas.marker(mx, my, glyph, color, marked, opacity=weight)
            # the key names the kind, so it shows the kind's colour — never one event's override
            used[ev["kind"]] = (glyph, kind_color)
        if legend and used:
            _draw_legend(canvas, style, used, legend_title, size, legend_loc, legend_size)

    return layer


def _draw_legend(canvas, style, used, title, marker, loc, fsize) -> None:
    width, height = canvas.size
    fs = fsize if fsize is not None else style.font_size
    ms = marker * (fs / style.font_size)                            # glyphs scale with the legend text
    row_h = fs * 1.7
    labels = ([title] if title else []) + list(used)
    box_w = ms * 2 + 14 + max(len(s) for s in labels) * fs * 0.62
    n_rows = len(used) + (1 if title else 0)
    x = (style.margin_at("left") + ms + 6) if "left" in loc else (width - style.margin_at("right") - box_w)
    y = (style.margin_at("top") * 0.6 + fs) if "top" in loc else (height - style.margin_at("bottom") - row_h * n_rows)
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
