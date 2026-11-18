"""Colour — colormaps for continuous values, palettes for categories, and normalisation.

Matplotlib-free: the viridis ramp is a small embedded lookup table sampled by interpolation, and the
categorical palette is Paul Tol's colour-blind-safe "bright" set.

Every ``cmap=`` in the library takes a :data:`Colormap`: one of the built-in names, or a list of
colours of your own, which is what a figure needs when none of the built-ins says the right thing.
:func:`register` gives such a list a name, so one ramp can be defined once and asked for by name
everywhere — including by the colour bar that explains it.
"""

from __future__ import annotations

import math
import re
from typing import Callable, Iterable, Sequence, Union

#: What every ``cmap=`` takes: a built-in name (optionally with ``_r``), a name added by
#: :func:`register`, or the colours themselves — hex strings or ``(R, G, B)`` triples in 0–255,
#: read as evenly spaced anchors along the ramp.
Colormap = Union[str, Sequence[Union[str, tuple[int, int, int], tuple[float, float, float]]]]

_HEX = re.compile(r"^#?(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# 16 anchor colours (R, G, B in 0–255) per map, sampled evenly from matplotlib. The three sequential
# maps are perceptually uniform; `coolwarm` is diverging, for a value read against a midpoint. A
# figure that shows two characters at once needs two maps that cannot be mistaken for each other,
# which is why more than one sequential map is here.
_COLORMAPS: dict[str, list[tuple[int, int, int]]] = {
    # magma stopped before it goes pale, the same trade as `viridis_dark` below in a different hue.
    # Two line-safe ramps, not one, because a figure that shows two different quantities beside each
    # other needs them to look different — one ramp used twice reads as one quantity shown twice.
    "magma_dark": [
        (0, 0, 4), (11, 9, 36), (32, 17, 75), (59, 15, 112),
        (87, 21, 126), (114, 31, 129), (140, 41, 129), (168, 50, 125),
        (196, 60, 117), (222, 73, 104), (241, 96, 93), (250, 127, 94),
    ],
    # viridis stopped before it goes pale. A sequential ramp on a *line* has a problem a heatmap does
    # not: the light end of every perceptually-uniform map (viridis 222, magma 248, cividis 224 in
    # luminance) vanishes against white at a few pixels wide, so the values that land there are
    # invisible rather than merely faint. This keeps viridis's order and spacing and stops at its last
    # clearly-drawn green, which costs a little range and makes every value readable.
    "viridis_dark": [
        (68, 1, 84), (72, 26, 108), (71, 47, 125), (65, 68, 135),
        (57, 86, 140), (49, 104, 142), (42, 120, 142), (35, 136, 142),
        (31, 152, 139), (34, 168, 132), (53, 183, 121), (84, 197, 104),
    ],
    "viridis": [
        (68, 1, 84), (72, 26, 108), (71, 47, 125), (65, 68, 135),
        (57, 86, 140), (49, 104, 142), (42, 120, 142), (35, 136, 142),
        (31, 152, 139), (34, 168, 132), (53, 183, 121), (84, 197, 104),
        (122, 209, 81), (165, 219, 54), (210, 226, 27), (253, 231, 37),
    ],
    "magma": [
        (0, 0, 4), (11, 9, 36), (32, 17, 75), (59, 15, 112),
        (87, 21, 126), (114, 31, 129), (140, 41, 129), (168, 50, 125),
        (196, 60, 117), (222, 73, 104), (241, 96, 93), (250, 127, 94),
        (254, 159, 109), (254, 191, 132), (253, 222, 160), (252, 253, 191),
    ],
    "cividis": [
        (0, 34, 78), (0, 46, 108), (30, 58, 111), (53, 69, 108),
        (71, 81, 108), (87, 93, 109), (102, 105, 112), (117, 117, 117),
        (132, 130, 121), (148, 142, 119), (165, 156, 116), (183, 169, 110),
        (200, 184, 102), (219, 199, 90), (238, 214, 73), (254, 232, 56),
    ],
    "coolwarm": [
        (59, 76, 192), (79, 105, 217), (100, 133, 236), (123, 159, 249),
        (147, 181, 254), (170, 199, 253), (192, 212, 245), (212, 219, 230),
        (229, 216, 209), (242, 203, 183), (247, 184, 156), (245, 160, 129),
        (238, 132, 104), (224, 101, 79), (204, 64, 58), (180, 4, 38),
    ],
}

# Paul Tol "bright" — distinct and colour-blind-safe.
_PALETTE = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]


