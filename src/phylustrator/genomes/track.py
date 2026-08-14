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


def _polar(a: float, r: float, c: tuple[float, float] = (0.0, 0.0)) -> tuple[float, float]:
    return c[0] + r * math.cos(a), c[1] + r * math.sin(a)


def _arc(a0: float, a1: float, r: float, step: float = 0.12, c: tuple[float, float] = (0.0, 0.0)):
    """Points along the arc from ``a0`` to ``a1`` at radius ``r`` (data coords)."""
    n = max(1, int(math.ceil(abs(a1 - a0) / step)))
    return [_polar(a0 + (a1 - a0) * i / n, r, c) for i in range(n + 1)]


def _draw_circular(canvas, layout, color, style) -> None:
    """Each gene an arrow bent along its ring. ``gene_style="arrow"`` (default) is a chunky body with a
    flared arrowhead (head wider than the body, tapering to a point — the beautiful genome look);
    ``"wedge"`` is the thin, un-flared shape."""
    chunky = getattr(style, "gene_style", "arrow") != "wedge"
    for gene in layout.genes:
        a0, a1, R = layout.box(gene)
        c = layout.centre(gene)                 # a row of circles gives each chromosome its own
        hh = layout.half_height(R)
        ri, ro = R - hh, R + hh
        # Angles run clockwise, so a1 < a0 and the raw difference is NEGATIVE. Everything below is
        # sized on the magnitude and placed with `way`, the direction position runs in. Taking the
        # difference signed instead made `min(0.45 * span, 11°)` pick the 45% every time — the cap
        # never bound, so a five-gene ring drew heads nearly half the gene long — and made the flare
        # term negative, so `max(hh, …)` collapsed to `hh` and no arrow ever flared at all.
        way = 1.0 if a1 >= a0 else -1.0
        span = abs(a1 - a0)
        tip = min(0.45 * span, math.radians(11.0))   # arrowhead angular length (capped for long genes)
        # flare the head past the body only when the tip has angular room; on a gene-dense ring the
        # tip is tiny, so a fixed flare would stick out as a radial thorn — cap it to the tip's arc.
        head_hh = max(hh, min(hh * 1.5, R * tip)) if chunky else hh
        if gene.strand >= 0:                    # arrow points toward a1
            base = a1 - way * tip
            pts = (_arc(a0, base, ro, c=c)
                   + [_polar(base, R + head_hh, c), _polar(a1, R, c), _polar(base, R - head_hh, c)]
                   + _arc(base, a0, ri, c=c))
        else:                                   # arrow points toward a0
            base = a0 + way * tip
            pts = ([_polar(a0, R, c), _polar(base, R + head_hh, c)]
                   + _arc(base, a1, ro, c=c)
                   + _arc(a1, base, ri, c=c)
                   + [_polar(base, R - head_hh, c)])
        canvas.polygon(pts, fill=color(gene), stroke=style.gene_stroke,
                       stroke_width=style.gene_stroke_width)
