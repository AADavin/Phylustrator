"""The branch-events layer — mark point events along the branches.

An *event* is ``(node_name, x, kind)``: a marker of a given ``kind`` placed at distance ``x`` on the
branch of the named node — for example a gene family's duplications, transfers, losses and
originations drawn on the species tree. The layer is general (any kinds, any styling); the default
palette is ZOMBI2's D/T/L/O vocabulary.

The x-axis is the layout's distance axis, so with the default **stem-aware** rectangular layout ``x``
is absolute time from the origin — pass event times straight through.
"""

from __future__ import annotations

# kind -> (marker shape, colour). Shapes: circle / square / triangle / diamond.
DEFAULT_EVENT_STYLES = {
    "duplication": ("circle", "#3a7ca5"),
    "transfer": ("triangle", "#2e8b57"),
    "loss": ("square", "#c1443c"),
    "origination": ("diamond", "#7b5ea7"),
}


def _unpack(ev):
    if isinstance(ev, dict):
        node = ev.get("node", ev.get("lineage"))
        x = ev.get("x", ev.get("time"))
        return node, float(x), ev.get("kind")
    node, x, kind = ev
    return node, float(x), kind


def branch_events(events, *, styles: dict | None = None, size: float = 5.5,
                  legend: bool = True, legend_title: str = "Events", clamp: bool = True):
    """Mark ``events`` on the branches. Each event is ``(node_name, x, kind)`` or a dict with
    ``node``/``lineage``, ``x``/``time``, ``kind``. ``styles`` maps a kind to ``(shape, colour)``
    (merged over the D/T/L/O default); ``clamp`` keeps a marker within its branch's span."""
    styles = {**DEFAULT_EVENT_STYLES, **(styles or {})}

    def layer(canvas, tree, layout, style):
        by_name = {n.name: n for n in tree.walk() if n.name}
        used: dict[str, tuple] = {}
        for ev in events:
            name, x, kind = _unpack(ev)
            node = by_name.get(name)
            if node is None:
                continue
            shape, color = styles.get(kind, ("circle", "#8a8f94"))
            if clamp and node.parent is not None:
                lo, hi = sorted((layout.x(node.parent), layout.x(node)))
                x = min(max(x, lo), hi)
            canvas.marker(x, layout.y(node), shape, color, size)
            used[kind] = (shape, color)
        if legend and used:
            _draw_legend(canvas, style, used, legend_title, size)

    return layer


def _draw_legend(canvas, style, used, title, size) -> None:
    width, _ = canvas.size
    x = width - style.margin - 118
    y = style.margin * 0.7
    if title:
        canvas.raw_text(x - size, y, title, anchor="start", weight="bold", size=style.font_size)
        y += style.font_size * 1.6
    for kind, (shape, color) in used.items():
        canvas.raw_marker(x, y, shape, color, size, stroke="#ffffff", stroke_width=0.8)
        canvas.raw_text(x + size + 8, y, kind, anchor="start", size=style.font_size * 0.9)
        y += style.font_size * 1.5
