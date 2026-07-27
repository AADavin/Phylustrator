"""The colouring layer — paint the branches by a per-node value.

``color_branches`` dispatches on the data: **numbers** get a colormap and a gradient down each branch
(and record a continuous scale, so ``colorbar()`` can draw itself); **labels** get a categorical
palette and solid branches (recording a palette, so ``legend()`` can). Values are keyed by node name
(or by node), and nodes with no value keep the default branch colour. Works on any layout, because it
draws through :func:`phylustrator.skeleton.draw_branches`.
"""

from __future__ import annotations

from ...color import map_values
from ..skeleton import draw_branches


def color_branches(values, *, cmap: str = "viridis", palette: dict | None = None, width=None,
                   dashed=None):
    """Colour every branch by ``values`` (``{node name: value}``). Numeric → colormap gradient;
    categorical → palette. ``dashed`` is an optional set of node names to draw dashed (e.g. extinct
    lineages), since the colour overdraws the base skeleton. Returns a layer."""

    def layer(canvas, tree, layout, style):
        by_name, scale = map_values(values, cmap=cmap, palette=palette)
        if scale is None:
            return
        canvas.scale = scale
        default = style.branch_color

        def color(node):
            return by_name.get(node.name, default)

        draw_branches(canvas, tree, layout, color=color, width=width or style.branch_width,
                      gradient=(scale["kind"] == "continuous"), dashed=dashed)

    return layer


def color_history(history, *, palette: dict, width=None, default: str | None = None, dashed=None):
    """Paint each branch as coloured **segments** from its per-lineage state history — a list of
    ``(state, duration)`` running from the branch's start to its end. Use this (not
    :func:`color_branches`) for a discrete trait whose state changes *along* a branch: the branch is a
    mosaic, not one colour. ``dashed`` is an optional set of node names to draw dashed (e.g. extinct
    lineages). Rectangular layout only; records the palette so ``legend`` can draw.
    ``history``: ``{node name: [(state, dur), …]}``."""
    dashed = dashed or set()

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            raise ValueError("color_history needs the rectangular layout (segments run along x)")
        w = width or style.branch_width
        canvas.scale = {"kind": "categorical", "palette": dict(palette)}
        base = default or style.branch_color
        for node in tree.walk():
            y = layout.y(node)
            x_end = layout.x(node)
            x_start = (x_end - layout.root_branch) if node.is_root else layout.x(node.parent)
            d = node.name in dashed
            segs = history.get(node.name)
            end_state = None
            if segs:
                total = sum(dur for _, dur in segs) or 1.0
                span = x_end - x_start
                xx = x_start
                for state, dur in segs:
                    x1 = xx + span * dur / total
                    canvas.line(xx, y, x1, y, palette.get(state, base), w, dash=d)
                    xx = x1
                end_state = segs[-1][0]
            else:
                canvas.line(x_start, y, x_end, y, base, w, dash=d)
            if not node.is_leaf:                              # connectors in the node's end state
                cc = palette.get(end_state, base)
                for c in node.children:
                    canvas.line(x_end, y, x_end, layout.y(c), cc, w, dash=(c.name in dashed))

    return layer


def color_lanes(lanes, *, width=None, gap: float = 1.0, connectors: bool = True,
                joint: str | None = None, default: str | None = None, dashed=None):
    """Paint each branch as several **parallel lanes** — one per trait — so more than one discrete
    trait shows side by side *on the same branch*, each branch a stacked two-tone (or n-tone) band.
    Each lane is a segmented colour history exactly like :func:`color_history` (``{node name:
    [(state, dur), …]}`` + its own palette), offset across the branch; lane 0 sits on one side, lane 1
    the other. ``gap`` is the lane spacing in units of the lane width (``1`` = touching, a solid band).

    Topology: by default the lanes carry their own speciation joints, but the cleanest result is to draw
    the plain grey skeleton for structure (``plot(tree)`` with ``skeleton=True``) and pass
    ``connectors=False`` here, so the lanes only paint the horizontal branches and the skeleton shows
    the tree. Rectangular layout only. ``lanes``: a list of ``(history, palette)`` pairs."""
    dashed = dashed or set()

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            raise ValueError("color_lanes needs the rectangular layout (segments run along x)")
        w = width or style.branch_width
        n = len(lanes)
        # lane widths/offsets are in pixels; y is data-space — convert via the canvas y-scale so the
        # lanes sit a few pixels apart (a solid band), not whole tree rows apart.
        ppu = (canvas.py(1.0) - canvas.py(0.0)) or 1.0              # pixels per unit y
        offs = [(i - (n - 1) / 2.0) * w * gap / ppu for i in range(n)]   # -> data units
        base = default or style.branch_color
        for node in tree.walk():
            y = layout.y(node)
            x_end = layout.x(node)
            x_start = (x_end - layout.root_branch) if node.is_root else layout.x(node.parent)
            d = node.name in dashed
            if connectors and not node.is_leaf:      # own joints, in the neutral joint colour
                jc = joint or style.branch_color
                for c in node.children:
                    canvas.line(x_end, y, x_end, layout.y(c), jc, w, dash=(c.name in dashed))
            for (history, palette), off in zip(lanes, offs):
                yy = y + off
                segs = history.get(node.name)
                if segs:
                    total = sum(dur for _, dur in segs) or 1.0
                    span = x_end - x_start
                    xx = x_start
                    for state, dur in segs:
                        x1 = xx + span * dur / total
                        canvas.line(xx, yy, x1, yy, palette.get(state, base), w, dash=d)
                        xx = x1
                else:
                    canvas.line(x_start, yy, x_end, yy, base, w, dash=d)

    return layer
