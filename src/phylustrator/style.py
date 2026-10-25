"""Style — the aesthetic knobs shared across a figure.

One small dataclass: canvas size and margin, branch colour/width, label font. Layers read from it so a
figure looks consistent; pass a customised ``Style`` to :func:`~phylustrator.figure.plot` to restyle.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Style:
    width: float = 800.0
    height: float = 600.0
    margin: float = 50.0
    #: one side's margin, when it should differ from ``margin``; ``None`` takes ``margin``. A
    #: composite reserves room on one side — a y axis on the left, a panel underneath — without
    #: moving the other three. Read a side through :meth:`margin_at`, never the field itself.
    margin_left: float | None = None
    margin_right: float | None = None
    margin_top: float | None = None
    margin_bottom: float | None = None
    #: extra space above the plot, on top of ``margin``. A colorbar or legend is drawn inside
    #: the plotting area, so on a tree whose first branch reaches the top corner the two share
    #: a row; this pushes the tree down instead of moving the key somewhere worse.
    headroom: float = 0.0
    # trees
    branch_color: str = "#333333"
    branch_width: float = 1.6
    #: how a branch ends. ``"round"`` (the default) softens the tips and hides the joint where two
    #: segments meet; ``"butt"`` squares them off, which is what a LaTeX/TikZ diagram looks like —
    #: and what a wide branch needs, since a round cap adds half its width at each end and so reads
    #: as longer than it is. A single call may still override it.
    line_cap: str = "round"
    # genomes
    gene_height: float = 0.6            # gene-arrow height as a fraction of the row spacing
    gene_stroke: str = "#2a2a2a"
    gene_stroke_width: float = 0.7
    default_color: str = "#9fb2ac"
    gene_style: str = "arrow"           # circular gene shape: "arrow" (chunky, flared head, dashed backbone) or "wedge" (the classic thin genes on a solid backbone)
    ring_gene_frac: float | None = None  # circular gene half-thickness (fraction of the per-ring band); None → 0.30 for "arrow", 0.11 for "wedge"
    ring_backbone: bool = True          # circular: draw the backbone loop behind the genes
    # shared text / background
    font_family: str = "Helvetica"
    font_size: float = 12.0
    #: the face a node's own label is written in — ``"normal"`` or ``"italic"``. A LaTeX figure
    #: sets its taxon names in maths, which is italic, while its title stays roman; this is the
    #: label's face alone, so the title, the key and the axis are not dragged along with it.
    label_style: str = "normal"
    #: the family a node's own label is written in; ``None`` takes ``font_family``. A LaTeX figure
    #: sets its taxon names from the maths font and its title from the text font, and those are two
    #: different files.
    label_family: str | None = None
    label_color: str = "#222222"
    background: str | None = "white"

    def margin_at(self, side: str) -> float:
        """The margin on ``side`` (``"left"`` / ``"right"`` / ``"top"`` / ``"bottom"``): that side's
        own value if set, else ``margin``.

        Resolved on every read, not once in ``__post_init__``: ``replace(style, margin=10)`` copies
        the side fields as they are, so a side filled in from the old ``margin`` would keep it."""
        if side not in ("left", "right", "top", "bottom"):
            raise ValueError(f"side must be 'left', 'right', 'top' or 'bottom', got {side!r}")
        own = getattr(self, f"margin_{side}")
        return self.margin if own is None else own
