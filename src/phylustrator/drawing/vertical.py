import drawsvg as draw
from .base import BaseDrawer
import random

class VerticalTreeDrawer(BaseDrawer):
    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_layout()

    def _calculate_layout(self):
        # 1. Calculate Distances
        max_dist = 0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            if n.dist_to_root > max_dist: max_dist = n.dist_to_root
        
        self.total_tree_depth = max_dist
        
        # Padding for labels and centering
        horizontal_padding = 100 
        self.sf = (self.style.width - (horizontal_padding * 2)) / max_dist if max_dist > 0 else 1
        
        # Center the root X based on padding
        self.root_x = -self.style.width / 2 + horizontal_padding

        # 2. Calculate Vertical Positions
        leaves = self.t.get_leaves()
        y_padding = 100
        y_step = (self.style.height - (y_padding * 2)) / max(len(leaves)-1, 1)
        start_y = -self.style.height / 2 + y_padding

        for i, leaf in enumerate(leaves):
            leaf.y_coord = start_y + (i * y_step)
            leaf.coordinates = (self.root_x + (leaf.dist_to_root * self.sf), leaf.y_coord)

        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                n.y_coord = sum(c.y_coord for c in n.children) / len(n.children)
                n.coordinates = (self.root_x + (n.dist_to_root * self.sf), n.y_coord)

    def draw(self, branch2color=None):
        """Draws the tree. Accepts branch2color dict {node: color_string}."""
        for n in self.t.traverse("postorder"):
            x, y = n.coordinates
            
            # Resolve Color
            color = self.style.branch_color
            if branch2color and n in branch2color:
                color = branch2color[n]

            # 1. Horizontal branch
            if not n.is_root():
                px, py = n.up.coordinates
                self.d.append(draw.Line(px, y, x, y, stroke=color, 
                                        stroke_width=self.style.branch_size, stroke_linecap="round"))
            else:
                self.d.append(draw.Line(x - 20, y, x, y, stroke=color, stroke_width=self.style.branch_size))

            # 2. Vertical connector
            if not n.is_leaf():
                y_min, y_max = min(c.y_coord for c in n.children), max(c.y_coord for c in n.children)
                self.d.append(draw.Line(x, y_min, x, y_max, stroke=color, 
                                        stroke_width=self.style.branch_size, stroke_linecap="round"))
                self.d.append(draw.Circle(x, y, self.style.node_size, fill=color))
            else:
                self.d.append(draw.Circle(x, y, self.style.leaf_size, fill=self.style.leaf_color))

    def highlight_clade(self, node, color="lightblue", opacity=0.3, padding=10):
        """
        Draws a shaded rectangle behind a specific clade.
        """
        leaves = node.get_leaves()
        
        # Calculate bounds based on node and leaf coordinates
        x_start, _ = node.coordinates
        
        # X range: From node to the furthest tip in this clade
        x_max = max(l.coordinates[0] for l in leaves)
        
        # Y range: Spanning all leaves in the clade
        y_min = min(l.y_coord for l in leaves)
        y_max = max(l.y_coord for l in leaves)
        
        # Geometry: 
        # width is (x_max - x_start) + a small padding for the tips
        # height is (y_max - y_min) + padding on top/bottom
        rect_x = x_start - (padding / 2)
        rect_y = y_min - padding
        rect_w = (x_max - x_start) + padding # Reduced the "60" extension to just padding
        rect_h = (y_max - y_min) + (2 * padding)
        
        self.d.append(draw.Rectangle(
            rect_x, rect_y, rect_w, rect_h, 
            fill=color, 
            fill_opacity=opacity,
            stroke="none"
        ))

    def highlight_branch(self, node, color="red", size=None):
        if node.is_root(): return
        s_width = size if size else self.style.branch_size * 2
        x, y = node.coordinates
        px, py = node.up.coordinates
        self.d.append(draw.Line(px, y, x, y, stroke=color, stroke_width=s_width, stroke_linecap="round"))

    def gradient_branch(self, node, colors=("red", "blue"), size=None):
        if node.is_root(): return
        s_width = size if size else self.style.branch_size
        x, y = node.coordinates
        px, _ = node.up.coordinates
        grad_id = f"grad_{random.randint(0,9999)}"
        grad = draw.LinearGradient(px, y, x, y, id=grad_id)
        grad.add_stop(0, colors[0]).add_stop(1, colors[1])
        self.d.append(grad)
        self.d.append(draw.Line(px, y, x, y, stroke=grad, stroke_width=s_width))

    def add_leaf_names(self, padding=10):
        for l in self.t.get_leaves():
            x, y = l.coordinates
            self.d.append(draw.Text(l.name, self.style.font_size, x+padding, y+self.style.font_size/3))

    def mark_events(self, events, type_filter=None, shape="circle", color="red", size=5):
        name2node = {n.name: n for n in self.t.traverse()}
        for ev in events:
            if type_filter and ev.get('type') != type_filter: continue
            node = name2node.get(ev.get('node'))
            if not node: continue
            
            # Support both Zombi (time) and midpoint logic
            if ev.get('time') is not None:
                x = self.root_x + (ev['time'] * self.sf)
            else:
                x = (node.up.coordinates[0] + node.coordinates[0]) / 2
                
            y = node.y_coord
            if shape == "circle": self.d.append(draw.Circle(x, y, size, fill=color))
            elif shape == "square": self.d.append(draw.Rectangle(x-size, y-size, size*2, size*2, fill=color))
            elif shape == "x":
                p = draw.Path(stroke=color, stroke_width=2).M(x-size, y-size).L(x+size, y+size).M(x-size, y+size).L(x+size, y-size)
                self.d.append(p)

    def add_transfer_links(self, transfers, gradient_colors=("purple", "orange"), stroke_width=2, arrows=True):
        name2node = {n.name: n for n in self.t.traverse()}
        for tr in transfers:
            src, dst = name2node.get(tr['from']), name2node.get(tr['to'])
            if not src or not dst: continue
            
            x = self.root_x + (tr['time'] * self.sf)
            path = draw.Path(stroke_width=stroke_width, fill="none", stroke_opacity=0.6)
            
            if gradient_colors:
                grad_id = f"tr_{random.randint(0,9999)}"
                grad = draw.LinearGradient(x, src.y_coord, x, dst.y_coord, id=grad_id)
                grad.add_stop(0, gradient_colors[0]).add_stop(1, gradient_colors[1])
                self.d.append(grad)
                path.args['stroke'] = grad
            else:
                path.args['stroke'] = "orange"

            path.M(x, src.y_coord).C(x+50, src.y_coord, x+50, dst.y_coord, x, dst.y_coord)
            if arrows:
                marker = draw.Marker(9, 5, 2, 2, scale=2, orient="auto")
                marker.append(draw.Path("M 0 0 L 10 5 L 0 10 z", fill=gradient_colors[1] if gradient_colors else "orange"))
                self.d.append(marker)
                path.args['marker_end'] = marker
            self.d.append(path)
