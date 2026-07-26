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


def color_branches(values, *, cmap: str = "viridis", palette: dict | None = None, width=None):
    """Colour every branch by ``values`` (``{node name: value}``). Numeric → colormap gradient;
    categorical → palette. Returns a layer."""

    def layer(canvas, tree, layout, style):
        by_name, scale = map_values(values, cmap=cmap, palette=palette)
        if scale is None:
            return
        canvas.scale = scale
        default = style.branch_color

        def color(node):
            return by_name.get(node.name, default)

        draw_branches(canvas, tree, layout, color=color, width=width or style.branch_width,
                      gradient=(scale["kind"] == "continuous"))

    return layer
