"""The gene layers — paint the arrows by an attribute (default the gene family), and name them.

Families get consistent colours across genomes (family "5" is the same colour everywhere), which is
what makes stacked genomes read as synteny.
"""

from __future__ import annotations

import math

from ...color import colormap, to_hex
from ..track import draw_genes


def _key(value: str):
    return (0, int(value)) if str(value).lstrip("-").isdigit() else (1, str(value))


def genes(by: str = "family", *, cmap: str = "viridis", palette: dict | None = None):
    """Colour gene arrows by ``by`` (an attribute of each gene). Returns a layer."""

    def layer(canvas, primary, layout, style):
        keys = sorted({str(getattr(g, by)) for g in layout.genes}, key=_key)
        if palette is not None:
            color_of = dict(palette)
        else:
            sample = colormap(cmap)
            n = len(keys)
            color_of = {k: to_hex(sample(i / (n - 1) if n > 1 else 0.5)) for i, k in enumerate(keys)}
        canvas.scale = {"kind": "genes", "colors": color_of, "by": by}

        def color(gene):
            return color_of.get(str(getattr(gene, by)), style.default_color)

        draw_genes(canvas, layout, color, style)

    return layer


def gene_labels(by: str = "family", *, size: float | None = None, color: str | None = None,
                pad: float = 0.09):
    """Write each gene's ``by`` beside it — the family by default. Returns a layer.

    A small genome is often *about* which family each gene belongs to: two neighbours of one family
    are a tandem duplication, and you cannot say that from colour alone once there are more families
    than a reader can hold. On a ring the label sits outside the gene at its own angle; on a track it
    sits above the box. ``pad`` is the gap, in layout units.

    This is for the handful-of-genes case. A real genome has hundreds, and hundreds of labels around
    a ring is a grey band — colour the genes instead, and let the caption name the ones that matter."""

    def layer(canvas, primary, layout, style):
        fs = size if size is not None else style.font_size
        ink = color or getattr(style, "label_color", "#1a1a1a")
        for gene in layout.genes:
            text = str(getattr(gene, by))
            if layout.kind == "circular":
                a0, a1, R = layout.box(gene)
                cx, cy = layout.centre(gene)
                a = (a0 + a1) / 2.0
                r = R + layout.half_height(R) + pad
                canvas.text(cx + r * math.cos(a), cy + r * math.sin(a), text,
                            anchor="middle", size=fs, color=ink)
            else:
                x0, x1, y = layout.box(gene)
                canvas.text((x0 + x1) / 2.0, y - style.gene_height / 2.0 - pad, text,
                            anchor="middle", size=fs, color=ink)

    return layer
