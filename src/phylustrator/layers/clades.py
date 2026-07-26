"""Clade layers — shade or bracket a subtree.

Shading sits *behind* the branches, so add ``highlight_clade`` **before** the colouring layer:
``plot(tree) + highlight_clade("n5") + color_branches(...)``.
"""

from __future__ import annotations


def _subtree(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(n.children)


def highlight_clade(clade: str, *, color: str = "#FDBF6F", opacity: float = 0.35, pad: float = 0.4):
    """Shade the box behind the clade rooted at the node named ``clade`` (rectangular layout).
    Returns a layer."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            return
        node = tree.find(clade)
        if node is None:
            return
        leaves = [n for n in _subtree(node) if n.is_leaf]
        if not leaves:
            return
        ys = [layout.y(leaf) for leaf in leaves]
        x0, x1 = layout.x(node), max(layout.x(leaf) for leaf in leaves)
        canvas.region(x0, min(ys) - pad, x1, max(ys) + pad, fill=color, opacity=opacity)

    return layer
