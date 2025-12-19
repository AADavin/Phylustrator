import drawsvg as draw
from dataclasses import dataclass
import math

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
