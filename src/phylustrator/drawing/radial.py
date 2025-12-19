import drawsvg as draw
import math
import random
from .base import BaseDrawer

def radial_converter(degree, radius, rotation=0):
    theta = math.radians(degree + rotation)
    return radius * math.cos(theta), radius * math.sin(theta)

class RadialTreeDrawer(BaseDrawer):
    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_layout()

    def _calculate_layout(self):
        max_dist = 0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            max_dist = max(max_dist, n.dist_to_root)
        self.total_tree_depth = max_dist
        self.sf = self.style.radius / max_dist if max_dist > 0 else 1
        leaves = self.t.get_leaves()
        self.angle_step = self.style.degrees / len(leaves)
        for i, leaf in enumerate(leaves):
            leaf.angle = i * self.angle_step
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                n.angle = (n.children[0].angle + n.children[-1].angle) / 2
            n.rad = n.dist_to_root * self.sf
            n.xy = radial_converter(n.angle, n.rad, self.style.rotation)

    def draw(self):
        for n in self.t.traverse("postorder"):
            x, y = n.xy
            if not n.is_root():
                px, py = radial_converter(n.angle, n.up.rad, self.style.rotation)
                self.d.append(draw.Line(px, py, x, y, stroke=self.style.branch_color, stroke_width=self.style.branch_size))
            if not n.is_leaf():
                a1, a2 = n.children[0].angle, n.children[-1].angle
                p = draw.Path(stroke=self.style.branch_color, stroke_width=self.style.branch_size, fill="none")
                sx, sy = radial_converter(a1, n.rad, self.style.rotation)
                ex, ey = radial_converter(a2, n.rad, self.style.rotation)
                p.M(sx, sy).A(n.rad, n.rad, 0, 0, 1, ex, ey)
                self.d.append(p)
            else:
                self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))

    def add_ring(self, mapping, width=20, padding=10):
        r_in = self.style.radius + padding
        r_out = r_in + width
        for l in self.t.get_leaves():
            if l.name not in mapping: continue
            a1, a2 = l.angle - self.angle_step/2, l.angle + self.angle_step/2
            p = draw.Path(fill=mapping[l.name])
            s_i_x, s_i_y = radial_converter(a1, r_in, self.style.rotation)
            e_i_x, e_i_y = radial_converter(a2, r_in, self.style.rotation)
            s_o_x, s_o_y = radial_converter(a1, r_out, self.style.rotation)
            e_o_x, e_o_y = radial_converter(a2, r_out, self.style.rotation)
            p.M(s_o_x, s_o_y).A(r_out, r_out, 0, 0, 1, e_o_x, e_o_y).L(e_i_x, e_i_y).A(r_in, r_in, 0, 0, 0, s_i_x, s_i_y).Z()
            self.d.append(p)
            
    def add_leaf_names(self, padding=15):
        for l in self.t.get_leaves():
            angle = l.angle + self.style.rotation
            x, y = radial_converter(l.angle, self.style.radius + padding, self.style.rotation)
            rot = angle if -90 <= (angle % 360) <= 90 else angle - 180
            anchor = "start" if -90 <= (angle % 360) <= 90 else "end"
            self.d.append(draw.Text(l.name, self.style.font_size, x, y, transform=f"rotate({rot},{x},{y})", text_anchor=anchor))
