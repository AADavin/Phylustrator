"""The highlight layer — mark a span of a genome (a rearranged segment, a region of interest).

Shades the ranks ``[start, end]`` of one genome's chromosome with a tinted, outlined band that the
gene arrows read through. Works on a single ``plot`` or on one track of a ``stack``.
"""

from __future__ import annotations

from ..track import _arc, _polar


def highlight(genome, chromosome=None, start: int = 0, end: int = 0, *,
              color: str = "#f0cf7a", label: str | None = None, pad: float = 0.12):
    """Highlight positions ``start``..``end`` (inclusive) on ``genome`` / ``chromosome`` — a soft band
    behind the gene arrows, straight (linear/stacked) or curved along the ring (circular). Add it
    *before* the ``genes`` layer to sit behind them.

    ``chromosome`` may be a :class:`Chromosome`, its ``id``, or ``None`` (any chromosome)."""

    def _matches(owner):
        g, chrom = owner
        if g is not genome:
            return False
        return chromosome is None or chrom is chromosome or chrom.id == chromosome

    def layer(canvas, primary, layout, style):
        sel = [gene for gene in layout.genes
               if _matches(layout.owner[id(gene)]) and start <= gene.position <= end]
        if not sel:
            return
        boxes = [layout.box(g) for g in sel]
        if layout.kind == "circular":
            a_lo = min(min(b[0], b[1]) for b in boxes)
            a_hi = max(max(b[0], b[1]) for b in boxes)
            R = boxes[0][2]
            hh = layout.ring_hh * 1.9 + pad                 # a halo a touch wider than the genes
            band = _arc(a_lo, a_hi, R + hh) + _arc(a_hi, a_lo, R - hh)
            canvas.polygon(band, fill=color, opacity=0.55, stroke=color, stroke_width=1.2)
            if label:
                mx, my = _polar((a_lo + a_hi) / 2.0, R + hh + 0.06)
                canvas.text(mx, my, label, anchor="middle", color=color, size=style.font_size)
            return
        x0 = min(b[0] for b in boxes)
        x1 = max(b[1] for b in boxes)
        y = boxes[0][2]
        hh = style.gene_height / 2.0 + pad
        canvas.region(x0, y - hh, x1, y + hh, fill=color, opacity=0.35,
                      stroke=color, stroke_width=1.4, rx=4.0)
        if label:
            canvas.text((x0 + x1) / 2.0, y - hh, label, dy=-6, anchor="middle",
                        color=color, size=style.font_size)

    return layer
