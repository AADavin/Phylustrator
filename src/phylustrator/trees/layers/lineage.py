"""The lineage layer — draw one root-to-tip path thicker than the rest of the tree.

A tree coloured by a state, with one lineage drawn thick so a reader can follow it from the root to
its tip. Every other branch is left exactly as it was drawn, so this composes with a colouring layer
rather than replacing it.
"""

from __future__ import annotations

from ..skeleton import draw_branches
from ..tree import lineage
from .coloring import _dashed_or_figure


def highlight_lineage(node: str, *, width: float | None = None, factor: float = 2.6,
                      color: str | None = None, dashed=None):
    """Draw the branches from the root down to ``node`` thicker, and in ``color`` if one is given.

    Order decides what it looks like. **After** a colouring layer it paints the lineage over the
    top, so give it a colour. **Before** one, the thick line shows as an outline around the thinner
    coloured branches, which keeps the colours of the lineage readable.

    ``width`` is in pixels; by default it is ``factor`` times the style's branch width. The drop at
    a node is drawn only into the child that carries on down the lineage, so the bar is not
    thickened towards a child the lineage never enters. Raises if the tree has no such node."""

    def layer(canvas, tree, layout, style):
        names = set(lineage(tree, node))
        w = float(width) if width is not None else style.branch_width * factor
        paint = color or style.branch_color
        draw_branches(canvas, tree, layout, color=lambda n: paint, width=lambda n: w,
                      dashed=_dashed_or_figure(dashed, canvas),
                      include=lambda n: n.name in names)

    return layer
