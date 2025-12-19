import drawsvg as draw
from .base import BaseDrawer
import random

class VerticalTreeDrawer(BaseDrawer):
    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_layout()

    def _calculate_layout(self):
        max_dist = 0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            if n.dist_to_root > max_dist: max_dist = n.dist_to_root
        
        self.total_tree_depth = max_dist
        self.sf = (self.style.width - 250) / max_dist if max_dist > 0 else 1
        self.root_x = -self.style.width / 2 + 50

        leaves = self.t.get_leaves()
        y_step = (self.style.height - 100) / max(len(leaves)-1, 1)
        start_y = -self.style.height / 2 + 50

        for i, leaf in enumerate(leaves):
            leaf.y_coord = start_y + (i * y_step)
            leaf.coordinates = (self.root_x + (leaf.dist_to_root * self.sf), leaf.y_coord)

        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                n.y_coord = sum(c.y_coord for c in n.children) / len(n.children)
                n.coordinates = (self.root_x + (n.dist_to_root * self.sf), n.y_coord)

    def draw(self):
        for n in self.t.traverse("postorder"):
            x, y = n.coordinates
            if not n.is_root():
                px, py = n.up.coordinates
                self.d.append(draw.Line(px, y, x, y, stroke=self.style.branch_color, stroke_width=self.style.branch_size, stroke_linecap="round"))
            else:
                self.d.append(draw.Line(x - 20, y, x, y, stroke=self.style.branch_color, stroke_width=self.style.branch_size))
            if not n.is_leaf():
                y_min, y_max = min(c.y_coord for c in n.children), max(c.y_coord for c in n.children)
                self.d.append(draw.Line(x, y_min, x, y_max, stroke=self.style.branch_color, stroke_width=self.style.branch_size, stroke_linecap="round"))
                self.d.append(draw.Circle(x, y, self.style.node_size, fill=self.style.branch_color))
            else:
                self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))

    def highlight_clade(self, node, color="lightblue", opacity=0.3, padding=10):
        leaves = node.get_leaves()
        x_start, _ = node.coordinates
        x_max = max(l.coordinates[0] for l in leaves)
        y_min, y_max = min(l.y_coord for l in leaves), max(l.y_coord for l in leaves)
        rect_y = y_min - padding
        self.d.append(draw.Rectangle(x_start-padding, rect_y, (x_max-x_start)+padding+50, (y_max-y_min)+2*padding, fill=color, fill_opacity=opacity))

    def gradient_branch(self, node, colors=("red", "blue")):
        if node.is_root(): return
        x, y = node.coordinates
        px, _ = node.up.coordinates
        grad_id = f"grad_{random.randint(0,9999)}"
        grad = draw.LinearGradient(px, y, x, y, id=grad_id)
        grad.add_stop(0, colors[0]).add_stop(1, colors[1])
        self.d.append(grad)
        self.d.append(draw.Line(px, y, x, y, stroke=grad, stroke_width=self.style.branch_size))

    def mark_events(self, events, type_filter=None, shape="circle", color="red", size=5):
        name2node = {n.name: n for n in self.t.traverse()}
        for ev in events:
            if type_filter and ev.get('type') != type_filter: continue
            node = name2node.get(ev.get('node'))
            if not node: continue
            x = self.root_x + (ev['time'] * self.sf) if ev.get('time') is not None else (node.up.coordinates[0]+node.coordinates[0])/2
            y = node.y_coord
            if shape == "circle": self.d.append(draw.Circle(x, y, size, fill=color))
            elif shape == "square": self.d.append(draw.Rectangle(x-size, y-size, size*2, size*2, fill=color))
            elif shape == "x":
                p = draw.Path(stroke=color, stroke_width=2).M(x-size, y-size).L(x+size, y+size).M(x-size, y+size).L(x+size, y-size)
                self.d.append(p)

    def add_transfer_links(self, transfers, color="orange", curve_factor=0.3, arrows=True):
        name2node = {n.name: n for n in self.t.traverse()}
        for tr in transfers:
            src, dst = name2node.get(tr['from']), name2node.get(tr['to'])
            if not src or not dst: continue
            x = self.root_x + (tr['time'] * self.sf)
            path = draw.Path(stroke=color, stroke_width=2, fill="none", stroke_opacity=0.6)
            path.M(x, src.y_coord).C(x+50, src.y_coord, x+50, dst.y_coord, x, dst.y_coord)
            if arrows:
                marker = draw.Marker(9, 5, 2, 2, scale=2, orient="auto")
                marker.append(draw.Path("M 0 0 L 10 5 L 0 10 z", fill=color))
                self.d.append(marker)
                path.args['marker_end'] = marker
            self.d.append(path)

    def add_leaf_names(self, padding=10):
        for l in self.t.get_leaves():
            x, y = l.coordinates
            self.d.append(draw.Text(l.name, self.style.font_size, x+padding, y+self.style.font_size/3))
