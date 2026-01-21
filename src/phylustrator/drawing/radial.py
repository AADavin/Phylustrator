import drawsvg as draw
import math
import os
import base64
from .base import BaseDrawer
from ..utils import polar_to_cartesian, generate_id, lerp_color

class RadialTreeDrawer(BaseDrawer):
    """
    Drawer class for rendering phylogenetic trees in a circular (radial) layout.
    """
    def __init__(self, tree, style=None):
        """
        Initializes the RadialTreeDrawer and calculates the layout.
        """
        super().__init__(tree, style)
        self._calculate_layout()

    def _rot_ang(self, ang_deg: float) -> float:
        """Applies the style's rotation offset to a layout angle."""
        return float(ang_deg) + float(self.style.rotation)

    def _node_xy(self, node) -> tuple[float, float]:
        """Calculates Cartesian (x, y) coordinates for a node."""
        if not (hasattr(node, "rad") and hasattr(node, "angle")):
            self._calculate_layout()
        return polar_to_cartesian(self._rot_ang(node.angle), node.rad)

    def _leaf_xy(self, leaf, offset: float = 0.0) -> tuple[float, float]:
        """Calculates coordinates for a leaf tip with optional radial offset."""
        if not (hasattr(leaf, "rad") and hasattr(leaf, "angle")):
            self._calculate_layout()
        return polar_to_cartesian(self._rot_ang(leaf.angle), leaf.rad + float(offset))

    def _edge_point(self, child, where: float) -> tuple[float, float, float]:
        """Returns (x, y, angle) for a point along the radial branch leading to the child."""
        parent = child.up
        if parent is None:
            return (*self._node_xy(child), self._rot_ang(child.angle))
        r_p, r_c = float(parent.rad), float(child.rad)
        t = max(0.0, min(1.0, float(where)))
        r = r_p + (r_c - r_p) * t
        ang = self._rot_ang(child.angle)
        x, y = polar_to_cartesian(ang, r)
        return x, y, ang

    def _calculate_layout(self):
        """Calculates radial radius and angular positions for all nodes."""
        # 1. Radial Scaling (Distances)
        max_dist = 0.0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            max_dist = max(max_dist, n.dist_to_root)
        self.total_tree_depth = max_dist
        self.sf = float(self.style.radius) / max_dist if max_dist > 0 else 1.0
        
        for n in self.t.traverse():
            n.rad = n.dist_to_root * self.sf

        # 2. Angular Scaling (Leaves)
        leaves = self.t.get_leaves()
        span = float(self.style.degrees)
        angle_step = span / max(len(leaves), 1)
        for i, leaf in enumerate(leaves):
            leaf.angle = i * angle_step

        # 3. Internal Node Centering
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                if n.children:
                    n.angle = sum(c.angle for c in n.children) / len(n.children)
                else:
                    n.angle = 0.0
        self._layout_calculated = True

    def draw(self, branch2color=None):
        """Draws the tree with circular arcs and radial connectors."""
        self._pre_flight_check()
        for n in self.t.traverse("postorder"):
            color = branch2color.get(n, self.style.branch_color) if branch2color else self.style.branch_color
            x, y = self._node_xy(n)
            if not n.is_root():
                parent = n.up
                px, py = self._node_xy(parent)
                start_ang, end_ang = self._rot_ang(parent.angle), self._rot_ang(n.angle)
                if abs(start_ang - end_ang) > 0.001:
                    ax, ay = polar_to_cartesian(end_ang, parent.rad)
                    path = draw.Path(stroke=color, stroke_width=self.style.branch_stroke_width, fill="none")
                    sweep = 1 if end_ang > start_ang else 0
                    path.M(px, py).A(parent.rad, parent.rad, 0, 0, sweep, ax, ay)
                    self.drawing.append(path)
                    self.drawing.append(draw.Line(ax, ay, x, y, stroke=color, stroke_width=self.style.branch_stroke_width))
                else:
                    self.drawing.append(draw.Line(px, py, x, y, stroke=color, stroke_width=self.style.branch_stroke_width))
            
            r_v = self.style.leaf_r if n.is_leaf() else self.style.node_r
            if r_v > 0:
                fill = self.style.leaf_color if n.is_leaf() else color
                self.drawing.append(draw.Circle(x, y, r_v, fill=fill))

    def highlight_clade(self, node, color="lightblue", opacity=0.3, padding=10):
        """Draws a shaded donut-wedge behind a clade."""
        self._pre_flight_check()
        leaves = node.get_leaves()
        angles = [l.angle for l in leaves]
        start_ang, end_ang = self._rot_ang(min(angles)), self._rot_ang(max(angles))
        r_i, r_o = node.rad - padding, max(l.rad for l in leaves) + padding
        
        p = draw.Path(fill=color, fill_opacity=opacity)
        p1x, p1y = polar_to_cartesian(start_ang, r_i)
        p2x, p2y = polar_to_cartesian(end_ang, r_i)
        p3x, p3y = polar_to_cartesian(end_ang, r_o)
        p4x, p4y = polar_to_cartesian(start_ang, r_o)
        sweep = 1 if end_ang > start_ang else 0
        p.M(p1x, p1y).A(r_i, r_i, 0, 0, sweep, p2x, p2y).L(p3x, p3y).A(r_o, r_o, 0, 0, 0 if sweep == 1 else 1, p4x, p4y).Z()
        self.drawing.append(p)

    def highlight_branch(self, node, color="red", stroke_width=None):
        """Highlights a specific branch with an arc and radial line."""
        if node.is_root(): return
        sw = stroke_width or self.style.branch_stroke_width * 2
        px, py = self._node_xy(node.up)
        x, y = self._node_xy(node)
        start_ang, end_ang = self._rot_ang(node.up.angle), self._rot_ang(node.angle)
        
        if abs(start_ang - end_ang) > 0.001:
            ax, ay = polar_to_cartesian(end_ang, node.up.rad)
            path = draw.Path(stroke=color, stroke_width=sw, fill="none", stroke_linecap="round")
            sweep = 1 if end_ang > start_ang else 0
            path.M(px, py).A(node.up.rad, node.up.rad, 0, 0, sweep, ax, ay)
            self.drawing.append(path)
            self.drawing.append(draw.Line(ax, ay, x, y, stroke=color, stroke_width=sw, stroke_linecap="round"))
        else:
            self.drawing.append(draw.Line(px, py, x, y, stroke=color, stroke_width=sw, stroke_linecap="round"))

    def gradient_branch(self, node, colors=("red", "blue"), stroke_width=None):
        """Applies a color gradient along a branch."""
        if node.is_root(): return
        sw = stroke_width or self.style.branch_stroke_width
        px, py = self._node_xy(node.up)
        x, y = self._node_xy(node)
        gid = generate_id("grad")
        grad = draw.LinearGradient(px, py, x, y, id=gid)
        grad.add_stop(0, colors[0])
        grad.add_stop(1, colors[1])
        self.drawing.append(grad)
        self.highlight_branch(node, color=grad, stroke_width=sw)

    def add_leaf_names(self, font_size=None, color="black", padding=10):
        """Adds text labels to leaf tips, rotated radially."""
        fs = font_size or self.style.font_size
        for l in self.t.get_leaves():
            ang = (self._rot_ang(l.angle)) % 360
            x, y = polar_to_cartesian(ang, l.rad + padding)
            text_rot, anchor = ang, "start"
            if 90 < ang < 270:
                text_rot += 180
                anchor = "end"
            self.drawing.append(draw.Text(l.name, fs, x, y, fill=color, font_family=self.style.font_family,
                                          transform=f"rotate({text_rot}, {x}, {y})", text_anchor=anchor, dominant_baseline="middle"))

    def add_node_names(self, font_size=None, color="gray", padding=5):
        """Adds text labels to internal nodes."""
        fs = font_size or self.style.font_size * 0.8
        for n in self.t.traverse():
            if not n.is_leaf() and n.name:
                ang = (self._rot_ang(n.angle)) % 360
                x, y = polar_to_cartesian(ang, n.rad + padding)
                text_rot = ang + (180 if 90 < ang < 270 else 0)
                self.drawing.append(draw.Text(n.name, fs, x, y, fill=color, font_family=self.style.font_family,
                                              transform=f"rotate({text_rot}, {x}, {y})", text_anchor="middle", dominant_baseline="middle"))

    def add_leaf_shapes(self, leaves, shape="circle", fill="blue", r=5.0, stroke=None, stroke_width=1.0, offset=0.0, rotation=0.0, opacity=1.0, orient=False):
        """Adds shapes at leaf tips."""
        self._pre_flight_check()
        for item in leaves:
            try:
                node = self.t & item if isinstance(item, str) else item
                ang = self._rot_ang(node.angle)
                x, y = polar_to_cartesian(ang, node.rad + float(offset))
                rot = rotation + (ang if orient else 0.0)
                self._draw_shape_at(x, y, shape, fill, r, stroke, stroke_width, rot, opacity)
            except: continue

    def add_node_shapes(self, nodes, shape="circle", fill="red", r=5.0, stroke=None, stroke_width=1.0, rotation=0, dx=0, dy=0, orient=False):
        """Adds shapes at node positions."""
        self._pre_flight_check()
        if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict):
            for s in nodes:
                self.add_node_shapes([s.get("node")], s.get("shape", shape), s.get("fill", fill), s.get("r", r), 
                                     s.get("stroke", stroke), s.get("stroke_width", stroke_width), s.get("rotation", rotation), orient=orient)
            return
        for item in nodes:
            try:
                node = self.t.search_nodes(name=item)[0] if isinstance(item, str) else item
                ang = self._rot_ang(node.angle)
                x, y = polar_to_cartesian(ang, node.rad)
                rot = rotation + (ang if orient else 0.0)
                self._draw_shape_at(x + dx, y + dy, shape, fill, r, stroke, stroke_width, rot)
            except: continue

    def add_branch_shapes(self, specs, default_where=0.5, offset=0.0, orient=None):
        """Adds geometric shapes along radial branches."""
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

    def plot_transfers(self, transfers, mode="midpoint", curve_type="C", filter_below=0.0, use_gradient=True, 
                       gradient_colors=("purple", "orange"), color="orange", stroke_width=5.0, arc_intensity=50.0, opacity=0.6):
        """Plots curved HGT arrows in radial space."""
        if hasattr(transfers, "to_dict"): transfers = transfers.to_dict(orient="records")
        name2node = {n.name: n for n in self.t.traverse()}
        self._pre_flight_check()
        def get_where(node, t_ev):
            p = node.up
            if not p: return 0.0
            t0, t1 = float(getattr(p, "time_from_origin", 0.0)), float(getattr(node, "time_from_origin", 0.0))
            return max(0.0, min(1.0, (float(t_ev) - t0) / (t1 - t0))) if abs(t1 - t0) > 1e-12 else 0.5
        
        for tr in transfers:
            freq = float(tr.get("freq", 1.0))
            if freq < filter_below: continue
            src, dst = name2node.get(tr.get("from")), name2node.get(tr.get("to"))
            if not src or not dst: continue
            if mode == "time" and "time" in tr:
                x_s, y_s, _ = self._edge_point(src, get_where(src, tr["time"]))
                x_e, y_e, _ = self._edge_point(dst, get_where(dst, tr["time"]))
            else:
                x_s, y_s, _ = self._edge_point(src, 0.5); x_e, y_e, _ = self._edge_point(dst, 0.5)
            
            path = draw.Path(stroke_width=stroke_width * freq, fill="none", stroke_opacity=opacity)
            if use_gradient:
                gid = generate_id("tr_grad")
                grad = draw.LinearGradient(x_s, y_s, x_e, y_e, id=gid)
                grad.add_stop(0, gradient_colors[0]); grad.add_stop(1, gradient_colors[1])
                self.drawing.append(grad); path.args["stroke"] = grad
            else: path.args["stroke"] = color
            path.M(x_s, y_s)
            mx, my = (x_s + x_e) / 2.0, (y_s + y_e) / 2.0
            dist = math.sqrt(mx**2 + my**2)
            pull = max(0, dist - arc_intensity) if dist > 0 else 0
            cx = (mx/dist)*pull if dist > 0 else 0
            cy = (my/dist)*pull if dist > 0 else 0
            path.Q(cx, cy, x_e, y_e); self.drawing.append(path)

    def add_time_axis(self, ticks, label="", stroke="gray", stroke_width=1.0, stroke_dasharray="3,3", font_size=10, label_angle=90):
        """Adds concentric rings representing time/distance."""
        self._pre_flight_check()
        for t in ticks:
            r = t * self.sf
            self.drawing.append(draw.Circle(0, 0, r, fill="none", stroke=stroke, stroke_width=stroke_width, stroke_dasharray=stroke_dasharray))
            lx, ly = polar_to_cartesian(label_angle, r)
            self.drawing.append(draw.Text(str(t), font_size, lx, ly, fill="black", stroke="white", stroke_width=0.5, 
                                          paint_order="stroke", text_anchor="middle", dominant_baseline="middle", font_family="Arial"))

    def add_heatmap(self, values, width=15.0, offset=10.0, low_color="#f7fbff", high_color="#08306b", border_color="none", border_width=0.5):
        """Adds a circular heatmap ring next to tips."""
        if hasattr(values, "to_dict"): values = values.to_dict()
        vals = [float(v) for v in values.values() if isinstance(v, (int, float))]
        if not vals: return
        vmin, vmax = min(vals), max(vals) + 1e-12
        angle_span = float(self.style.degrees) / len(self.t.get_leaves())
        for l in self.t.get_leaves():
            val = values.get(l.name)
            fill = lerp_color(low_color, high_color, (float(val) - vmin) / (vmax - vmin)) if val is not None else "white"
            start_ang, end_ang = self._rot_ang(l.angle - angle_span/2), self._rot_ang(l.angle + angle_span/2)
            r_i, r_o = l.rad + offset, l.rad + offset + width
            p = draw.Path(fill=fill, stroke=border_color, stroke_width=border_width)
            p1x, p1y = polar_to_cartesian(start_ang, r_i); p2x, p2y = polar_to_cartesian(end_ang, r_i)
            p3x, p3y = polar_to_cartesian(end_ang, r_o); p4x, p4y = polar_to_cartesian(start_ang, r_o)
            sweep = 1 if end_ang > start_ang else 0
            p.M(p1x, p1y).A(r_i, r_i, 0, 0, sweep, p2x, p2y).L(p3x, p3y).A(r_o, r_o, 0, 0, 0 if sweep == 1 else 1, p4x, p4y).Z()
            self.drawing.append(p)

    def add_clade_labels(self, labels, offset=40.0, stroke_width=1.5, color="black", font_size=None):
        """Adds circular arcs and labels for clades outside the tree."""
        self._pre_flight_check()
        fs = font_size or self.style.font_size
        max_rad = max(l.rad for l in self.t.get_leaves())
        arc_rad = max_rad + offset
        for target, text in labels.items():
            try:
                node = self.t.search_nodes(name=target)[0] if isinstance(target, str) else target
                leaves = node.get_leaves()
                angles = [l.angle for l in leaves]
                start_ang, end_ang = self._rot_ang(min(angles)), self._rot_ang(max(angles))
                mid_ang = (start_ang + end_ang) / 2.0
                p1x, p1y = polar_to_cartesian(start_ang, arc_rad); p2x, p2y = polar_to_cartesian(end_ang, arc_rad)
                sweep = 1 if end_ang > start_ang else 0
                p = draw.Path(stroke=color, stroke_width=stroke_width, fill="none")
                p.M(p1x, p1y).A(arc_rad, arc_rad, 0, 0, sweep, p2x, p2y)
                self.drawing.append(p)
                tx, ty = polar_to_cartesian(mid_ang, arc_rad + 8)
                text_rot, anchor = mid_ang, "start"
                if 90 < (mid_ang % 360) < 270:
                    text_rot += 180; anchor = "end"
                self.drawing.append(draw.Text(text, fs, tx, ty, fill=color, font_family=self.style.font_family,
                                              transform=f"rotate({text_rot}, {tx}, {ty})", text_anchor=anchor, dominant_baseline="middle"))
            except: continue

    def plot_continuous_variable(self, node_to_rgb, stroke_width=None):
        """Colors branches based on RGB mapping of continuous traits."""
        def _to_hex(rgb): return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        sw = stroke_width or self.style.branch_stroke_width
        for node in self.t.traverse():
            if node.is_root(): continue
            c_c = node_to_rgb.get(node) or node_to_rgb.get(node.name)
            c_p = node_to_rgb.get(node.up) or node_to_rgb.get(node.up.name)
            if c_c and c_p: self.gradient_branch(node, stroke_width=sw, colors=(_to_hex(c_p), _to_hex(c_c)))
            else: self.highlight_branch(node, stroke_width=sw)
        for n in self.t.traverse("postorder"):
            if not n.is_leaf() and (col := (node_to_rgb.get(n) or node_to_rgb.get(n.name))):
                x, y = self._node_xy(n); self.drawing.append(draw.Circle(x, y, self.style.node_r, fill=_to_hex(col)))

    def plot_categorical_trait(self, data, value_col, node_col="Node", palette=None, stroke_width=None, default_color="black"):
        """Colors branches based on categorical trait mapping."""
        if hasattr(data, "to_dict"): mapping = dict(zip(data[node_col].astype(str), data[value_col]))
        else: mapping = data
        if palette is None:
            unique_vals = sorted(list(set(mapping.values())))
            defaults = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#FFFF33"]
            palette = {val: defaults[i % len(defaults)] for i, val in enumerate(unique_vals)}
        sw = stroke_width or self.style.branch_stroke_width
        def get_color(n): return palette.get(mapping.get(n.name), default_color)
        for node in self.t.traverse():
            if node.is_root(): continue
            c_n, c_p = get_color(node), get_color(node.up)
            if c_n != c_p: self.gradient_branch(node, colors=(c_p, c_n), stroke_width=sw)
            else: self.highlight_branch(node, color=c_n, stroke_width=sw)
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                x, y = self._node_xy(n); self.drawing.append(draw.Circle(x, y, self.style.node_r, fill=get_color(n)))

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

    def add_transfer_legend(self, colors=("purple", "orange"), labels=("Departure", "Arrival"), x=None, y=None, font_size=14):
        palette = {labels[0]: colors[0], labels[1]: colors[1]}
        self.add_categorical_legend(palette, title="Transfer Event", x=x, y=y, font_size=font_size)

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

    def add_leaf_images(self, image_dir, extension=".png", width=40, height=40, offset=10):
        for leaf in self.t.get_leaves():
            lx, ly = self._leaf_xy(leaf, offset=offset)
            path = os.path.join(image_dir, f"{leaf.name}{extension}")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
                self.drawing.append(draw.Image(lx - width/2, ly - height/2, width, height, path=uri))

    def add_ancestral_images(self, image_dir, extension=".png", width=40, height=40, omit=None):
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
        self._pre_flight_check()
        px = float(length) * self.sf
        label = label or str(length)
        x = x if x is not None else -self.style.width/2 + 20
        y = y if y is not None else self.style.height/2 - 20
        self.drawing.append(draw.Line(x, y, x + px, y, stroke=stroke, stroke_width=stroke_width))
        self.drawing.append(draw.Text(label, self.style.font_size, x + px/2, y - 8, center=True))
