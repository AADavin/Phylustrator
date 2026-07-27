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
    # trees
    branch_color: str = "#333333"
    branch_width: float = 1.6
    # genomes
    gene_height: float = 0.6            # gene-arrow height as a fraction of the row spacing
    gene_stroke: str = "#2a2a2a"
    gene_stroke_width: float = 0.7
    default_color: str = "#9fb2ac"
    # shared text / background
    font_family: str = "Helvetica"
    font_size: float = 12.0
    label_color: str = "#222222"
    background: str | None = "white"
