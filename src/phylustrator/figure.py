"""The figure — compose a tree plot from layers, then render.

``plot(tree)`` returns a :class:`Figure`; decorations are added with ``+`` (the composable grammar);
``.save(path)`` lays the tree out, draws the branch skeleton, runs each layer, and writes the file.

    >>> fig = plot(tree) + color_branches(values) + tip_labels()   # doctest: +SKIP
    >>> fig.save("tree.pdf")                                        # doctest: +SKIP

A **layer** is just a callable ``(canvas, tree, layout, style) -> None``; that is the whole extension
contract, so new decorations never touch the figure.
"""

from __future__ import annotations

from typing import Callable

from .layout import Layout, radial, rectangular, unrooted
from .render import Canvas
from .skeleton import draw_branches
from .style import Style
from .tree import Tree

Layer = Callable[[Canvas, Tree, Layout, Style], None]

_LAYOUTS = {"rectangular": rectangular, "radial": radial, "unrooted": unrooted}


class Figure:
    """A tree plus a layout, a style, and an ordered list of layers. Immutable-ish: ``+`` returns a
    new figure with one more layer, so a base figure can be reused."""

    def __init__(self, tree: Tree, *, layout: str = "rectangular", stem: bool = True,
                 style: Style | None = None, dashed=None, layers: tuple[Layer, ...] = ()) -> None:
        if layout not in _LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {sorted(_LAYOUTS)}")
        self.tree = tree
        self.layout = layout
        self.stem = stem
        self.style = style or Style()
        self.dashed = dashed  # node names whose branch is drawn dashed (e.g. extinct lineages)
        self.layers = tuple(layers)

    def __add__(self, layer: Layer) -> "Figure":
        return Figure(self.tree, layout=self.layout, stem=self.stem, style=self.style,
                      dashed=self.dashed, layers=self.layers + (layer,))

    def _build(self) -> Canvas:
        layout = _LAYOUTS[self.layout](self.tree, stem=self.stem)
        canvas = Canvas(self.style, layout.xlim, layout.ylim,
                        equal_aspect=(layout.kind != "rectangular"))
        _draw_skeleton(canvas, self.tree, layout, self.style, self.dashed)
        for layer in self.layers:
            layer(canvas, self.tree, layout, self.style)
        return canvas

    def as_svg(self) -> str:
        return self._build().as_svg()

    def save(self, path):
        """Render and write to ``path`` (format from its extension: ``.svg`` / ``.pdf`` / ``.png``)."""
        return self._build().save(path)


def plot(tree: Tree, *, layout: str = "rectangular", stem: bool = True,
         style: Style | None = None, dashed=None) -> Figure:
    """Start a figure for ``tree``. Add layers with ``+``, then :meth:`Figure.save`. ``dashed`` is an
    optional set of node names whose branches are drawn dashed (e.g. extinct lineages)."""
    return Figure(tree, layout=layout, stem=stem, style=style, dashed=dashed)


def _draw_skeleton(canvas: Canvas, tree: Tree, layout: Layout, style: Style, dashed=None) -> None:
    """The always-present base layer: the branches in the default colour, drawn for whichever layout
    is in force (a colouring layer later overdraws them)."""
    draw_branches(canvas, tree, layout, color=lambda node: style.branch_color,
                  width=style.branch_width, gradient=False, dashed=dashed)
