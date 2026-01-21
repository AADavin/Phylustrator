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
    Abstract base class providing shared UI and export functionality.
    """
    def __init__(self, tree, style=None):
        self.t = tree
        self.style = style if style else TreeStyle()
        self.drawing = draw.Drawing(self.style.width, self.style.height, origin='center')
        self.drawing.append(draw.Rectangle(-self.style.width/2, -self.style.height/2, 
                                           self.style.width, self.style.height, fill="white"))
        self.d = self.drawing
        self.total_tree_depth = 0
        self.sf = 1.0 
        self._layout_calculated = False

    def _pre_flight_check(self):
        if not self._layout_calculated:
            self._calculate_layout()
            self._layout_calculated = True

    def _calculate_layout(self):
        raise NotImplementedError

    def _draw_shape_at(self, x, y, shape, fill, r, stroke=None, stroke_width=1.0, rotation=0, opacity=1.0):
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

    def add_title(self, text, font_size=24, position="top", pad=40.0, color="black", weight="bold"):
        """Adds a title text to the drawing at a fixed position."""
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

    def add_text(self, text, x, y, font_size=12, color="black", weight="normal", text_anchor="start", dominant_baseline="middle", rotation=0):
        """Adds text at any Cartesian (x, y) coordinate."""
        transform = f"rotate({rotation}, {x}, {y})" if rotation != 0 else None
        self.drawing.append(draw.Text(
            text, font_size, x, y, fill=color, font_weight=weight,
            font_family=self.style.font_family, text_anchor=text_anchor, 
            dominant_baseline=dominant_baseline, transform=transform
        ))

    def save_svg(self, outpath, rotation=0):
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        svg_content = self._get_rotated_svg_content(rotation)
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(svg_content)

    def save_png(self, outpath, dpi=300, scale=None, rotation=0):
        if cairosvg is None:
            raise ImportError("PNG export requires 'cairosvg'.")
        self._pre_flight_check()
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        if scale is None: scale = dpi / 72.0
        svg_content = self._get_rotated_svg_content(rotation)
        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=str(outpath), scale=scale)

    def _get_rotated_svg_content(self, rotation):
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
