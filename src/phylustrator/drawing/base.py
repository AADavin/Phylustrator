import drawsvg as draw
from dataclasses import dataclass
from pathlib import Path
import math
import re
import os
import base64
from ..utils import to_hex, to_rgb, lerp_color, generate_id

try:
    import cairosvg
except ImportError:
    cairosvg = None

@dataclass
class TreeStyle:
    """
    Configuration object for visual styling parameters.

    Attributes:
        width (int): Total width of the SVG canvas.
        height (int): Total height of the SVG canvas.
        radius (int): Maximum radius for radial trees.
        degrees (int): Angular span for radial trees (usually 360).
        rotation (int): Global rotation offset for the layout.
        margin (float): Padding between the tree and the canvas edge.
        root_stub_length (float): Length of the line preceding the root node.
        leaf_r (float): Radius of markers at leaf tips.
        leaf_color (str): Default color for leaf markers.
        branch_stroke_width (float): Default thickness for tree branches.
        branch_color (str): Default color for tree branches.
        node_r (float): Radius of markers at internal nodes.
        font_size (int): Default size for text elements.
        font_family (str): Default font family for text elements.
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

class BaseDrawer:
    """
    Abstract base class providing shared UI and export functionality for all tree drawers.
    
    This class handles the initialization of the drawsvg Drawing object, coordinate 
    independency for UI elements (legends, titles), and high-resolution exports.
    """
    def __init__(self, tree, style=None):
        """
        Initializes the BaseDrawer.

        Args:
            tree (ete3.Tree): The tree object to render.
            style (TreeStyle, optional): Style configuration. Defaults to a standard TreeStyle.
        """
        self.t = tree
        self.style = style if style else TreeStyle()
        self.drawing = draw.Drawing(self.style.width, self.style.height, origin='center')
        self.drawing.append(draw.Rectangle(-self.style.width/2, -self.style.height/2, 
                                           self.style.width, self.style.height, fill="white"))
        
        # Notebook compatibility alias
        self.d = self.drawing
        
        self.total_tree_depth = 0
        self.sf = 1.0 
        self._layout_calculated = False

    def _pre_flight_check(self):
        """Internal helper to ensure layout math is performed before drawing elements."""
        if not self._layout_calculated:
            self._calculate_layout()
            self._layout_calculated = True

    def _calculate_layout(self):
        """Must be implemented by subclasses to set node positions."""
        raise NotImplementedError

    def _draw_shape_at(self, x, y, shape, fill, r, stroke=None, stroke_width=1.0, rotation=0, opacity=1.0):
        """
        Low-level helper to draw geometric markers on the canvas.

        Args:
            x (float): Cartesian X coordinate.
            y (float): Cartesian Y coordinate.
            shape (str): Shape type ('circle', 'square', 'triangle').
            fill (str): Fill color hex or name.
            r (float): Radius/Half-size of the shape.
            stroke (str, optional): Border color.
            stroke_width (float): Border thickness.
            rotation (float): Rotation in degrees.
            opacity (float): Transparency (0.0 to 1.0).
        """
        common = {"fill": fill, "opacity": opacity}
        if stroke:
            common["stroke"] = stroke
            common["stroke_width"] = stroke_width

        shp = str(shape).lower()
        transform = f"rotate({rotation},{x},{y})" if rotation != 0 else None

        if shp == "circle":
            self.drawing.append(draw.Circle(x, y, float(r), **common))
        elif shp == "square":
            side = float(r) * 2.0
            self.drawing.append(draw.Rectangle(x - r, y - r, side, side, transform=transform, **common))
        elif shp == "triangle":
            side = float(r) * 2.0
            h = side * math.sqrt(3) / 2.0
            p1, p2, p3 = (x, y - h*2/3), (x - side/2, y + h/3), (x + side/2, y + h/3)
            path = draw.Path(transform=transform, **common).M(*p1).L(*p2).L(*p3).Z()
            self.drawing.append(path)

    def save_svg(self, outpath, rotation=0):
        """
        Exports the current drawing to an SVG file.

        Args:
            outpath (str|Path): Path to save the file.
            rotation (float): Rotation to apply to the final exported group.
        """
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        svg_content = self._get_rotated_svg_content(rotation)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(svg_content)

    def save_png(self, outpath, dpi=300, scale=None, rotation=0):
        """
        Exports the current drawing to a high-resolution PNG file.

        Args:
            outpath (str|Path): Path to save the file.
            dpi (int): Target dots-per-inch for the export. Defaults to 300.
            scale (float, optional): Direct scaling factor. Overrides DPI if provided.
            rotation (float): Rotation to apply to the final export.
        """
        if cairosvg is None:
            raise ImportError("PNG export requires 'cairosvg'. Install via 'pip install phylustrator[export]'")
        
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        
        if scale is None:
            scale = dpi / 72.0
            
        svg_content = self._get_rotated_svg_content(rotation)
        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=str(outpath), scale=scale)

    def _get_rotated_svg_content(self, rotation):
        """Internal helper for generating rotated SVG markup."""
        if rotation == 0: return self.drawing.as_svg()
        original_svg = self.drawing.as_svg()
        original_svg = re.sub(r'<\?xml.*?\?>|<!DOCTYPE.*?>', '', original_svg)
        w, h = self.style.width, self.style.height
        rad = math.radians(rotation)
        new_w = abs(w * math.cos(rad)) + abs(h * math.sin(rad))
        new_h = abs(w * math.sin(rad)) + abs(h * math.cos(rad))
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{new_w}" height="{new_h}" viewBox="0 0 {new_w} {new_h}">\n'
            f'  <g transform="translate({new_w/2}, {new_h/2}) rotate({rotation}) translate({-w/2}, {-h/2})">\n'
            f'    {original_svg}\n'
            f'  </g>\n'
            f'</svg>'
        )

    def add_categorical_legend(self, palette, title="Legend", x=None, y=None, font_size=14, r=6):
        """
        Adds a categorical legend (colored dots with text) to the canvas.

        Args:
            palette (dict): Mapping of category names to color hex strings.
            title (str): Legend title.
            x (float, optional): X coordinate (Canvas center is 0,0). Defaults to top-left.
            y (float, optional): Y coordinate. Defaults to top-left.
            font_size (int): Text size for labels.
            r (float): Radius of the color dots.
        """
        if x is None: x = -self.style.width / 2 + 30
        if y is None: y = -self.style.height / 2 + 30
        
        self.drawing.append(draw.Text(title, font_size + 2, x, y, font_weight="bold", 
                                      font_family=self.style.font_family, text_anchor="start"))
        curr_y = y + font_size * 1.5
        for label, color in palette.items():
            self.drawing.append(draw.Circle(x + r, curr_y, r, fill=color))
            self.drawing.append(draw.Text(str(label), font_size, x + r*2.5, curr_y, 
                                          font_family=self.style.font_family, text_anchor="start", dominant_baseline="middle"))
            curr_y += font_size * 1.4

    def add_color_bar(self, low_color, high_color, vmin, vmax, title="", x=None, y=None, width=100, height=15, font_size=12):
        """
        Adds a continuous color gradient bar to the canvas.

        Args:
            low_color (str): Color hex for minimum value.
            high_color (str): Color hex for maximum value.
            vmin (float): Minimum value label.
            vmax (float): Maximum value label.
            title (str): Color bar title.
            x (float, optional): X coordinate. Defaults to bottom-left.
            y (float, optional): Y coordinate. Defaults to bottom-left.
            width (float): Width of the bar.
            height (float): Height of the bar.
            font_size (int): Text size for labels.
        """
        if x is None: x = -self.style.width / 2 + 30
        if y is None: y = self.style.height / 2 - 60
        gid = generate_id("cb_grad")
        grad = draw.LinearGradient(x, y, x + width, y, id=gid)
        grad.add_stop(0, low_color); grad.add_stop(1, high_color)
        self.drawing.append(grad)
        if title:
            self.drawing.append(draw.Text(title, font_size, x, y - 10, font_weight="bold", text_anchor="start"))
        self.drawing.append(draw.Rectangle(x, y, width, height, fill=grad, stroke="black", stroke_width=0.5))
        self.drawing.append(draw.Text(f"{vmin:.2g}", font_size - 2, x, y + height + 12, text_anchor="start"))
        self.drawing.append(draw.Text(f"{vmax:.2g}", font_size - 2, x + width, y + height + 12, text_anchor="end"))

    def add_title(self, text, font_size=24, position="top", pad=40.0, color="black", weight="bold"):
        """
        Adds a text title to a fixed position on the canvas.

        Args:
            text (str): Title text.
            font_size (int): Text size.
            position (str): 'top', 'bottom', 'left', or 'right'.
            pad (float): Padding from the canvas edge.
            color (str): Text color.
            weight (str): Font weight ('normal', 'bold').
        """
        w, h = self.style.width, self.style.height
        tx, ty = 0, 0
        if position == "top": ty = -h/2 + pad
        elif position == "bottom": ty = h/2 - pad
        elif position == "left": tx = -w/2 + pad
        elif position == "right": tx = w/2 - pad
        self.drawing.append(draw.Text(
            text, font_size, tx, ty, fill=color, font_weight=weight,
            font_family=self.style.font_family, text_anchor="middle", dominant_baseline="middle"
        ))

    def add_scale_bar(self, length, label=None, x=None, y=None, stroke="black", stroke_width=2.0):
        """
        Adds a physical scale bar representing evolutionary distance.

        Args:
            length (float): Length in tree distance units.
            label (str, optional): Label text. Defaults to length value.
            x (float, optional): X coordinate.
            y (float, optional): Y coordinate.
            stroke (str): Bar color.
            stroke_width (float): Bar thickness.
        """
        self._pre_flight_check()
        px = float(length) * self.sf
        label = label or str(length)
        x = x if x is not None else -self.style.width/2 + 20
        y = y if y is not None else self.style.height/2 - 20
        self.drawing.append(draw.Line(x, y, x + px, y, stroke=stroke, stroke_width=stroke_width))
        self.drawing.append(draw.Text(label, self.style.font_size, x + px/2, y - 8, 
                                      text_anchor="middle", font_family=self.style.font_family))
