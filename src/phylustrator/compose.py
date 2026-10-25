"""Composition — put a panel beside a Phylustrator tree, rows lined up with the tips, or below it,
lined up with the time axis.

``beside(tree, panel)`` takes a **Phylustrator** figure (the phylogeny — Phylustrator draws it, we do
not redraw it) and a panel (``heatmap`` / ``alignment``). It asks the tree for its tip pixel positions
(``Figure.geometry``), renders the tree into the left column, and draws the panel to the right with
each row at its tip's ``y`` — so a genome's row sits exactly on its leaf.

``below(tree, panel)`` is its x-axis twin: the panel (``trees.node_points``) sits under the tree and
places each value at its node's pixel ``x``.
"""

from __future__ import annotations

from dataclasses import replace

from .render import Canvas
from .style import Style
from .trees.layers.guides import draw_time_axis


class Composite:
    """The rendered composite; save like any figure."""

    def __init__(self, canvas: Canvas) -> None:
        self._canvas = canvas

    def as_svg(self) -> str:
        return self._canvas.as_svg()

    def save(self, path):
        return self._canvas.save(path)


def beside(tree, panel, *, width: float = 1100.0, height: float | None = None,
           tree_fraction: float = 0.4, gap: float = 18.0, pad: float = 34.0,
           footer: float = 0.0, background: str = "white") -> Composite:
    """Render Phylustrator ``tree`` on the left and ``panel`` on the right, rows aligned to the tips.

    ``tree_fraction`` is the share of the width given to the tree column (the rest, minus ``gap`` and
    ``pad``, holds the panel). ``footer`` reserves blank height below the rows (for a panel's colour
    key). Rows are matched to tips by label and drawn in the tree's tip order.

    The tree is nested as **vectors**, so the composite is one: it used to be rendered to a PNG and
    pasted in, which made a figure for a journal a picture of a tree beside a drawing of a panel,
    and needed cairosvg to build at all."""
    n_tips = len(tree.tree.leaves)
    # per-tip row height eases from ~44px (few tips) down to ~24px (many), so 25-40 rows stay sane
    row_px = max(24.0, 46.0 - 0.55 * n_tips)
    H = height if height is not None else max(260.0, 70.0 + row_px * n_tips) + footer
    tree_w = round(width * tree_fraction)
    tree_h = H - footer                              # tips fill the area above the footer

    sized = tree.with_size(tree_w, tree_h)
    geom = sized.geometry()

    canvas = Canvas(Style(width=width, height=H, margin=0, background=background), (0.0, 1.0), (0.0, 1.0))
    canvas.embed_svg(sized.as_svg(), 0, 0, tag="tree")

    # A panel that wants **every** tip row says so, and gets them all — including tips it has no
    # value for. `Bars` does: its axis sits under the last row it is handed, and filtering the rows
    # down to the ones it has values for put that axis under the last *valued* tip instead of under
    # the tree, so a tree with extinct tips below the last bar drew its two axes at different heights.
    wanted = set(panel.rows)
    rows = [(t.name, t.y) for t in geom.tips
            if getattr(panel, "all_rows", False) or t.name in wanted]
    if rows:
        panel.draw(canvas, tree_w + gap, width - pad, rows, canvas.style)
    return Composite(canvas)


def below(tree, panel, *, panel_height: float = 200.0, gap: float = 18.0, axis: str | None = "Time",
          ticks: int = 5) -> Composite:
    """Render Phylustrator ``tree`` with ``panel`` underneath, both on the tree's x axis.

    The x-axis twin of :func:`beside`: a value at a node sits directly under that node (see
    :func:`~phylustrator.trees.node_points`). The tree keeps its own style — width, height, margins —
    and every node lands on the pixel it has in the tree alone. The page grows by ``gap`` plus
    ``panel_height``, and the panel spans the tree's left and right pixel edges.

    ``axis`` labels a time axis under the panel; ``None`` draws none. Leave ``time_axis`` off the
    tree itself: anything a tree layer puts in its bottom margin (``time_axis``, ``scale_bar``, a
    bottom-left ``colorbar``) lands in the panel. The panel's y axis sits in the tree's left margin,
    so widen ``margin_left`` in the tree's ``Style`` for long tick labels or a y label.

    Rectangular trees only, since that is the layout where x is time. The composite is drawn as
    vectors on one canvas, so it needs no cairosvg (unlike :func:`beside`)."""
    if tree.layout != "rectangular":
        raise ValueError(f"below() needs a rectangular tree, where x is time; got layout={tree.layout!r}")
    if not hasattr(panel, "draw_below"):
        raise TypeError(f"below() takes a panel lined up with the tree's x axis, such as trees.node_points; "
                        f"{type(panel).__name__} is not one (a row panel goes in beside())")
    style = tree.style
    ts, ls = style.font_size * 0.85, style.font_size
    plot_bottom = style.height - style.margin_at("bottom")      # where the lowest tip sits in the tree alone
    top = plot_bottom + gap
    bottom = top + panel_height
    # Under the panel: the tree's bottom margin, or more when the axis needs it. The axis label is
    # centred 14 + ts + ls + 4 below the panel, so a 40px margin cut the label in half.
    if axis is None:
        axis_room = 0.0
    elif axis:
        axis_room = 14 + ts + ls + 4 + ls / 2 + 6
    else:                                                       # ticks, no label
        axis_room = 14 + ts + 3 + ts / 2 + 6
    height = bottom + max(style.margin_at("bottom"), axis_room)
    # The same tree on a taller page, with all the extra height given to its bottom margin: the
    # nodes keep their pixels, and the panel is drawn into that margin on the same canvas.
    sized = tree.with_style(replace(style, height=height, margin_bottom=height - plot_bottom))
    geom = sized.geometry()
    canvas = sized._build()
    panel.draw_below(canvas, geom, top, bottom, style)
    if axis is not None:
        # +14 below the panel, the offset trees.time_axis leaves below a tree
        draw_time_axis(canvas, geom.px, geom.xlim[1], bottom + 14, axis, ticks=ticks,
                       tick_size=ts, label_size=ls)
    return Composite(canvas)


