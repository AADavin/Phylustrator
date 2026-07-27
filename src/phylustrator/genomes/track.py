"""Gene-arrow drawing — the domain drawer (Phylustrator's ``skeleton``, for genomes).

Both the base map and the ``genes`` colouring layer draw through :func:`draw_genes`, so a gene is
drawn one way and every layer follows. ``linear`` draws straight arrows; ``circular`` draws the same
arrow bent along its ring.
"""

from __future__ import annotations

import math


def draw_genes(canvas, layout, color, style) -> None:
    """Draw each gene the layout placed as an arrow pointing along its strand, filled by
    ``color(gene)``. Reads ``layout.genes``, so single / stacked / circular all flow through here."""
    if layout.kind == "circular":
        _draw_circular(canvas, layout, color, style)
    else:
        _draw_linear(canvas, layout, color, style)


def _draw_linear(canvas, layout, color, style) -> None:
    hh = style.gene_height / 2.0            # half-height, in row-spacing units
    for gene in layout.genes:
        x0, x1, y = layout.box(gene)
        tip = 0.4 * (x1 - x0)
        if gene.strand >= 0:
            pts = [(x0, y - hh), (x1 - tip, y - hh), (x1, y), (x1 - tip, y + hh), (x0, y + hh)]
        else:
            pts = [(x1, y - hh), (x0 + tip, y - hh), (x0, y), (x0 + tip, y + hh), (x1, y + hh)]
        canvas.polygon(pts, fill=color(gene), stroke=style.gene_stroke,
                       stroke_width=style.gene_stroke_width)


def _polar(a: float, r: float) -> tuple[float, float]:
    return r * math.cos(a), r * math.sin(a)


def _arc(a0: float, a1: float, r: float, step: float = 0.12):
    """Points along the arc from ``a0`` to ``a1`` at radius ``r`` (data coords)."""
    n = max(1, int(math.ceil(abs(a1 - a0) / step)))
    return [_polar(a0 + (a1 - a0) * i / n, r) for i in range(n + 1)]


def _draw_circular(canvas, layout, color, style) -> None:
    hh = layout.ring_hh
    for gene in layout.genes:
        a0, a1, R = layout.box(gene)
        ri, ro = R - hh, R + hh
        span = a1 - a0
        tip = 0.4 * span                       # angular length of the arrowhead
        if gene.strand >= 0:                    # arrow points toward a1
            base = a1 - tip
            pts = _arc(a0, base, ro) + [_polar(a1, R)] + _arc(base, a0, ri)
        else:                                   # arrow points toward a0
            base = a0 + tip
            pts = _arc(base, a1, ro) + _arc(a1, base, ri) + [_polar(a0, R)]
        canvas.polygon(pts, fill=color(gene), stroke=style.gene_stroke,
                       stroke_width=style.gene_stroke_width)
