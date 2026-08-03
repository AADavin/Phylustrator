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
            dash = getattr(style, "gene_style", "arrow") != "wedge"     # arrow: dashed loop; wedge: the classic solid one
            color, width = ("#c9d2ce", 1.2) if dash else ("#d8ddda", 1.4)
            for R in layout.rings or []:
                canvas.data_ring(R, color, width, dash=dash)
    else:
        for y, x0, x1 in layout.backbones:
            canvas.line(x0, y, x1, y, "#d8ddda", 1.4)
    draw_genes(canvas, layout, lambda gene: style.default_color, style)


#: Cell side (px) below which `GridFigure` stops drawing borders between cells — eight, so a 0.6px
#: hairline is at most ~7% of a cell rather than a tenth of it.
_GRID_MIN_CELL = 8.0


class GridFigure(Figure):
    """A :class:`~phylustrator.genomes.matrix.Matrix` as a figure in its own right.

    ``heatmap`` is a **panel**: it is handed one pixel row per tree tip by
    :func:`~phylustrator.compose.beside`, so it only exists next to a tree. A matrix is often the
    whole picture — a phyletic profile with a few hundred families is not a companion to anything,
    and sorting its rows by prevalence rather than by tip order is the point of the figure. This is
    that: rows top to bottom, columns left to right, in the order the `Matrix` carries them.

    ``palette`` maps values to colours directly (``{0: "#eee", 1: "#26565B"}``) — the right reading
    for presence/absence, where a continuous ramp would imply an ordering between two categories
    that do not have one. Without it the values run along ``cmap`` between ``vmin`` and ``vmax``.

    ``borders`` draws a border between cells: a colour to force one, ``False`` to forbid it, and the
    default ``None`` to decide by size. A border needs a cell with an inside to be a border of — at a
    few hundred rows a hairline is a tenth of each cell, so the picture becomes a mesh with the data
    behind it, and a solid block of identical values reads as criss-crossed rather than solid.
    """

    def __init__(self, matrix, *, cmap: str = "viridis", palette=None, vmin=None, vmax=None,
                 row_labels: bool = False, col_labels: bool = False,
                 borders: "str | bool | None" = None,
                 style: Style | None = None, layers: tuple = ()) -> None:
        self.matrix = matrix
        self.cmap = cmap
        self.palette = dict(palette) if palette else None
        vals = [v for r in matrix.values for v in r]
        self.vmin = 0.0 if vmin is None else vmin
        self.vmax = (max(vals) if vals else 1.0) if vmax is None else vmax
        self.row_labels = row_labels
        self.col_labels = col_labels
        self.borders = borders
        self.style = style or Style()
        self.layers = tuple(layers)
        self.genome = None                      # a grid has none; kept for the Figure contract

    def _clone(self, **kw) -> "GridFigure":
        base = dict(cmap=self.cmap, palette=self.palette, vmin=self.vmin, vmax=self.vmax,
                    row_labels=self.row_labels, col_labels=self.col_labels, borders=self.borders,
                    style=self.style, layers=self.layers)
        base.update(kw)
        return GridFigure(self.matrix, **base)  # type: ignore[arg-type]  # kw dict, params are typed

    def _build(self) -> Canvas:
        from ..color import colormap, to_hex

        m = self.style.margin
        canvas = Canvas(self.style, (0.0, 1.0), (0.0, 1.0))
        nrow, ncol = len(self.matrix.rows), len(self.matrix.cols)
        if not nrow or not ncol:
            return canvas
        x0, y0 = m, m
        w = self.style.width - 2 * m
        h = self.style.height - 2 * m
        cw, ch = w / ncol, h / nrow

        sample = colormap(self.cmap)
        span = (self.vmax - self.vmin) or 1.0
        # A border needs a cell with an inside to be a border of. `_GRID_MIN_CELL` is where a 0.6px
        # hairline stops being a line between cells and starts being a mesh over them: below it the
        # border is a tenth of the cell, and a solid block of identical values reads as criss-crossed.
        if self.borders is False:
            stroke = None
        elif isinstance(self.borders, str):
            stroke = self.borders
        else:
            stroke = "#ffffff" if min(cw, ch) >= _GRID_MIN_CELL else None
        for i, label in enumerate(self.matrix.rows):
            for j, v in enumerate(self.matrix.values[i]):
                fill = (self.palette.get(v, "#ffffff") if self.palette is not None
                        else to_hex(sample((v - self.vmin) / span)))
                canvas.raw_rect(x0 + j * cw, y0 + i * ch, cw, ch, fill=fill,
                                stroke=stroke or "none", stroke_width=0.6 if stroke else 0.0)
            if self.row_labels:
                canvas.raw_text(x0 - 6, y0 + (i + 0.5) * ch, str(label), anchor="end",
                                size=self.style.font_size * 0.8)
        if self.col_labels:
            for j, c in enumerate(self.matrix.cols):
                canvas.raw_text(x0 + (j + 0.5) * cw, y0 - 6, str(c), anchor="start",
                                baseline="alphabetic", size=self.style.font_size * 0.8, rotate=-60)
        for layer in self.layers:
            layer(canvas, None, None, self.style)
        return canvas


def grid(matrix, **kw) -> GridFigure:
    """Start a figure for a whole :class:`~phylustrator.genomes.matrix.Matrix` — rows × columns as
    coloured cells, with no tree beside it. See :class:`GridFigure`.

        ph.genomes.grid(M, palette={0: "#F4F3EE", 1: "#26565B"}).save("profiles.png")
    """
    return GridFigure(matrix, **kw)
