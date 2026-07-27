"""Composition — put a Genustrator panel beside a Phylustrator tree, rows lined up with the tips.

``beside(tree, panel)`` takes a **Phylustrator** figure (the phylogeny — Phylustrator draws it, we do
not redraw it) and a panel (``heatmap`` / ``alignment``). It asks the tree for its tip pixel positions
(``Figure.geometry``), renders the tree into the left column, and draws the panel to the right with
each row at its tip's ``y`` — so a genome's row sits exactly on its leaf.
"""

from __future__ import annotations

from .render import Canvas
from .style import Style


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

    wanted = set(panel.rows)
    rows = [(t.name, t.y) for t in geom.tips if t.name in wanted]
    if rows:
        panel.draw(canvas, tree_w + gap, width - pad, rows, canvas.style)
    return Composite(canvas)
