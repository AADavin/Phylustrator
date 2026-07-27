"""The colouring layer — paint the branches by a per-node value.

``color_branches`` dispatches on the data: **numbers** get a colormap and a gradient down each branch
(and record a continuous scale, so ``colorbar()`` can draw itself); **labels** get a categorical
palette and solid branches (recording a palette, so ``legend()`` can). Values are keyed by node name
(or by node), and nodes with no value keep the default branch colour. Works on any layout, because it
draws through :func:`phylustrator.skeleton.draw_branches`.
"""

from __future__ import annotations

from ..color import map_values
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
