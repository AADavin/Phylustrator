import drawsvg as draw
import math
import os
import base64
from .base import BaseDrawer
from ..utils import polar_to_cartesian, generate_id, lerp_color

class RadialTreeDrawer(BaseDrawer):
    """
    Drawer class for rendering phylogenetic trees in a circular (radial) layout.
    
    Inherits from BaseDrawer and implements radial-specific geometry calculations
    where nodes are positioned by angle and radius.
    """
    def __init__(self, tree, style=None):
        """
        Initializes the RadialTreeDrawer and performs the initial layout calculation.

        Args:
            tree (ete3.TreeNode): The tree object to be visualized.
            style (TreeStyle, optional): Custom style configuration.
        """
        super().__init__(tree, style)
        self._calculate_layout()

    def _rot_ang(self, ang_deg: float) -> float:
        """Applies the global rotation offset to a given angle."""
        return float(ang_deg) + float(self.style.rotation)

    def _node_xy(self, node) -> tuple[float, float]:
        """Calculates Cartesian (x, y) coordinates for a node in polar space."""
        if not (hasattr(node, "rad") and hasattr(node, "angle")):
            self._calculate_layout()
        return polar_to_cartesian(self._rot_ang(node.angle), node.rad)

    def _leaf_xy(self, leaf, offset: float = 0.0) -> tuple[float, float]:
        """Calculates Cartesian coordinates for a leaf tip with a radial offset."""
        if not (hasattr(leaf, "rad") and hasattr(leaf, "angle")):
            self._calculate_layout()
        return polar_to_cartesian(self._rot_ang(leaf.angle), leaf.rad + float(offset))

    def _edge_point(self, child, where: float) -> tuple[float, float, float]:
        """Finds a point along the radial branch leading to a child node."""
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
        """
        Computes polar coordinates (radius and angle) for all nodes in the tree.
        
        This method is called automatically during initialization or before drawing.
        """
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

        # 3. Internal Centerings
        for n in self.t.traverse("postorder"):
            if not n.is_leaf():
                if n.children:
                    n.angle = sum(c.angle for c in n.children) / len(n.children)
                else:
                    n.angle = 0.0
        self._layout_calculated = True

    def draw(self, branch2color=None):
        """
        Draws the main tree skeleton.

        Connectors are drawn as circular arcs and branches as radial lines.

        Args:
            branch2color (dict, optional): Dictionary mapping `ete3.TreeNode` objects to 
                CSS color strings. Used to color specific branches.
        """
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
        """
        Draws a shaded "donut wedge" background behind a specific clade.

        Args:
            node (ete3.TreeNode): The root node of the clade to highlight.
            color (str, optional): Fill color. Defaults to "lightblue".
            opacity (float, optional): Fill opacity (0.0 to 1.0). Defaults to 0.3.
            padding (float, optional): Radial padding in pixels. Defaults to 10.
        """
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
        """
        Overlays a thicker or colored arc/line on the branch leading to the specific node.

        Args:
            node (ete3.TreeNode): The target node.
            color (str, optional): CSS color string. Defaults to "red".
            stroke_width (float, optional): Thickness of the highlight. Defaults to 2x standard width.
        """
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
        """
        Applies a linear color gradient along a radial branch segment.

        Args:
            node (ete3.TreeNode): The target node.
            colors (tuple, optional): Tuple of (start_color, end_color). Defaults to ("red", "blue").
            stroke_width (float, optional): Thickness of the branch. Defaults to style default.
        """
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
        """
        Adds text labels to leaf tips, automatically rotated to match the radial angle.

        Args:
            font_size (int, optional): Font size in pixels. Defaults to style default.
            color (str, optional): Text color. Defaults to "black".
            padding (float, optional): Distance from leaf tip to text start. Defaults to 10.
        """
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
        """
        Adds text labels to internal node positions.

        Args:
            font_size (int, optional): Font size. Defaults to style default * 0.8.
            color (str, optional): Text color. Defaults to "gray".
            padding (float, optional): Radial offset. Defaults to 5.
        """
        fs = font_size or self.style.font_size * 0.8
        for n in self.t.traverse():
            if not n.is_leaf() and n.name:
                ang = (self._rot_ang(n.angle)) % 360
                x, y = polar_to_cartesian(ang, n.rad + padding)
                text_rot = ang + (180 if 90 < ang < 270 else 0)
                self.drawing.append(draw.Text(n.name, fs, x, y, fill=color, font_family=self.style.font_family,
                                              transform=f"rotate({text_rot}, {x}, {y})", text_anchor="middle", dominant_baseline="middle"))

    def add_leaf_shapes(self, leaves, shape="circle", fill="blue", r=5.0, stroke=None, stroke_width=1.0, offset=0.0, rotation=0.0, opacity=1.0, orient=False):
        """
        Adds geometric markers next to specific leaf tips.

        Args:
            leaves (list): List of node names (str) or objects to mark.
            shape (str, optional): Shape type ("circle", "square", "triangle"). Defaults to "circle".
            fill (str, optional): Fill color. Defaults to "blue".
            r (float, optional): Radius/Size of the shape. Defaults to 5.0.
            stroke (str, optional): Border color. Defaults to None.
            stroke_width (float, optional): Border width. Defaults to 1.0.
            offset (float, optional): Radial distance offset from the leaf tip. Defaults to 0.0.
            rotation (float, optional): Additional rotation for the shape. Defaults to 0.0.
            opacity (float, optional): Opacity (0.0 to 1.0). Defaults to 1.0.
            orient (bool, optional): If True, rotates shape to match the branch angle. Defaults to False.
        """
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
        """
        Adds geometric markers centered on specific node positions.

        Args:
            nodes (list): List of node names/objects OR list of dicts with specific style per node.
            shape (str, optional): Default shape. Defaults to "circle".
            fill (str, optional): Default fill color. Defaults to "red".
            r (float, optional): Default radius. Defaults to 5.0.
            stroke (str, optional): Default stroke color. Defaults to None.
            stroke_width (float, optional): Default stroke width. Defaults to 1.0.
            rotation (float, optional): Default rotation. Defaults to 0.
            dx (float, optional): Cartesian X offset. Defaults to 0.
            dy (float, optional): Cartesian Y offset. Defaults to 0.
            orient (bool, optional): If True, rotates shape to match the branch angle. Defaults to False.
        """
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
        """
        Adds geometric markers along branches (e.g., to visualize events).

        Args:
            specs (list or DataFrame): Data definitions. Must contain 'branch' key/column.
            default_where (float, optional): Position along branch (0.0 to 1.0). Defaults to 0.5.
            offset (float, optional): Perpendicular offset from the branch line. Defaults to 0.0.
            orient (str, optional): Rotation mode: "along" (matches branch), "perp" (90 deg to branch), or None.
        """
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
        """
        Plots curved HGT (Horizontal Gene Transfer) links between lineages in radial space.

        Args:
            transfers (list or DataFrame): List of dicts with 'from', 'to', 'freq' keys.
            mode (str, optional): "time" (uses 'time' key for position) or "midpoint". Defaults to "midpoint".
            curve_type (str, optional): Bezier curve type ("C" or "S"). Defaults to "C".
            filter_below (float, optional): Minimum frequency to plot. Defaults to 0.0.
            use_gradient (bool, optional): If True, colors fade from source to dest. Defaults to True.
            gradient_colors (tuple, optional): (Start color, End color). Defaults to ("purple", "orange").
            color (str, optional): Solid color if gradients are disabled. Defaults to "orange".
            stroke_width (float, optional): Base thickness of the transfer lines. Defaults to 5.0.
            arc_intensity (float, optional): Curvature strength (control point distance). Defaults to 50.0.
            opacity (float, optional): Opacity of the transfer lines. Defaults to 0.6.
        """
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

    def add_time_axis(self, ticks, label="", tick_labels=None, stroke="gray", stroke_width=1.0, stroke_dasharray="3,3", font_size=10, label_angle=90):
        """
        Adds concentric rings representing evolutionary time or distance steps.

        Args:
            ticks (list): List of radial distances to draw rings at.
            label (str, optional): Unused in radial currently, but kept for interface consistency.
            tick_labels (list, optional): Custom text for each tick. Defaults to numerical values.
            stroke (str, optional): Color of rings. Defaults to "gray".
            stroke_width (float, optional): Thickness of rings. Defaults to 1.0.
            stroke_dasharray (str, optional): Dash pattern. Defaults to "3,3".
            font_size (int, optional): Size of tick labels. Defaults to 10.
            label_angle (float, optional): Angle (degrees) to place labels at. Defaults to 90.
        """
        self._pre_flight_check()
        for i, t in enumerate(ticks):
            r = t * self.sf
            self.drawing.append(draw.Circle(0, 0, r, fill="none", stroke=stroke, stroke_width=stroke_width, stroke_dasharray=stroke_dasharray))
            lx, ly = polar_to_cartesian(label_angle, r)
            
            # Use custom label if provided
            display_text = str(tick_labels[i]) if tick_labels is not None and i < len(tick_labels) else str(t)
            self.drawing.append(draw.Text(display_text, font_size, lx, ly, fill="black", stroke="white", stroke_width=0.5, 
                                          paint_order="stroke", text_anchor="middle", dominant_baseline="middle", font_family="Arial"))

    def add_heatmap(self, values, width=15.0, offset=10.0, low_color="#f7fbff", high_color="#08306b", border_color="none", border_width=0.5):
        """
        Adds a circular heatmap ring surrounding the leaf tips.

        Args:
            values (dict): Mapping of {node_name: numeric_value}.
            width (float, optional): Thickness of the heatmap ring. Defaults to 15.0.
            offset (float, optional): Radial offset from leaf tips. Defaults to 10.0.
            low_color (str, optional): Color for minimum value. Defaults to "#f7fbff".
            high_color (str, optional): Color for maximum value. Defaults to "#08306b".
            border_color (str, optional): Border color for cells. Defaults to "none".
            border_width (float, optional): Border thickness. Defaults to 0.5.
        """
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
        """
        Adds circular arcs outside the tree to group and label specific clades.

        Args:
            labels (dict): Mapping of {node_name_or_object: label_text}.
            offset (float, optional): Radial offset from the outermost leaf. Defaults to 40.0.
            stroke_width (float, optional): Thickness of the bracket arc. Defaults to 1.5.
            color (str, optional): Color of the arc and text. Defaults to "black".
            font_size (int, optional): Font size. Defaults to style default.
        """
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
        """
        Maps a continuous trait to branch colors using a gradient interpolation.

        Args:
            node_to_rgb (dict): Mapping of {node: (r, g, b)} tuples (values 0-255).
            stroke_width (float, optional): Thickness of the branches. Defaults to style default.
        """
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
        """
        Maps categorical traits to branch and node colors.

        If a parent and child have different categories, the branch color transitions (gradient).

        Args:
            data (DataFrame or dict): Data containing trait values per node.
            value_col (str): Column name for the trait values (if DataFrame).
            node_col (str, optional): Column name for node names. Defaults to "Node".
            palette (dict, optional): Color map {value: color}. Defaults to auto-generated.
            stroke_width (float, optional): Branch thickness. Defaults to style default.
            default_color (str, optional): Fallback color. Defaults to "black".
        """
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
        """
        Adds a physical scale bar representing a distance value.
        """
        self._pre_flight_check()
        px = float(length) * self.sf
        label = label or str(length)
        x = x if x is not None else -self.style.width/2 + 20
        y = y if y is not None else self.style.height/2 - 20
        self.drawing.append(draw.Line(x, y, x + px, y, stroke=stroke, stroke_width=stroke_width))
        self.drawing.append(draw.Text(label, self.style.font_size, x + px/2, y - 8, center=True))

