"""The synteny layer — ribbons linking same-family genes between adjacent stacked genomes.

Runs after ``genes`` when present, so ribbons inherit the family colours the ``genes`` layer chose;
on its own it falls back to a neutral link colour. Only meaningful on a ``stack``.
"""

from __future__ import annotations

from ...color import colormap, to_hex


def _family_colors(layout, canvas):
    scale = getattr(canvas, "scale", None)
    if scale and scale.get("kind") == "genes":
        return scale["colors"]
    fams = sorted({str(g.family) for g in layout.genes})
    sample = colormap("viridis")
    n = len(fams)
    return {f: to_hex(sample(i / (n - 1) if n > 1 else 0.5)) for i, f in enumerate(fams)}


def synteny(*, by: str = "family", opacity: float = 0.3, color: str | None = None):
    """Link genes sharing ``by`` between neighbouring tracks with a curved ribbon. ``color`` overrides
    the per-family colour with a single neutral tone."""

    def layer(canvas, primary, layout, style):
        tracks = layout.track_order
        if len(tracks) < 2:
            return
        colors = _family_colors(layout, canvas)
        hh = style.gene_height / 2.0
        # genes grouped by (track index, key)
        per_track = [{} for _ in tracks]
        index = {id(g): t for t, gen in enumerate(tracks)
                 for g in gen.genes if id(g) in layout.boxes}
        for g in layout.genes:
            t = index.get(id(g))
            if t is None:
                continue
            per_track[t].setdefault(str(getattr(g, by)), []).append(g)
        for t in range(len(tracks) - 1):
            upper, lower = per_track[t], per_track[t + 1]
            for key, ups in upper.items():
                downs = lower.get(key)
                if not downs:
                    continue
                fill = color or colors.get(key, style.default_color)
                ups = sorted(ups, key=lambda g: layout.box(g)[0])
                downs = sorted(downs, key=lambda g: layout.box(g)[0])
                for i, u in enumerate(ups):
                    d = downs[min(i, len(downs) - 1)]      # pair by copy order
                    ux0, ux1, uy = layout.box(u)
                    dx0, dx1, dy = layout.box(d)
                    canvas.ribbon(ux0, ux1, uy + hh, dx0, dx1, dy - hh, fill=fill, opacity=opacity)

    return layer
