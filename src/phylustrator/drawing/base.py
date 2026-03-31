"""Base drawing infrastructure for phylogenetic tree rendering."""

from __future__ import annotations

import base64
import logging
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import drawsvg as draw

from ..utils import generate_id, lerp_color, to_hex, to_rgb

logger = logging.getLogger(__name__)

try:
    import cairosvg
except ImportError:
    cairosvg = None

# Valid shape names accepted by _draw_shape_at
_VALID_SHAPES = frozenset({"circle", "square", "triangle"})

# Valid position strings for add_title
_VALID_POSITIONS = frozenset({"top", "bottom", "left", "right"})


@dataclass
class TreeStyle:
    """Configuration object for visual styling parameters of the phylogenetic tree.

    All dimensional values are in pixels unless otherwise noted.

    Attributes:
        width: Total width of the drawing canvas. Must be positive.
        height: Total height of the drawing canvas. Must be positive.
        radius: Radius of the tree layout (radial trees only). Must be positive.
        degrees: Angular span in degrees (radial trees only).
        rotation: Global rotation offset in degrees. Defaults to -90 (12 o'clock start).
        margin: Margin padding around the tree. Must be non-negative.
        root_stub_length: Length of the root branch stub.
        leaf_r: Radius of leaf-tip circles. Set to 0 to hide.
        leaf_color: CSS color string for leaf nodes.
        branch_stroke_width: Thickness of branch lines. Must be positive.
        branch_color: CSS color string for branches.
        node_r: Radius of internal node circles. Set to 0 to hide.
        font_size: Base font size for text elements. Must be positive.
        font_family: Font family for text elements.
    """

    width: int = 1000
    height: int = 1000
    radius: int = 400
    degrees: int = 360
    rotation: int = -90
    margin: float = 100.0
    root_stub_length: float = 20.0
    leaf_r: float = 5.0
    leaf_color: str = "black"
    branch_stroke_width: float = 2.0
    branch_color: str = "black"
    node_r: float = 2.0
    font_size: int = 12
    font_family: str = "Arial"

    def __post_init__(self) -> None:
        """Validate style parameters after initialisation."""
        if self.width <= 0:
            raise ValueError(f"width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"height must be positive, got {self.height}")
        if self.radius <= 0:
            raise ValueError(f"radius must be positive, got {self.radius}")
        if self.margin < 0:
            raise ValueError(f"margin must be non-negative, got {self.margin}")
        if self.branch_stroke_width <= 0:
            raise ValueError(f"branch_stroke_width must be positive, got {self.branch_stroke_width}")
        if self.font_size <= 0:
            raise ValueError(f"font_size must be positive, got {self.font_size}")


class BaseDrawer:
    """Abstract base class providing shared rendering primitives and export functionality.

    Subclasses must implement ``_calculate_layout()`` to position tree nodes before
    any drawing operations are performed.
    """

    def __init__(self, tree: Any, style: TreeStyle | None = None) -> None:
        """Initialise the drawer with a tree structure and style configuration.

        Args:
            tree: An ete3 TreeNode object to be visualised.
            style: Custom style configuration. If ``None``, the default style is used.

        Raises:
            TypeError: If *tree* is ``None``.
        """
        if tree is None:
            raise TypeError("tree must not be None")
        self.t = tree
        self.style = style if style else TreeStyle()
        self.drawing = draw.Drawing(self.style.width, self.style.height, origin="center")
        self.drawing.append(
            draw.Rectangle(
                -self.style.width / 2,
                -self.style.height / 2,
                self.style.width,
                self.style.height,
                fill="white",
            )
        )
        self.d = self.drawing
        self.total_tree_depth: float = 0.0
        self.sf: float = 1.0
        self._layout_calculated: bool = False

    def _pre_flight_check(self) -> None:
        """Ensure layout calculations are performed before drawing operations."""
        if not self._layout_calculated:
            self._calculate_layout()
            self._layout_calculated = True

    def _calculate_layout(self) -> None:
        """Calculate node coordinates. Must be implemented by subclasses.

        Raises:
            NotImplementedError: Always, unless overridden.
        """
        raise NotImplementedError

    def _draw_shape_at(
        self,
        x: float,
        y: float,
        shape: str,
        fill: str,
        r: float,
        stroke: str | None = None,
        stroke_width: float = 1.0,
        rotation: float = 0.0,
        opacity: float = 1.0,
    ) -> None:
        """Render a geometric shape at specific coordinates.

        Args:
            x: X-coordinate of the shape centre.
            y: Y-coordinate of the shape centre.
            shape: One of ``"circle"``, ``"square"``, or ``"triangle"``.
            fill: CSS fill colour.
            r: Radius / half-side-length of the shape.
            stroke: Optional stroke colour.
            stroke_width: Stroke thickness.
            rotation: Rotation angle in degrees.
            opacity: Fill opacity in ``[0, 1]``.
        """
        shp = str(shape).lower()
        if shp not in _VALID_SHAPES:
            logger.warning("Unknown shape '%s'; expected one of %s. Skipping.", shape, _VALID_SHAPES)
            return

        common: dict[str, Any] = {"fill": fill, "opacity": opacity}
        if stroke:
            common["stroke"] = stroke
            common["stroke_width"] = stroke_width
        transform = f"rotate({rotation},{x},{y})" if rotation != 0 else None

        if shp == "circle":
            self.drawing.append(draw.Circle(x, y, float(r), **common))
        elif shp == "square":
            side = float(r) * 2.0
            self.drawing.append(draw.Rectangle(x - r, y - r, side, side, transform=transform, **common))
        elif shp == "triangle":
            side = float(r) * 2.0
            h = side * math.sqrt(3) / 2.0
            p1 = (x, y - h * 2 / 3)
            p2 = (x - side / 2, y + h / 3)
            p3 = (x + side / 2, y + h / 3)
            path = draw.Path(transform=transform, **common).M(*p1).L(*p2).L(*p3).Z()
            self.drawing.append(path)

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def add_title(
        self,
        text: str,
        font_size: int = 24,
        position: str = "top",
        pad: float = 40.0,
        color: str = "black",
        weight: str = "bold",
    ) -> None:
        """Add a title to the drawing at a cardinal position.

        Args:
            text: The title text.
            font_size: Font size in pixels.
            position: One of ``"top"``, ``"bottom"``, ``"left"``, ``"right"``.
            pad: Padding from the canvas edge.
            color: CSS text colour.
            weight: Font weight (e.g. ``"bold"``, ``"normal"``).

        Raises:
            ValueError: If *position* is not a valid cardinal direction.
        """
        if position not in _VALID_POSITIONS:
            raise ValueError(f"position must be one of {_VALID_POSITIONS}, got '{position}'")
        w, h = self.style.width, self.style.height
        tx, ty = 0.0, 0.0
        if position == "top":
            ty = -h / 2 + pad
        elif position == "bottom":
            ty = h / 2 - pad
        elif position == "left":
            tx = -w / 2 + pad
        elif position == "right":
            tx = w / 2 - pad
        self.drawing.append(
            draw.Text(
                text,
                font_size,
                tx,
                ty,
                fill=color,
                font_weight=weight,
                font_family=self.style.font_family,
                text_anchor="middle",
                dominant_baseline="middle",
            )
        )

    def add_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: int = 12,
        color: str = "black",
        weight: str = "normal",
        text_anchor: str = "start",
        dominant_baseline: str = "middle",
        rotation: float = 0.0,
    ) -> None:
        """Add arbitrary text at Cartesian coordinates.

        Args:
            text: The text content.
            x: X-coordinate.
            y: Y-coordinate.
            font_size: Font size.
            color: CSS colour string.
            weight: Font weight.
            text_anchor: Horizontal alignment.
            dominant_baseline: Vertical alignment.
            rotation: Rotation angle in degrees.
        """
        transform = f"rotate({rotation}, {x}, {y})" if rotation != 0 else None
        self.drawing.append(
            draw.Text(
                text,
                font_size,
                x,
                y,
                fill=color,
                font_weight=weight,
                font_family=self.style.font_family,
                text_anchor=text_anchor,
                dominant_baseline=dominant_baseline,
                transform=transform,
            )
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def save_svg(self, outpath: str | Path, rotation: float = 0.0) -> None:
        """Export the drawing to an SVG file.

        Args:
            outpath: Destination file path.
            rotation: Global rotation to apply to the output.
        """
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        svg_content = self._get_rotated_svg_content(rotation)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(svg_content)

    def save_png(
        self, outpath: str | Path, dpi: int = 300, scale: float | None = None, rotation: float = 0.0
    ) -> None:
        """Export the drawing to a PNG file.

        Requires the ``cairosvg`` library.

        Args:
            outpath: Destination file path.
            dpi: Resolution in dots per inch.
            scale: Explicit scale factor; computed from *dpi* if ``None``.
            rotation: Global rotation to apply to the output.

        Raises:
            ImportError: If ``cairosvg`` is not installed.
        """
        if cairosvg is None:
            raise ImportError(
                "PNG export requires 'cairosvg'. Install it with: pip install phylustrator[export]"
            )
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        if scale is None:
            scale = dpi / 72.0
        svg_content = self._get_rotated_svg_content(rotation)
        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=str(outpath), scale=scale)

    def _get_rotated_svg_content(self, rotation: float) -> str:
        """Generate SVG content, applying a global rotation if needed."""
        if rotation == 0:
            return self.drawing.as_svg()
        original_svg = self.drawing.as_svg()
        original_svg = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>", "", original_svg)
        w, h = self.style.width, self.style.height
        rad = math.radians(rotation)
        new_w = abs(w * math.cos(rad)) + abs(h * math.sin(rad))
        new_h = abs(w * math.sin(rad)) + abs(h * math.cos(rad))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{new_w}" height="{new_h}" '
            f'viewBox="0 0 {new_w} {new_h}">\n'
            f'  <g transform="translate({new_w / 2}, {new_h / 2}) rotate({rotation}) '
            f'translate({-w / 2}, {-h / 2})">\n'
            f"    {original_svg}\n"
            f"  </g>\n"
            f"</svg>"
        )

    # ------------------------------------------------------------------
    # Legends
    # ------------------------------------------------------------------

    def add_categorical_legend(
        self,
        palette: dict[str, str],
        title: str = "Legend",
        x: float | None = None,
        y: float | None = None,
        font_size: int = 14,
        r: float = 6.0,
    ) -> None:
        """Add a categorical legend with coloured circles and labels.

        Args:
            palette: Mapping of ``{label: colour_string}``.
            title: Legend title.
            x: Top-left X coordinate (auto-placed if ``None``).
            y: Top-left Y coordinate (auto-placed if ``None``).
            font_size: Text size.
            r: Radius of the marker dots.
        """
        if x is None:
            x = -self.style.width / 2 + 30
        if y is None:
            y = -self.style.height / 2 + 30
        self.drawing.append(
            draw.Text(
                title,
                font_size + 2,
                x,
                y,
                font_weight="bold",
                font_family=self.style.font_family,
                text_anchor="start",
            )
        )
        curr_y = y + font_size * 1.5
        for label, color in palette.items():
            self.drawing.append(draw.Circle(x + r, curr_y, r, fill=color))
            self.drawing.append(
                draw.Text(
                    str(label),
                    font_size,
                    x + r * 2.5,
                    curr_y,
                    font_family=self.style.font_family,
                    text_anchor="start",
                    dominant_baseline="middle",
                )
            )
            curr_y += font_size * 1.4

    def add_color_bar(
        self,
        low_color: str,
        high_color: str,
        vmin: float,
        vmax: float,
        title: str = "",
        x: float | None = None,
        y: float | None = None,
        width: float = 100.0,
        height: float = 15.0,
        font_size: int = 12,
    ) -> None:
        """Add a continuous-gradient colour bar legend.

        Args:
            low_color: Colour for the minimum value.
            high_color: Colour for the maximum value.
            vmin: Numeric minimum.
            vmax: Numeric maximum.
            title: Title text above the bar.
            x: Top-left X coordinate (auto-placed if ``None``).
            y: Top-left Y coordinate (auto-placed if ``None``).
            width: Bar width in pixels.
            height: Bar height in pixels.
            font_size: Label font size.
        """
        if x is None:
            x = -self.style.width / 2 + 30
        if y is None:
            y = self.style.height / 2 - 60
        gid = generate_id("cb_grad")
        grad = draw.LinearGradient(x, y, x + width, y, id=gid)
        grad.add_stop(0, low_color)
        grad.add_stop(1, high_color)
        self.drawing.append(grad)
        if title:
            self.drawing.append(
                draw.Text(title, font_size, x, y - 10, font_weight="bold", text_anchor="start")
            )
        self.drawing.append(
            draw.Rectangle(x, y, width, height, fill=grad, stroke="black", stroke_width=0.5)
        )
        self.drawing.append(
            draw.Text(f"{vmin:.2g}", font_size - 2, x, y + height + 12, text_anchor="start")
        )
        self.drawing.append(
            draw.Text(
                f"{vmax:.2g}", font_size - 2, x + width, y + height + 12, text_anchor="end"
            )
        )
