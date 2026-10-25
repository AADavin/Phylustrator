"""The node-dots layer — a small mark sitting on a node itself.

The dot a textbook diagram puts on every tip and at the root, so that a branch ends in a point
rather than trailing off, and so that the one node the figure is about can be starred. It carries no
data: :func:`~phylustrator.trees.node_points` draws a value per node, ``node_halves`` draws two, and
this one says only "here is a node".
"""

from __future__ import annotations

#: Which nodes a dot goes on, when they are not named one by one.
WHERE = ("tips", "internal", "root", "all")


def node_dots(nodes=None, *, where: str = "tips", size: float = 2.6, color: str | None = None,
              shape: str = "circle", stroke: str = "none", stroke_width: float = 0.0):
    """Mark nodes with a dot. ``where`` picks them as a group — ``"tips"`` (the default),
    ``"internal"``, ``"root"`` or ``"all"`` — and ``nodes``, a list of names, picks them one by one
    instead, for the single starred node a diagram is about:

        plot(tree, layout="diagonal", orientation="down") + node_dots() + node_dots(["r"])
        ... + node_dots(["ab"], shape="star", size=5)

    ``size`` is the dot's radius in pixels and ``shape`` is any glyph
    :meth:`~phylustrator.render.Canvas.raw_marker` draws, so ``"star"`` or ``"square"`` marks one
    node out of the rest. ``color`` defaults to the style's branch colour, since the dot is the end
    of the branch rather than something laid on top of it. Returns a layer."""
    if where not in WHERE:
        raise ValueError(f"where must be one of {', '.join(WHERE)}, not {where!r}")
    wanted = None if nodes is None else {str(n) for n in nodes}

    def layer(canvas, tree, layout, style):
        if wanted is not None:
            missing = wanted - {n.name for n in tree.walk() if n.name}
            if missing:
                shown = ", ".join(sorted(missing)[:5]) + (", …" if len(missing) > 5 else "")
                raise ValueError(f"node_dots: {len(missing)} name(s) not in the tree: {shown}")
        for node in tree.walk():
            if wanted is not None:
                if node.name not in wanted:
                    continue
            elif not ((where == "all")
                      or (where == "tips" and node.is_leaf)
                      or (where == "root" and node.is_root)
                      or (where == "internal" and not node.is_leaf)):
                continue
            canvas.raw_marker(canvas.px(layout.x(node)), canvas.py(layout.y(node)), shape,
                              color or style.branch_color, size,
                              stroke=stroke, stroke_width=stroke_width)

    return layer