#: How a figure is asked for its size, if it can be asked at all.
def _natural_size(figure) -> tuple[float, float]:
    style = getattr(figure, "style", None)
    if style is not None:
        return float(style.width), float(style.height)
    canvas = getattr(figure, "_canvas", None)         # a Composite carries its canvas
    if canvas is not None:
        return float(canvas.size[0]), float(canvas.size[1])
    return 400.0, 300.0


def _letters_for(labels, cells: int):
    """The panel letters, as a list one per cell. ``True`` is A, B, C … in reading order; a string
    is taken one character per cell; a list is taken as written; ``None``/``False`` is none."""
    if not labels:
        return [None] * cells
    if labels is True:
        return [chr(ord("A") + i) for i in range(cells)]
    given = list(labels)
    if len(given) < cells:
        given += [None] * (cells - len(given))
    return given[:cells]


def page(rows, *, width: float = 800.0, height: float | None = None, title: str | None = None,
         letters=None, gap: float = 16.0, pad: float = 20.0, units: str | None = None,
         background: str = "white", title_size: float | None = None,
         letter_size: float | None = None, style: Style | None = None) -> Composite:
    """Several independent figures on one page, nested **as vectors**.

    ``rows`` is a list of rows, each a list of figures; a flat list is one row, and ``None`` leaves
    a cell empty. Every figure keeps its own layers and style and is re-rendered at its cell's size
    where it can be (a tree figure can), so the text stays the size it was asked for rather than
    being scaled with the drawing.

    This is what `beside`/`below` could not do: those pair **one** tree with **one** companion
    panel, so two trees side by side — the same tree under two analyses, the commonest comparison
    there is — had to leave the library and be stitched together as images.

    ``title`` is centred over the whole page, which a title on a figure inside it cannot be: on a
    45/55 split it would sit left of the middle. ``letters=True`` writes A, B, C … at the corner of
    each cell in reading order, or pass the labels yourself.

    ``units`` ("pt", "mm", "cm", "in") sets the page's physical size, leaving the drawing in pixels
    underneath, so a figure can be made to hit a journal's column width exactly: ``width=482,
    units="pt"`` is a 482 pt page. Saves to ``.svg``, ``.pdf`` or ``.png`` like any figure."""
    grid = [r if isinstance(r, (list, tuple)) else [r] for r in rows] \
        if rows and isinstance(rows[0], (list, tuple)) else [list(rows)]
    n_cols = max(len(r) for r in grid)
    base = style or Style()
    ts = title_size if title_size is not None else base.font_size * 1.5
    ls = letter_size if letter_size is not None else base.font_size * 1.25
    head = (ts * 1.9 if title else 0.0)
    cell_w = (width - 2 * pad - gap * (n_cols - 1)) / n_cols

    # a row is as tall as the tallest cell in it, keeping each figure's own proportions
    row_heights = []
    for row in grid:
        tall = 0.0
        for figure in row:
            if figure is None:
                continue
            w0, h0 = _natural_size(figure)
            tall = max(tall, cell_w * h0 / (w0 or 1.0) if hasattr(figure, "with_size") else h0)
        row_heights.append(tall or cell_w * 0.75)
    if height is not None:                            # a fixed page: share what is left between rows
        spare = height - 2 * pad - head - gap * (len(grid) - 1)
        row_heights = [spare / len(grid)] * len(grid)
    page_h = height if height is not None else (2 * pad + head + sum(row_heights)
                                                + gap * (len(grid) - 1))

    canvas = Canvas(Style(width=width, height=page_h, margin=0, background=background,
                          font_family=base.font_family, label_color=base.label_color),
                    (0.0, 1.0), (0.0, 1.0))
    if title:
        canvas.raw_text(width / 2, pad + ts * 0.8, title, anchor="middle", weight="bold", size=ts,
                        color=base.label_color)

    # letters go to the figures, not to the cells: an empty cell is a gap in the page, and a gap
    # should not eat a letter and leave the next panel called C
    marks = _letters_for(letters, sum(1 for r in grid for c in r if c is not None))
    seen = 0
    y = pad + head
    for row, row_h in zip(grid, row_heights):
        x = pad
        for figure in row:
            if figure is not None:
                mark = marks[seen]
                seen += 1
                sized = figure.with_size(cell_w, row_h) if hasattr(figure, "with_size") else figure
                canvas.embed_svg(sized.as_svg(), x, y, tag=f"c{seen}")
                if mark:
                    canvas.raw_text(x + 2, y + ls * 0.9, str(mark), anchor="start", weight="bold",
                                    size=ls, color=base.label_color)
            x += cell_w + gap
        y += row_h + gap
    if units:
        canvas.physical_size(units)
    return Composite(canvas)