def to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(max(0, min(255, round(c)))) for c in rgb))


def colormap(name: Colormap = "viridis") -> Callable[[float], tuple[float, float, float]]:
    """Return a sampler ``t in [0, 1] -> (R, G, B)`` that interpolates the colormap."""
    anchors = _colormap_anchors(name)
    n = len(anchors)

    def sample(t: float) -> tuple[float, float, float]:
        t = max(0.0, min(1.0, float(t)))
        pos = t * (n - 1)
        i = int(math.floor(pos))
        if i >= n - 1:
            return anchors[-1]
        frac = pos - i
        a, b = anchors[i], anchors[i + 1]
        return (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac, a[2] + (b[2] - a[2]) * frac)

    return sample


def colormap_hex(name: Colormap = "viridis") -> list[str]:
    """The colormap's anchor colours as hex — for a gradient bar."""
    return [to_hex(rgb) for rgb in _colormap_anchors(name)]


def colormaps() -> list[str]:
    """Every colormap name there is, the built-in ones and any :func:`register` has added. Each of
    them also answers to ``_r``, which runs it the other way."""
    return sorted(_COLORMAPS)


def register(name: str, colors: Sequence, *, overwrite: bool = False) -> None:
    """Give a ramp of your own a name, so every ``cmap=`` in the library can ask for it.

    ``colors`` is at least two colours — hex strings or ``(R, G, B)`` triples in 0–255 — read as
    evenly spaced anchors and interpolated between, exactly as a built-in map is. The name is
    registered for the rest of the session, so a project's own ramp belongs in one place near the
    top of the script that draws with it::

        ph.color.register("warm", ["#fff7bc", "#fec44f", "#d95f0e", "#993404"])
        ph.trees.plot(tree) + ph.trees.ring(values, cmap="warm")

    A name already taken is refused unless ``overwrite=True``: silently redefining ``viridis``
    halfway through a script would leave two figures that disagree about what a colour means. A
    name ending in ``_r`` is refused outright, because that is how a map is asked for backwards —
    ``"warm"`` already gives you ``"warm_r"``."""
    key = name.strip().lower()
    if not key:
        raise ValueError("a colormap needs a name")
    if key.endswith("_r"):
        raise ValueError(f"a name ending in '_r' is how a map is asked for backwards, so {name!r} "
                         f"could never be reached; register {key[:-2]!r} and '_r' comes with it")
    if key in _COLORMAPS and not overwrite:
        raise ValueError(f"the colormap {key!r} is already registered; pass overwrite=True to "
                         f"redefine it, or choose another name")
    _COLORMAPS[key] = _anchors_from(colors, f"register({name!r})")


def _parse_color(color, who: str) -> tuple[int, int, int]:
    """One colour as ``(R, G, B)`` in 0–255, from a hex string or a triple."""
    if isinstance(color, str):
        if not _HEX.match(color.strip()):
            raise ValueError(f"{who}: {color!r} is not a colour; a hex string such as '#d95f0e' "
                             f"or '#fc0', or an (R, G, B) triple in 0-255")
        digits = color.strip().lstrip("#")
        if len(digits) == 3:
            digits = "".join(d * 2 for d in digits)
        return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))
    try:
        r, g, b = (float(c) for c in color)
    except (TypeError, ValueError):
        raise ValueError(f"{who}: {color!r} is not a colour; a hex string such as '#d95f0e', or "
                         f"an (R, G, B) triple in 0-255") from None
    if not all(0.0 <= c <= 255.0 for c in (r, g, b)):
        raise ValueError(f"{who}: {color!r} is outside 0-255. A triple is read in 0-255, not 0-1, "
                         f"because that is what the built-in maps are written in")
    return (round(r), round(g), round(b))


