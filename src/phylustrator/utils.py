from __future__ import annotations
import ete3
import math
import random
import string

def generate_id(prefix: str = "id", length: int = 6) -> str:
    """Generates a unique ID for SVG elements like gradients."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{suffix}"

def to_rgb(color_str: str) -> tuple[int, int, int]:
    """Parses hex, common names, or RGB tuples into a standard RGB tuple."""
    color_str = str(color_str).strip().lower()
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        if len(h) == 3: h = "".join([c*2 for c in h])
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    common_names = {
        "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0),
        "green": (0, 128, 0), "blue": (0, 0, 255), "orange": (255, 165, 0),
        "purple": (128, 0, 128), "yellow": (255, 255, 0), "gray": (128, 128, 128)
    }
    return common_names.get(color_str, (0, 0, 0))

def to_hex(rgb: tuple[int, int, int]) -> str:
    """Converts an RGB tuple to a hex string."""
    return "#{:02x}{:02x}{:02x}".format(*[int(max(0, min(255, x))) for x in rgb])

def lerp_color(low_hex: str, high_hex: str, t: float) -> str:
    """Interpolates between two colors."""
    t = max(0.0, min(1.0, t))
    c1 = to_rgb(low_hex)
    c2 = to_rgb(high_hex)
    return to_hex(tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3)))

def polar_to_cartesian(degree: float, radius: float, rotation: float = 0) -> tuple[float, float]:
    """Converts polar coordinates (degree, radius) to (x, y)."""
    theta = math.radians(degree + rotation)
    return radius * math.cos(theta), radius * math.sin(theta)

def add_origin_if_root_has_dist(tree: ete3.Tree, origin_name: str = "Origin") -> ete3.Tree:
    """Standardizes trees by adding an explicit origin node if the root has a distance."""
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
