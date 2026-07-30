"""The figure — ``plot(genome)`` + layers, then render. Mirrors Phylustrator's grammar.

    fig = plot(genome, layout="linear") + genes(by="family") + position_axis()
    fig.save("map.svg")

    fig = stack([g1, g2, g3]) + genes() + synteny()          # several genomes, one per track

A **layer** is a callable ``(canvas, primary, layout, style) -> None`` — the whole extension contract.
``primary`` is the genome (or the first, for a stack); layers read the self-describing ``layout``.
"""

from __future__ import annotations

from typing import Callable

from ..render import Canvas
from ..style import Style
from .layout import Layout, circular, linear, stacked
from .track import draw_genes

Layer = Callable[[Canvas, object, Layout, Style], None]

_LAYOUTS = {"linear": linear, "circular": circular}


class Figure:
    def __init__(self, genome, *, layout: str = "linear", coordinates: str = "ordered",
                 style: Style | None = None, layers: tuple = ()) -> None:
        if layout not in _LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {sorted(_LAYOUTS)}")
        self.genome = genome
        self.layout = layout
        self.coordinates = coordinates
        self.style = style or Style()
        self.layers = tuple(layers)

    def _make_layout(self) -> Layout:
        return _LAYOUTS[self.layout](self.genome, coordinates=self.coordinates, style=self.style)

    def _clone(self, **kw) -> "Figure":
        base = dict(layout=self.layout, coordinates=self.coordinates, style=self.style,
                    layers=self.layers)
        base.update(kw)
        return Figure(self.genome, **base)  # type: ignore[arg-type]  # kw dict, params are typed

    def __add__(self, layer: Layer) -> "Figure":
        return self._clone(layers=self.layers + (layer,))

    def _build(self) -> Canvas:
        layout = self._make_layout()
        canvas = Canvas(self.style, layout.xlim, layout.ylim, equal_aspect=layout.equal_aspect)
        _draw_base(canvas, layout, self.style)
        primary = layout.track_order[0] if layout.track_order else None
        for layer in self.layers:
            layer(canvas, primary, layout, self.style)
        return canvas

    def as_svg(self) -> str:
        return self._build().as_svg()

    def save(self, path):
        return self._build().save(path)


class StackFigure(Figure):
    """A figure over several genomes (one track each). Same grammar; a different layout."""

    def __init__(self, genomes, *, coordinates: str = "ordered", style: Style | None = None,
                 layers: tuple = ()) -> None:
        self.genomes = list(genomes)
        self.layout = "stacked"
        self.coordinates = coordinates
        n = len(self.genomes)
        self.style = style or Style(height=70.0 + 82.0 * n, gene_height=0.4)
        self.layers = tuple(layers)
        self.genome = self.genomes[0] if self.genomes else None

    def _make_layout(self) -> Layout:
        return stacked(self.genomes, coordinates=self.coordinates, style=self.style)

    def _clone(self, **kw) -> "StackFigure":
        base = dict(coordinates=self.coordinates, style=self.style, layers=self.layers)
        base.update({k: v for k, v in kw.items() if k in ("coordinates", "style", "layers")})
        return StackFigure(self.genomes, **base)  # type: ignore[arg-type]  # kw dict, params are typed


def plot(genome, *, layout: str = "linear", coordinates: str = "ordered",
         style: Style | None = None) -> Figure:
    """Start a figure for one ``genome``. Add layers with ``+``, then :meth:`Figure.save`."""
    return Figure(genome, layout=layout, coordinates=coordinates, style=style)


def stack(genomes, *, coordinates: str = "ordered", style: Style | None = None) -> StackFigure:
    """Start a figure comparing several ``genomes``, one horizontal track each (top genome first)."""
    return StackFigure(genomes, coordinates=coordinates, style=style)


def _draw_base(canvas: Canvas, layout: Layout, style: Style) -> None:
    """The base map: a faint backbone per track, and the gene arrows in the default colour (a
    ``genes`` layer overdraws them coloured)."""
    if layout.kind == "circular":
        if getattr(style, "ring_backbone", True):
            for R in layout.rings or []:
                canvas.data_ring(R, "#c9d2ce", 1.2, dash=True)   # a faint dashed loop behind the genes
    else:
        for y, x0, x1 in layout.backbones:
            canvas.line(x0, y, x1, y, "#d8ddda", 1.4)
    draw_genes(canvas, layout, lambda gene: style.default_color, style)