def _written_in_unit_scale(colors: Sequence) -> bool:
    """Whether the triples in a ramp were written in matplotlib's 0–1 rather than in this library's
    0–255.

    Worth asking, because the mistake is otherwise silent: ``(0.9, 0.4, 0.1)`` is inside 0–255 and
    rounds to ``(1, 0, 0)``, so the figure comes out black instead of orange. Every component under
    1 would be a ramp running from black to very slightly less black, which nobody draws on
    purpose. A ramp of hex strings has no triples to ask about, and one that is all zeros says
    black and means it."""
    seen: list[float] = []
    for color in colors:
        if isinstance(color, str):
            continue
        try:
            seen.extend(float(v) for v in color)
        except (TypeError, ValueError):
            return False                     # not a triple at all; _parse_color says so properly
    return bool(seen) and all(v <= 1.0 for v in seen) and any(v > 0.0 for v in seen)


def _anchors_from(colors: Sequence, who: str) -> list[tuple[int, int, int]]:
    """A sequence of colours as colormap anchors, checked."""
    given = list(colors)
    if len(given) < 2:
        raise ValueError(f"{who}: a ramp needs at least two colours to run between; got "
                         f"{len(given)}")
    if _written_in_unit_scale(given):
        raise ValueError(f"{who}: these colours look like matplotlib's 0-1; a triple here is read "
                         f"in 0-255, as the built-in maps are written, so they would all come out "
                         f"black. Multiply them by 255, or give hex strings")
    return [_parse_color(c, who) for c in given]


def _colormap_anchors(name: Colormap) -> list[tuple[int, int, int]]:
    """The colormap's anchors, from a name or from the colours themselves.

    A trailing ``_r`` reverses any name, as it does in matplotlib — the convention everyone arrives
    with, and the one a scale wants whenever the low values are the interesting ones. The error
    still lists the base names, not a doubled set."""
    if not isinstance(name, str):
        return _anchors_from(name, "cmap")
    wanted = name.strip().lower()
    reverse = wanted.endswith("_r")
    anchors = _COLORMAPS.get(wanted[:-2] if reverse else wanted)
    if anchors is None:
        raise ValueError(f"unknown colormap {name!r}; available: {sorted(_COLORMAPS)} "
                         f"(any of them with '_r' appended runs the other way). A ramp of your own "
                         f"goes in as the colours themselves — cmap=['#fff7bc', '#993404'] — or "
                         f"through color.register()")
    return list(reversed(anchors)) if reverse else anchors


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


def _clamped_unit(lo: float, span: float) -> Callable[[float], float]:
    """``to_unit`` for a range given rather than derived: values outside it clamp to the ends."""
    return lambda v: min(max((float(v) - lo) / span, 0.0), 1.0)


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def map_values(values: dict, *, cmap: Colormap = "viridis", palette: dict | None = None,
               limits: tuple[float, float] | None = None) -> tuple[dict, dict | None]:
    """Turn ``{key: value}`` into ``({key: hex colour}, scale)``, dispatching on the data: numbers get
    the colormap (and a ``continuous`` scale for a colour bar), labels get a palette (and a
    ``categorical`` scale for a legend). ``scale`` is ``None`` if there is nothing to colour.

    ``limits`` fixes the numeric range instead of taking it from the values. Panels drawn separately
    otherwise each normalise to their own min and max, so the same colour means a different number in
    each — fine for one figure, wrong for a row of them meant to be compared. Values outside the
    range clamp to the ends. Ignored for categorical data, which has a palette instead."""
    present = {k: v for k, v in values.items() if v is not None}
    if not present:
        return {}, None
    if all(_is_number(v) for v in present.values()):
        if limits is not None:
            vmin, vmax = (float(x) for x in limits)
            to_unit = _clamped_unit(vmin, (vmax - vmin) or 1.0)
        else:
            vmin, vmax, to_unit = normalize(present.values())
        sample = colormap(cmap)
        colors = {k: to_hex(sample(to_unit(v))) for k, v in present.items()}
        return colors, {"kind": "continuous", "vmin": vmin, "vmax": vmax, "cmap": cmap}
    pal = palette or globals()["palette"](present.values())
    return {k: pal[v] for k, v in present.items()}, {"kind": "categorical", "palette": pal}
