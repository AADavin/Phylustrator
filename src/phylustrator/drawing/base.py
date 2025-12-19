import drawsvg as draw
from dataclasses import dataclass
import math
import random

@dataclass
class TreeStyle:
    width: int = 1000
    height: int = 1000
    radius: int = 400
    degrees: int = 360
    rotation: int = -90
    leaf_size: int = 5
    leaf_color: str = "black"
    branch_size: int = 2
    branch_color: str = "black"
    node_size: int = 2
    font_size: int = 12
    font_family: str = "Arial"

class BaseDrawer:
    def __init__(self, tree, style=None):
        self.t = tree
        self.style = style if style else TreeStyle()
        self.d = draw.Drawing(self.style.width, self.style.height, origin='center')
        self.d.append(draw.Rectangle(-self.style.width/2, -self.style.height/2, 
                                     self.style.width, self.style.height, fill="white"))
        self.total_tree_depth = 0
        self.sf = 1.0 

    def save_figure(self, filename, scale=4.0):
        if filename.endswith(".svg"):
            self.d.save_svg(filename)
        else:
            import cairosvg
            svg_data = self.d.as_svg()
            if filename.endswith(".png"):
                cairosvg.svg2png(bytestring=svg_data, write_to=filename, scale=scale)
            elif filename.endswith(".pdf"):
                cairosvg.svg2pdf(bytestring=svg_data, write_to=filename)

    def add_scale_bar(self, length=None, label=None, x=None, y=None):
        if length is None:
            target = self.total_tree_depth * 0.1
            exponent = math.floor(math.log10(target)) if target > 0 else 0
            length = round(target, -exponent)
        px_length = length * self.sf
        label = label if label else f"{length}"
        x = x if x is not None else -self.style.width / 2 + 50
        y = y if y is not None else self.style.height / 2 - 50
        self.d.append(draw.Line(x, y, x + px_length, y, stroke="black", stroke_width=2))
        self.d.append(draw.Text(label, 12, x + (px_length / 2), y + 20, text_anchor="middle"))
