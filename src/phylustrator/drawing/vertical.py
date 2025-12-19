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

    def plot_transfers(self, transfers, mode="midpoint", curve_type="C", filter_below=0.0, 
                       use_gradient=True, gradient_colors=("purple", "orange"),
                       color="orange", use_thickness=True, stroke_width=5,
                       arc_intensity=40, opacity=0.6):
        """
        Plots horizontal gene transfer events as curved lines.
        :param curve_type: "C" for a classic bulge (default), "S" for an S-shaped flow.
        :param arc_intensity: The 'strength' of the curve. For C-curves, positive values 
                              tuck the bulge toward the root.
        """
        name2node = {n.name: n for n in self.t.traverse()}

        # Ensure layout attributes exist (coordinates/y_coord live on nodes)
        any_node = next(self.t.traverse("preorder"))
        if not hasattr(any_node, "coordinates") or not hasattr(any_node, "y_coord"):
            self._calculate_layout()

        for tr in transfers:
            # 1. Filter by frequency
            freq = tr.get("freq", 1.0)
            if freq < filter_below:
                continue

            src, dst = name2node.get(tr["from"]), name2node.get(tr["to"])
            if not src or not dst:
                continue

            # 2. Calculate X-Coordinates (Preserves Midpoint vs. Time options)
            if mode == "time" and tr.get('time') is not None:
                x_start = self.root_x + (tr['time'] * self.sf)
                x_end = x_start
            else:
                src_px = src.up.coordinates[0] if src.up else src.coordinates[0] - 20
                dst_px = dst.up.coordinates[0] if dst.up else dst.coordinates[0] - 20
                x_start = (src_px + src.coordinates[0]) / 2
                x_end = (dst_px + dst.coordinates[0]) / 2

            # 3. Path styling
            width = (stroke_width * freq) if use_thickness else stroke_width
            path = draw.Path(stroke_width=width, fill="none", stroke_opacity=opacity)

            # 4. Color / Gradient Logic
            if use_gradient:
                grad_id = f"tr_grad_{random.randint(0, 999999)}"
                grad = draw.LinearGradient(x_start, src.y_coord, x_end, dst.y_coord, id=grad_id)
                grad.add_stop(0, gradient_colors[0]) 
                grad.add_stop(1, gradient_colors[1])
                self.d.append(grad)
                path.args["stroke"] = grad
            else:
                path.args["stroke"] = color

            # 5. Geometry Selection
            path.M(x_start, src.y_coord)
            
            if curve_type.upper() == "S":
                # S-Curve Logic: Control points pull in opposite directions
                dx = x_end - x_start
                sgn = 1 if dx >= 0 else -1
                arc = abs(arc_intensity)
                cp1x = x_start + (sgn * arc)
                cp2x = x_end - (sgn * arc)
                path.C(cp1x, src.y_coord, cp2x, dst.y_coord, x_end, dst.y_coord)
            
            else:
                # C-Curve Logic: Both points pull in the same direction
                # Using '- arc_intensity' here so that positive values 'tuck' toward root
                path.C(x_start - arc_intensity, src.y_coord, 
                       x_end - arc_intensity, dst.y_coord, 
                       x_end, dst.y_coord)

            self.d.append(path)
    
    def add_transfer_legend(
        self,
        title="Transfer Frequency",
        colors=("purple", "orange"),
        low=0.1,
        high=1.0,
        source_label="Source",
        arrival_label="Arrival",
        show_frequency=False,
        show_direction=True,
        margin=20,
    ):
        """Add a transfer legend.

        By default this shows *direction* (two solid colors): a "Source" swatch and an
        "Arrival" swatch. If you also want a frequency scale, set
        ``show_frequency=True``.

        Parameters
        ----------
        colors:
            Tuple (source_color, arrival_color). These match the gradient endpoints
            used by ``plot_transfers(..., gradient_colors=...)``.
        show_frequency:
            Draws a gradient bar + numeric low/high labels.
        show_direction:
            Draws two solid color swatches labelled source/arrival.
        """
        if not (show_frequency or show_direction):
            return

        font_size = 11
        num_font_size = 9
        sw = 14
        gap = 6
        pad_x = 10
        top_pad = 10
        bottom_pad = 10
        row_h = 18
        bar_h = 12
        bar_w = 110

        # Estimate legend width from label lengths (drawsvg doesn't expose text metrics).
        max_label_len = 0
        if show_direction:
            max_label_len = max(len(str(source_label)), len(str(arrival_label)))
        if show_frequency:
            max_label_len = max(max_label_len, len(str(title)))
        est_text_w = max_label_len * font_size * 0.60
        w = int(pad_x + sw + gap + est_text_w + pad_x)
        if show_frequency:
            w = max(w, pad_x + bar_w + pad_x)

        # Height: SVG y-axis increases downward.
        content_h = top_pad
        if show_frequency:
            # title + bar + low/high labels + spacing
            content_h += (font_size + 4) + bar_h + (num_font_size + 10) + 6
        if show_direction:
            content_h += (2 * row_h)
        content_h += bottom_pad
        box_h = content_h

        x = -self.style.width / 2 + 30
        y = self.style.height / 2 - margin - box_h

        self.d.append(draw.Rectangle(x, y, w, box_h, fill="white", stroke="black", stroke_width=1, opacity=0.9))

        cursor_y = y + top_pad + 2

        if show_frequency:
            self.d.append(draw.Text(title, font_size, x + 10, cursor_y, font_family="sans-serif", font_weight="bold"))
            cursor_y += 10

            grad_id = f"legend_transfer_grad_{random.randint(0, 999999)}"
            grad = draw.LinearGradient(x + 10, cursor_y + bar_h / 2, x + 10 + bar_w, cursor_y + bar_h / 2, id=grad_id)
            grad.add_stop(0, colors[0])
            grad.add_stop(1, colors[1])
            self.d.append(grad)
            self.d.append(draw.Rectangle(x + 10, cursor_y, bar_w, bar_h, fill=grad))

            self.d.append(draw.Text(f"{low}", num_font_size, x + 10, cursor_y + bar_h + 12, font_family="sans-serif"))
            self.d.append(draw.Text(f"{high}", num_font_size, x + 10 + bar_w - 15, cursor_y + bar_h + 12, font_family="sans-serif"))
            cursor_y += bar_h + 24

        if show_direction:
            sw = 14
            self.d.append(draw.Rectangle(x + 10, cursor_y, sw, sw, fill=colors[0]))
            self.d.append(draw.Text(source_label, font_size, x + 30, cursor_y + 11, font_family="sans-serif"))
            cursor_y += row_h

            self.d.append(draw.Rectangle(x + 10, cursor_y, sw, sw, fill=colors[1]))
            self.d.append(draw.Text(arrival_label, 11, x + 30, cursor_y + 11, font_family="sans-serif"))