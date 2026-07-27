"""The gene-colouring layer — paint the arrows by an attribute (default the gene family).

Families get consistent colours across genomes (family "5" is the same colour everywhere), which is
what makes stacked genomes read as synteny.
"""

from __future__ import annotations

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
