"""Colour — colormaps for continuous values, palettes for categories, and normalisation.

Matplotlib-free: the viridis ramp is a small embedded lookup table sampled by interpolation, and the
categorical palette is Paul Tol's colour-blind-safe "bright" set.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable

# viridis, 16 anchor colours (R, G, B in 0–255), sampled evenly from matplotlib.
_COLORMAPS: dict[str, list[tuple[int, int, int]]] = {
    "viridis": [
        (68, 1, 84), (72, 26, 108), (71, 47, 125), (65, 68, 135),
        (57, 86, 140), (49, 104, 142), (42, 120, 142), (35, 136, 142),
        (31, 152, 139), (34, 168, 132), (53, 183, 121), (84, 197, 104),
        (122, 209, 81), (165, 219, 54), (210, 226, 27), (253, 231, 37),
    ],
}

# Paul Tol "bright" — distinct and colour-blind-safe.
_PALETTE = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]


def to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(max(0, min(255, round(c)))) for c in rgb))


def colormap(name: str = "viridis") -> Callable[[float], tuple[int, int, int]]:
    """Return a sampler ``t in [0, 1] -> (R, G, B)`` that interpolates the named colormap."""
    anchors = _colormap_anchors(name)
    n = len(anchors)

    def sample(t: float) -> tuple[int, int, int]:
        t = max(0.0, min(1.0, float(t)))
        pos = t * (n - 1)
        i = int(math.floor(pos))
        if i >= n - 1:
            return anchors[-1]
        frac = pos - i
        a, b = anchors[i], anchors[i + 1]
        return tuple(a[k] + (b[k] - a[k]) * frac for k in range(3))

    return sample


def colormap_hex(name: str = "viridis") -> list[str]:
    """The colormap's anchor colours as hex — for a gradient bar."""
    return [to_hex(rgb) for rgb in _colormap_anchors(name)]


def _colormap_anchors(name: str) -> list[tuple[int, int, int]]:
    anchors = _COLORMAPS.get(name.lower())
    if anchors is None:
        raise ValueError(f"unknown colormap {name!r}; available: {sorted(_COLORMAPS)}")
    return anchors


def palette(labels: Iterable) -> dict:
    """A ``{label: hex colour}`` map over ``labels`` (sorted for stability), from the bright set."""
    ordered = sorted(set(labels), key=str)
    return {label: _PALETTE[i % len(_PALETTE)] for i, label in enumerate(ordered)}


def normalize(values: Iterable[float]) -> tuple[float, float, Callable[[float], float]]:
    """Return ``(vmin, vmax, to_unit)`` where ``to_unit(v)`` maps ``[vmin, vmax] -> [0, 1]``."""
    nums = [float(v) for v in values]
    vmin, vmax = min(nums), max(nums)
    span = (vmax - vmin) or 1.0
    return vmin, vmax, lambda v: (float(v) - vmin) / span


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def map_values(values: dict, *, cmap: str = "viridis",
               palette: dict | None = None) -> tuple[dict, dict]:
    """Turn ``{key: value}`` into ``({key: hex colour}, scale)``, dispatching on the data: numbers get
    the colormap (and a ``continuous`` scale for a colour bar), labels get a palette (and a
    ``categorical`` scale for a legend). ``scale`` is ``None`` if there is nothing to colour."""
    present = {k: v for k, v in values.items() if v is not None}
    if not present:
        return {}, None
    if all(_is_number(v) for v in present.values()):
        vmin, vmax, to_unit = normalize(present.values())
        sample = colormap(cmap)
        colors = {k: to_hex(sample(to_unit(v))) for k, v in present.items()}
        return colors, {"kind": "continuous", "vmin": vmin, "vmax": vmax, "cmap": cmap}
    pal = palette or globals()["palette"](present.values())
    return {k: pal[v] for k, v in present.items()}, {"kind": "categorical", "palette": pal}
