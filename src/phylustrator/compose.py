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
    key). Rows are matched to tips by label and drawn in the tree's tip order. Needs ``cairosvg``."""
    try:
        import cairosvg
    except ImportError as exc:                       # pragma: no cover
        raise RuntimeError("genustrator.beside needs cairosvg (pip install genustrator[export]) "
                           "to place the tree into the composite") from exc

    n_tips = len(tree.tree.leaves)
    # per-tip row height eases from ~44px (few tips) down to ~24px (many), so 25-40 rows stay sane
    row_px = max(24.0, 46.0 - 0.55 * n_tips)
    H = height if height is not None else max(260.0, 70.0 + row_px * n_tips) + footer
    tree_w = round(width * tree_fraction)
    tree_h = H - footer                              # tips fill the area above the footer

    sized = tree.with_size(tree_w, tree_h)
    geom = sized.geometry()
    png = cairosvg.svg2png(bytestring=sized.as_svg().encode(),
                           output_width=int(tree_w * 2), output_height=int(tree_h * 2))

    canvas = Canvas(Style(width=width, height=H, margin=0, background=background), (0.0, 1.0), (0.0, 1.0))
    canvas.embed_png(png, 0, 0, tree_w, tree_h)

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
