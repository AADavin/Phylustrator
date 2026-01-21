import drawsvg as draw
from .base import BaseDrawer
from ..utils import to_hex, lerp_color, generate_id
import math
import random
import os
import base64

class VerticalTreeDrawer(BaseDrawer):
    """
    Drawer class for rendering phylogenetic trees in a rectangular vertical layout.
    """
    def __init__(self, tree, style=None):
        """
        Initializes the VerticalTreeDrawer.

        Args:
            tree (ete3.Tree): The tree to be drawn.
            style (TreeStyle, optional): Visual styling parameters.
        """
        super().__init__(tree, style)
        self._calculate_layout()

    def _node_xy(self, node) -> tuple[float, float]:
        """Calculates Cartesian (x, y) coordinates for a node."""
        if not hasattr(node, "coordinates"):
            self._calculate_layout()
        x, y = node.coordinates
        return float(x), float(y)

    def _leaf_xy(self, leaf, offset: float = 0.0) -> tuple[float, float]:
        """Calculates coordinates for a leaf tip, with an optional horizontal offset."""
        x, y = self._node_xy(leaf)
        return (x + float(offset), y)

    def _edge_point(self, child, where: float) -> tuple[float, float, float]:
        """Finds a point along the horizontal part of the rectangular edge."""
        parent = child.up
        if parent is None:
            return (*self._node_xy(child), 0.0)
        x_p, _ = self._node_xy(parent)
        x_c, y_c = self._node_xy(child)
        t = max(0.0, min(1.0, float(where)))
        # Horizontal segment: x moves, y stays at child y
        return x_p + (x_c - x_p) * t, y_c, (0.0 if (x_c - x_p) >= 0 else 180.0)

    def _calculate_layout(self, max_width: float | None = None):
        """Calculates rectangular positions using TreeStyle margins."""
        max_dist = 0.0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            max_dist = max(max_dist, n.dist_to_root)
        
        self.total_tree_depth = max_dist
        pad = self.style.margin
        target_w = max_width if max_width is not None else self.style.width
        self.sf = (target_w - (pad * 2)) / max_dist if max_dist > 0 else 1.0
        self.root_x = -self.style.width / 2 + pad

        leaves = self.t.get_leaves()
        y_step = (self.style.height - (pad * 2)) / max(len(leaves)-1, 1)
        start_y = -self.style.height / 2 + pad

        for i, leaf in enumerate(leaves):
            leaf.y_coord = start_y + (i * y_step)
            leaf.coordinates = (self.root_x + (leaf.dist_to_root * self.sf), leaf.y_coord)

        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                n.y_coord = sum(c.y_coord for c in n.children) / len(n.children)
                n.coordinates = (self.root_x + (n.dist_to_root * self.sf), n.y_coord)
        self._layout_calculated = True

    def draw(self, branch2color=None, right_margin=0):
        """Draws the phylogenetic tree using rectangular elbows."""
        self._pre_flight_check()
        if right_margin > 0:
            self._calculate_layout(max_width=self.style.width - right_margin)

        for n in self.t.traverse("postorder"):
            x, y = n.coordinates
            color = branch2color.get(n, self.style.branch_color) if branch2color else self.style.branch_color

            if not n.is_root():
                px, py = n.up.coordinates
                # Horizontal segment
                self.drawing.append(draw.Line(px, y, x, y, stroke=color, 
                                              stroke_width=self.style.branch_stroke_width, stroke_linecap="round"))
            else:
                # Root stub
                self.drawing.append(draw.Line(x - self.style.root_stub_length, y, x, y, 
                                              stroke=color, stroke_width=self.style.branch_stroke_width))

            if not n.is_leaf():
                # Vertical connector
                y_min = min(c.y_coord for c in n.children)
                y_max = max(c.y_coord for c in n.children)
                self.drawing.append(draw.Line(x, y_min, x, y_max, stroke=color, 
                                              stroke_width=self.style.branch_stroke_width, stroke_linecap="round"))
                self.drawing.append(draw.Circle(x, y, self.style.node_r, fill=color))
            else:
                self.drawing.append(draw.Circle(x, y, self.style.leaf_r, fill=self.style.leaf_color))

    def highlight_clade(self, node, color="lightblue", opacity=0.3, padding=10):
        """Draws a shaded rectangle behind a specific clade."""
        self._pre_flight_check()
        leaves = node.get_leaves()
        x_start, _ = node.coordinates
        x_max = max(l.coordinates[0] for l in leaves)
        y_min = min(l.y_coord for l in leaves)
        y_max = max(l.y_coord for l in leaves)
        self.drawing.append(draw.Rectangle(
            x_start - (padding / 2), y_min - padding, 
            (x_max - x_start) + padding, (y_max - y_min) + (2 * padding),
            fill=color, fill_opacity=opacity, stroke="none"
        ))

    def highlight_branch(self, node, color="red", stroke_width=None):
        """Highlights a specific branch."""
        if node.is_root():
            return
        sw = stroke_width if stroke_width is not None else self.style.branch_stroke_width * 2
        x, y = node.coordinates
        px, _ = node.up.coordinates
        self.drawing.append(draw.Line(px, y, x, y, stroke=color, stroke_width=sw, stroke_linecap="round"))

    def gradient_branch(self, node, colors=("red", "blue"), stroke_width=None):
        """Applies a color gradient to a branch."""
        if node.is_root():
            return
        sw = stroke_width if stroke_width is not None else self.style.branch_stroke_width
        x, y, (px, _) = *node.coordinates, node.up.coordinates
        gid = generate_id("grad")
        grad = draw.LinearGradient(px, y, x, y, id=gid)
        grad.add_stop(0, colors[0])
        grad.add_stop(1, colors[1])
        self.drawing.append(grad)
        self.drawing.append(draw.Line(px, y, x, y, stroke=grad, stroke_width=sw))

    def add_leaf_names(self, font_size=None, color="black", rotation=0, padding=10):
        """Adds text labels to leaf tips."""
        fs = font_size or self.style.font_size
        for l in self.t.get_leaves():
            x, y = l.coordinates
            tx, ty = x + padding, y
            transform = f"rotate({rotation}, {tx}, {ty})" if rotation != 0 else ""
            self.drawing.append(draw.Text(l.name, fs, tx, ty, fill=color, font_family=self.style.font_family,
                                          transform=transform, text_anchor="start", dominant_baseline="middle"))

    def add_node_names(self, font_size=None, color="gray", x_offset=-15, y_offset=-10, rotation=0):
        """Adds text labels to internal nodes."""
        fs = font_size or self.style.font_size * 0.8
        for n in self.t.traverse():
            if not n.is_leaf() and n.name:
                x, y = n.coordinates
                tx, ty = x + x_offset, y + y_offset
                transform = f"rotate({rotation}, {tx}, {ty})" if rotation != 0 else ""
                self.drawing.append(draw.Text(
                    n.name, fs, tx, ty, fill=color, font_family=self.style.font_family,
                    transform=transform, text_anchor="middle", dominant_baseline="middle"
                ))

    def add_leaf_shapes(self, leaves, shape="circle", fill="blue", r=5.0, stroke=None, stroke_width=1.0, offset=0.0, rotation=0.0, opacity=1.0):
        """Adds geometric shapes next to leaf tips."""
        self._pre_flight_check()
        for item in leaves:
            try:
                node = self.t & item if isinstance(item, str) else item
                x, y = self._leaf_xy(node, offset=float(offset))
                self._draw_shape_at(x, y, shape, fill, r, stroke, stroke_width, rotation, opacity)
            except: continue

    def add_node_shapes(self, nodes, shape="circle", fill="red", r=5.0, stroke=None, stroke_width=1.0, rotation=0, dx=0, dy=0):
        """Adds geometric shapes at node positions."""
        self._pre_flight_check()
        if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict):
            for s in nodes:
                self.add_node_shapes([s.get("node")], s.get("shape", shape), s.get("fill", fill), s.get("r", r), 
                                     s.get("stroke", stroke), s.get("stroke_width", stroke_width), s.get("rotation", rotation))
            return
        for item in nodes:
            try:
                node = self.t.search_nodes(name=item)[0] if isinstance(item, str) else item
                x, y = self._node_xy(node)
                self._draw_shape_at(x + dx, y + dy, shape, fill, r, stroke, stroke_width, rotation)
            except: continue

    def add_branch_shapes(self, specs, default_where=0.5, offset=0.0, orient=None):
        """Adds geometric shapes along branches."""
        self._pre_flight_check()
        if hasattr(specs, "to_dict"): specs = specs.to_dict(orient="records")
        for s in specs:
            br = s.get("branch")
            if not br: continue
            try:
                node = self.t & br if isinstance(br, str) else br
                where = s.get("where", default_where)
                x, y, ang = self._edge_point(node, where=where)
                if offset != 0:
                    perp = math.radians(ang + 90)
                    x += offset * math.cos(perp)
                    y += offset * math.sin(perp)
                rot = s.get("rotation", 0.0)
                if orient == "along": rot = ang
                elif orient == "perp": rot = ang + 90
                r_val = float(s.get("r", s.get("size", 10.0) / 2.0))
                self._draw_shape_at(x, y, s.get("shape", "circle"), s.get("fill", "blue"), r_val, 
                                    s.get("stroke"), s.get("stroke_width", 1.0), rot, s.get("opacity", 1.0))
            except: continue

    def add_time_axis(self, ticks, label="Time", tick_size=6.0, padding=20.0, y_offset=0.0, stroke_width=2.0, grid=False):
        """Adds a linear time axis at the bottom."""
        self._pre_flight_check()
        leaves = self.t.get_leaves()
        min_y, max_y = min(l.y_coord for l in leaves), max(l.y_coord for l in leaves)
        y_axis = max_y + padding + y_offset
        x_left, x_right = self.root_x - self.style.root_stub_length, self.root_x + (max(ticks) * self.sf)
        self.drawing.append(draw.Line(x_left, y_axis, x_right, y_axis, stroke="black", stroke_width=stroke_width))
        for tt in ticks:
            x = self.root_x + tt * self.sf
            if grid:
                self.drawing.append(draw.Line(x, min_y, x, max_y, stroke="#ccc", stroke_width=1.0, stroke_opacity=0.5))
            self.drawing.append(draw.Line(x, y_axis, x, y_axis + tick_size, stroke="black", stroke_width=stroke_width))
            self.drawing.append(draw.Text(str(tt), self.style.font_size, x, y_axis + tick_size + self.style.font_size, center=True))
        self.drawing.append(draw.Text(label, self.style.font_size, (x_left + x_right) / 2.0, y_axis + tick_size + self.style.font_size * 2.5, center=True))

    def plot_transfers(
        self,
        transfers,
        mode="midpoint",
        curve_type="C",
        filter_below=0.0,
        use_gradient=True,
        gradient_colors=("purple", "orange"),
        color="orange",
        stroke_width=5.0,
        arc_intensity=40.0,
        opacity=0.6,
    ):
        """Plots curved arrows for Horizontal Gene Transfers."""
        if hasattr(transfers, "to_dict") and hasattr(transfers, "columns"):
            transfers = transfers.to_dict(orient="records")
        name2node = {n.name: n for n in self.t.traverse()}
        self._pre_flight_check()

        def get_where(node, t_ev):
            p = node.up
            if not p:
                return 0.0
            t0, t1 = float(getattr(p, "time_from_origin", 0.0)), float(getattr(node, "time_from_origin", 0.0))
            if abs(t1 - t0) > 1e-12:
                return max(0.0, min(1.0, (float(t_ev) - t0) / (t1 - t0)))
            return 0.5

        for tr in transfers:
            freq = float(tr.get("freq", 1.0))
            if freq < filter_below:
                continue
            src, dst = name2node.get(tr.get("from")), name2node.get(tr.get("to"))
            if not src or not dst:
                continue
            if mode == "time" and "time" in tr:
                x_s, y_s, _ = self._edge_point(src, get_where(src, tr["time"]))
                x_e, y_e, _ = self._edge_point(dst, get_where(dst, tr["time"]))
            else:
                x_s, y_s, _ = self._edge_point(src, 0.5)
                x_e, y_e, _ = self._edge_point(dst, 0.5)
            
            path = draw.Path(stroke_width=stroke_width * freq, fill="none", stroke_opacity=opacity)
            if use_gradient:
                gid = generate_id("tr_grad")
                grad = draw.LinearGradient(x_s, y_s, x_e, y_e, id=gid)
                grad.add_stop(0, gradient_colors[0])
                grad.add_stop(1, gradient_colors[1])
                self.drawing.append(grad)
                path.args["stroke"] = grad
            else:
                path.args["stroke"] = color
            
            path.M(x_s, y_s)
            if curve_type.upper() == "S":
                sgn = 1 if (x_e - x_s) >= 0 else -1
                path.C(x_s + (sgn * arc_intensity), y_s, x_e - (sgn * arc_intensity), y_e, x_e, y_e)
            else:
                path.C(x_s - arc_intensity, y_s, x_e - arc_intensity, y_e, x_e, y_e)
            self.drawing.append(path)

    def add_heatmap(self, values, width=15.0, offset=10.0, low_color="#f7fbff", high_color="#08306b", border_color="none", border_width=0.5):
        """Adds a rectangular heatmap next to tips."""
        if hasattr(values, "to_dict"):
            values = values.to_dict()
        vals = [float(v) for v in values.values() if isinstance(v, (int, float))]
        if not vals:
            return
        vmin, vmax = min(vals), max(vals) + 1e-12
        max_x = max(l.coordinates[0] for l in self.t.get_leaves())
        y_step = (self.style.height - 200) / max(len(self.t.get_leaves())-1, 1)
        for l in self.t.get_leaves():
            val = values.get(l.name)
            fill = lerp_color(low_color, high_color, (float(val) - vmin) / (vmax - vmin)) if val is not None else "white"
            self.drawing.append(draw.Rectangle(max_x + offset, l.y_coord - y_step/2, width, y_step, 
                                               fill=fill, stroke=border_color, stroke_width=border_width))

    def add_clade_labels(self, labels, offset=40.0, stroke_width=1.5, color="black", font_size=None):
        """Adds square brackets and text labels for clades."""
        self._pre_flight_check()
        fs = font_size or self.style.font_size
        max_x = max(l.coordinates[0] for l in self.t.get_leaves())
        bracket_x = max_x + offset
        for target, text in labels.items():
            try:
                node = self.t.search_nodes(name=target)[0] if isinstance(target, str) else target
                leaves = node.get_leaves()
                y_min = min(l.y_coord for l in leaves)
                y_max = max(l.y_coord for l in leaves)
                p = draw.Path(stroke=color, stroke_width=stroke_width, fill="none")
                p.M(bracket_x - 5, y_min).L(bracket_x, y_min).L(bracket_x, y_max).L(bracket_x - 5, y_max)
                self.drawing.append(p)
                self.drawing.append(draw.Text(text, fs, bracket_x + 8, (y_min + y_max) / 2, 
                                              fill=color, font_family=self.style.font_family, 
                                              text_anchor="start", dominant_baseline="middle"))
            except:
                continue

    def plot_continuous_variable(self, node_to_rgb, stroke_width=None):
        """Colors branches based on a continuous variable."""
        def _to_hex(rgb): return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        sw = stroke_width or self.style.branch_stroke_width
        for node in self.t.traverse():
            if node.is_root():
                continue
            c_c = node_to_rgb.get(node) or node_to_rgb.get(node.name)
            c_p = node_to_rgb.get(node.up) or node_to_rgb.get(node.up.name)
            if c_c and c_p:
                self.gradient_branch(node, stroke_width=sw, colors=(_to_hex(c_p), _to_hex(c_c)))
            else:
                self.highlight_branch(node, stroke_width=sw)
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                col = node_to_rgb.get(n) or node_to_rgb.get(n.name)
                if col:
                    x, y = n.coordinates
                    y_min, y_max = min(c.y_coord for c in n.children), max(c.y_coord for c in n.children)
                    self.drawing.append(draw.Line(x, y_min, x, y_max, stroke=_to_hex(col), stroke_width=sw, stroke_linecap="round"))
                    self.drawing.append(draw.Circle(x, y, self.style.node_r, fill=_to_hex(col)))

    def plot_categorical_trait(self, data, value_col, node_col="Node", palette=None, stroke_width=None, default_color="black"):
        """Colors branches based on categorical traits."""
        if hasattr(data, "to_dict"):
            mapping = dict(zip(data[node_col].astype(str), data[value_col]))
        else:
            mapping = data
        if palette is None:
            unique_vals = sorted(list(set(mapping.values())))
            defaults = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#FFFF33"]
            palette = {val: defaults[i % len(defaults)] for i, val in enumerate(unique_vals)}
        sw = stroke_width or self.style.branch_stroke_width
        def get_color(n): return palette.get(mapping.get(n.name), default_color)
        for node in self.t.traverse():
            if node.is_root():
                continue
            c_n, c_p = get_color(node), get_color(node.up)
            if c_n != c_p:
                self.gradient_branch(node, colors=(c_p, c_n), stroke_width=sw)
            else:
                x, y = node.coordinates
                px, _ = node.up.coordinates
                self.drawing.append(draw.Line(px, y, x, y, stroke=c_n, stroke_width=sw, stroke_linecap="round"))
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                color = get_color(n)
                x, y = n.coordinates
                y_min, y_max = min(c.y_coord for c in n.children), max(c.y_coord for c in n.children)
                self.drawing.append(draw.Line(x, y_min, x, y_max, stroke=color, stroke_width=sw, stroke_linecap="round"))
                self.drawing.append(draw.Circle(x, y, self.style.node_r, fill=color))

    def add_categorical_legend(self, palette, title="Legend", x=None, y=None, font_size=14, r=6):
        """Adds a categorical legend (colored circles with labels)."""
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

    def add_transfer_legend(self, colors=("purple", "orange"), labels=("Departure", "Arrival"), x=None, y=None, font_size=14):
        """Adds a legend specifically for Horizontal Gene Transfers."""
        palette = {labels[0]: colors[0], labels[1]: colors[1]}
        self.add_categorical_legend(palette, title="Transfer Event", x=x, y=y, font_size=font_size)

    def add_color_bar(self, low_color, high_color, vmin, vmax, title="", x=None, y=None, width=100, height=15, font_size=12):
        """Adds a continuous color bar gradient legend."""
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

    def add_leaf_images(self, image_dir, extension=".png", width=40, height=40, offset=10):
        """Places images next to leaf tips."""
        for leaf in self.t.get_leaves():
            lx, ly = self._leaf_xy(leaf, offset=offset)
            path = os.path.join(image_dir, f"{leaf.name}{extension}")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
                self.drawing.append(draw.Image(lx - width/2, ly - height/2, width, height, path=uri))

    def add_ancestral_images(self, image_dir, extension=".png", width=40, height=40, omit=None):
        """Places images at internal node positions."""
        for node in self.t.traverse():
            if not node.is_leaf():
                if omit and node.name in omit: continue
                nx, ny = self._node_xy(node)
                path = os.path.join(image_dir, f"{node.name}{extension}")
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
                    self.drawing.append(draw.Image(nx - width/2, ny - height/2, width, height, path=uri))

    def add_title(self, text, font_size=24, position="top", pad=40.0, color="black", weight="bold"):
        """Adds a title text to the drawing."""
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
        """Adds a physical scale bar representing a distance value."""
        self._pre_flight_check()
        px = float(length) * self.sf
        label = label or str(length)
        x = x if x is not None else -self.style.width/2 + 20
        y = y if y is not None else self.style.height/2 - 20
        self.drawing.append(draw.Line(x, y, x + px, y, stroke=stroke, stroke_width=stroke_width))
        self.drawing.append(draw.Text(label, self.style.font_size, x + px/2, y - 8, center=True))
