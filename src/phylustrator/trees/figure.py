"""The figure — compose a tree plot from layers, then render.

``plot(tree)`` returns a :class:`Figure`; decorations are added with ``+`` (the composable grammar);
``.save(path)`` lays the tree out, draws the branch skeleton, runs each layer, and writes the file.

    >>> fig = plot(tree) + color_branches(values) + tip_labels()   # doctest: +SKIP
    >>> fig.save("tree.pdf")                                        # doctest: +SKIP

A **layer** is just a callable ``(canvas, tree, layout, style) -> None``; that is the whole extension
contract, so new decorations never touch the figure.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from ..render import Canvas
from ..style import Style
from .layout import Layout, radial, rectangular, unrooted
from .skeleton import draw_branches
from .tree import Tree

Layer = Callable[[Canvas, Tree, Layout, Style], None]

_LAYOUTS = {"rectangular": rectangular, "radial": radial, "unrooted": unrooted}


@dataclass
class TipPos:
    """Where a leaf lands on the rendered page, in pixels."""

    name: str
    x: float
    y: float


@dataclass
class Geometry:
    """The rendered figure's pixel geometry — enough to align something else (a heatmap, an
    alignment) to the tree's tips without redrawing the tree. ``tips`` are in top-to-bottom order;
    ``tip_x`` is the pixel x where the tips end (where a companion panel can begin)."""

    size: tuple[float, float]
    tips: list[TipPos]
    tip_x: float


class Figure:
    """A tree plus a layout, a style, and an ordered list of layers. Immutable-ish: ``+`` returns a
    new figure with one more layer, so a base figure can be reused."""

    def __init__(self, tree: Tree, *, layout: str = "rectangular", stem: bool = True,
                 style: Style | None = None, dashed=None, skeleton: bool = True,
                 layers: tuple[Layer, ...] = ()) -> None:
        if layout not in _LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {sorted(_LAYOUTS)}")
        self.tree = tree
        self.layout = layout
        self.stem = stem
        self.style = style or Style()
        self.dashed = dashed  # node names whose branch is drawn dashed (e.g. extinct lineages)
        # whether to draw the default-colour base skeleton first. Turn OFF when a colouring layer
        # paints every branch itself (e.g. color_history), so dashed branches aren't underlaid by a
        # solid line showing through the gaps.
        self.skeleton = skeleton
        self.layers = tuple(layers)

    def __add__(self, layer: Layer) -> "Figure":
        return Figure(self.tree, layout=self.layout, stem=self.stem, style=self.style,
                      dashed=self.dashed, skeleton=self.skeleton, layers=self.layers + (layer,))

    def with_size(self, width: float, height: float) -> "Figure":
        """A copy of this figure rendered at a given pixel size (same tree, layers, style otherwise).
        Used to fit the tree into a column beside a companion panel."""
        return Figure(self.tree, layout=self.layout, stem=self.stem,
                      style=replace(self.style, width=width, height=height),
                      dashed=self.dashed, skeleton=self.skeleton, layers=self.layers)

    def geometry(self) -> Geometry:
        """The pixel positions of the tips for this figure's current style — so a companion panel can
        line its rows up with the tree without redrawing it."""
        layout = _LAYOUTS[self.layout](self.tree, stem=self.stem)
        canvas = Canvas(self.style, layout.xlim, layout.ylim,
                        equal_aspect=(self.layout != "rectangular"))
        tips = [TipPos(leaf.name or "", canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf)))
                for leaf in self.tree.leaves]
        tip_x = max((t.x for t in tips), default=canvas.size[0])
        return Geometry(canvas.size, tips, tip_x)

    def _build(self) -> Canvas:
        layout = _LAYOUTS[self.layout](self.tree, stem=self.stem)
        canvas = Canvas(self.style, layout.xlim, layout.ylim,
                        equal_aspect=(layout.kind != "rectangular"))
        # A colouring layer overdraws the skeleton, so it has to know which branches were dashed or
        # it silently paints them solid — a run's extinct lineages disappearing into the colour is
        # exactly how that has gone wrong. The figure knows; the layers see the canvas; so it goes
        # here, and `color_branches(dashed=...)` overrides it when a caller wants something else.
        canvas.dashed = self.dashed
        if self.skeleton:
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
         style: Style | None = None, dashed=None, skeleton: bool = True) -> Figure:
    """Start a figure for ``tree``. Add layers with ``+``, then :meth:`Figure.save`. ``dashed`` is an
    optional set of node names whose branches are drawn dashed (e.g. extinct lineages). Set
    ``skeleton=False`` when a colouring layer paints every branch itself (so dashed branches are not
    underlaid by a solid line)."""
    return Figure(tree, layout=layout, stem=stem, style=style, dashed=dashed, skeleton=skeleton)


def _draw_skeleton(canvas: Canvas, tree: Tree, layout: Layout, style: Style, dashed=None) -> None:
    """The always-present base layer: the branches in the default colour, drawn for whichever layout
    is in force (a colouring layer later overdraws them)."""
    draw_branches(canvas, tree, layout, color=lambda node: style.branch_color,
                  width=style.branch_width, gradient=False, dashed=dashed)
