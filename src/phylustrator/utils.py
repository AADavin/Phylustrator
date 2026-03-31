"""Utility functions for color parsing, coordinate conversion, and tree manipulation."""

from __future__ import annotations

import logging
import math
import random
import string

import ete3

logger = logging.getLogger(__name__)

# Standard CSS named colors (subset covering the most common use cases)
_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "yellow": (255, 255, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "brown": (165, 42, 42),
    "pink": (255, 192, 203),
    "lime": (0, 255, 0),
    "navy": (0, 0, 128),
    "teal": (0, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "coral": (255, 127, 80),
    "salmon": (250, 128, 114),
    "gold": (255, 215, 0),
    "darkgreen": (0, 100, 0),
    "darkblue": (0, 0, 139),
    "darkred": (139, 0, 0),
    "lightblue": (173, 216, 230),
    "lightgreen": (144, 238, 144),
    "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211),
}


def generate_id(prefix: str = "id", length: int = 6) -> str:
    """Generate a unique ID for SVG elements like gradients.

    Args:
        prefix: String prefix for the ID.
        length: Number of random characters to append.

    Returns:
        A string like ``"prefix_a1b2c3"``.
    """
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{suffix}"


def to_rgb(color_str: str) -> tuple[int, int, int]:
    """Parse a CSS color string into an ``(R, G, B)`` tuple.

    Supports hex codes (``#fff``, ``#ffffff``), common named colors, and
    falls back to black ``(0, 0, 0)`` for unrecognised values.

    Args:
        color_str: A CSS color string.

    Returns:
        An ``(R, G, B)`` tuple with values in ``[0, 255]``.
    """
    color_str = str(color_str).strip().lower()
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3:
            h = "".join([c * 2 for c in h])
        if len(h) != 6:
            logger.warning("Invalid hex color '%s', falling back to black.", color_str)
            return (0, 0, 0)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            logger.warning("Cannot parse hex color '%s', falling back to black.", color_str)
            return (0, 0, 0)
    result = _NAMED_COLORS.get(color_str)
    if result is None:
        logger.warning("Unknown color name '%s', falling back to black.", color_str)
        return (0, 0, 0)
    return result


def to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an ``(R, G, B)`` tuple to a hex string.

    Values are clamped to ``[0, 255]``.

    Args:
        rgb: An ``(R, G, B)`` tuple.

    Returns:
        A hex color string like ``"#ff00ab"``.
    """
    return "#{:02x}{:02x}{:02x}".format(*(int(max(0, min(255, x))) for x in rgb))


def lerp_color(low_hex: str, high_hex: str, t: float) -> str:
    """Linearly interpolate between two colors.

    Args:
        low_hex: Start color (CSS string).
        high_hex: End color (CSS string).
        t: Interpolation factor, clamped to ``[0.0, 1.0]``.

    Returns:
        A hex color string representing the interpolated color.
    """
    t = max(0.0, min(1.0, float(t)))
    c1 = to_rgb(low_hex)
    c2 = to_rgb(high_hex)
    return to_hex(tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3)))


def polar_to_cartesian(degree: float, radius: float, rotation: float = 0.0) -> tuple[float, float]:
    """Convert polar coordinates to Cartesian ``(x, y)``.

    Args:
        degree: Angle in degrees.
        radius: Radial distance from the origin.
        rotation: Additional rotation offset in degrees.

    Returns:
        A ``(x, y)`` tuple.
    """
    theta = math.radians(float(degree) + float(rotation))
    return float(radius) * math.cos(theta), float(radius) * math.sin(theta)


def add_origin_if_root_has_dist(tree: ete3.Tree, origin_name: str = "Origin") -> ete3.Tree:
    """Standardize a tree by adding an explicit origin node if the root has a non-zero distance.

    Args:
        tree: An ete3 Tree object.
        origin_name: Name to assign to the new origin node.

    Returns:
        The (possibly modified) tree with an explicit origin.
    """
    stem = float(tree.dist or 0.0)
    if stem <= 0.0:
        tree.dist = 0.0
        return tree
    origin = ete3.Tree()
    origin.name = origin_name
    origin.dist = 0.0
    tree.dist = stem
    origin.add_child(tree)
    return origin
