from platform import node
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

    def _rot_ang(self, ang_deg: float) -> float:
        # layout angle + style rotation (degrees)
        return float(ang_deg) + float(getattr(self.style, "rotation", 0.0))


    def _node_xy(self, node):
        if not (hasattr(node, "rad") and hasattr(node, "angle")):
            self._calculate_layout()
        r = float(node.rad)
        ang = self._rot_ang(node.angle)
        th = math.radians(ang)
        return (r * math.cos(th), r * math.sin(th))


    def _leaf_xy(self, leaf, offset: float = 0.0):
        if not (hasattr(leaf, "rad") and hasattr(leaf, "angle")):
            self._calculate_layout()
        r = float(leaf.rad) + float(offset)
        ang = self._rot_ang(leaf.angle)
        th = math.radians(ang)
        return (r * math.cos(th), r * math.sin(th))


    def _edge_point(self, child, where: float):
        """
        Place a point along the drawn branch centerline (radial segment at CHILD angle).
        where=0 => (r=parent.rad, angle=child.angle)
        where=1 => (r=child.rad,  angle=child.angle)
        """
        parent = child.up
        if parent is None:
            x, y = self._node_xy(child)
            return x, y, 0.0

        if not (hasattr(parent, "rad") and hasattr(child, "rad") and hasattr(child, "angle")):
            self._calculate_layout()

        r0 = float(parent.rad)
        r1 = float(child.rad)
        t = max(0.0, min(1.0, float(where)))
        r = r0 + (r1 - r0) * t

        ang = self._rot_ang(child.angle)
        th = math.radians(ang)
        x = r * math.cos(th)
        y = r * math.sin(th)

        # orientation "along" the branch direction
        edge_ang = ang if (r1 - r0) >= 0 else (ang + 180.0)
        return x, y, edge_ang

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

    def draw(self, branch2color=None, hide_radial_lines=None):
        """
        Standard radial drawing loop.
        :param branch2color: Dictionary {node_object: color_string}
        :param hide_radial_lines: List of nodes to skip parent connections
        """
        hidden_set = set(hide_radial_lines) if hide_radial_lines else set()

        for n in self.t.traverse("postorder"):
            # Resolve Color
            b_color = self.style.branch_color
            if branch2color and n in branch2color:
                b_color = branch2color[n]
                if b_color == "None": continue

            x, y = n.xy

            # 1. Radial Line to Parent
            if not n.is_root() and n not in hidden_set:
                px, py = radial_converter(n.angle, n.up.rad, self.style.rotation)
                self.d.append(draw.Line(px, py, x, y, stroke=b_color, stroke_width=self.style.branch_size))

            # 2. Connector Arc and Nodes
            if not n.is_leaf():
                a1, a2 = n.children[0].angle, n.children[-1].angle
                p = draw.Path(stroke=b_color, stroke_width=self.style.branch_size, fill="none")
                sx, sy = radial_converter(a1, n.rad, self.style.rotation)
                ex, ey = radial_converter(a2, n.rad, self.style.rotation)
                p.M(sx, sy).A(n.rad, n.rad, 0, 0, 1, ex, ey)
                self.d.append(p)
                
                if not n.is_root():
                    self.d.append(draw.Circle(x, y, self.style.node_size, fill=b_color))
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
    
    def plot_transfers(
        self,
        transfers,
        mode="midpoint",
        curve_type="C",
        filter_below=0.1,
        use_gradient=True,
        gradient_colors=("purple", "orange"),
        color="orange",
        use_thickness=True,
        stroke_width=5,
        arc_intensity=40,
        opacity=0.6,
    ):
        """
        Plot transfers on a radial tree.

        mode="time" places endpoints at the correct event time along each endpoint branch
        using node.time_from_origin (from Zombi parser). Otherwise uses midpoint logic.
        """
        # Accept either list[dict] or a DataFrame-like object (e.g. pandas.DataFrame)
        if hasattr(transfers, "to_dict") and hasattr(transfers, "columns"):
            transfers = transfers.to_dict(orient="records")

        # Ensure layout exists
        any_node = next(self.t.traverse("preorder"))
        if not hasattr(any_node, "rad") or not hasattr(any_node, "angle"):
            self._calculate_layout()

        name_to_node = {n.name: n for n in self.t.traverse()}

        def where_from_time(node, tt: float) -> float:
            parent = node.up
            if parent is None:
                return 0.0
            t0 = float(getattr(parent, "time_from_origin", 0.0))
            t1 = float(getattr(node, "time_from_origin", t0))
            denom = (t1 - t0) if abs(t1 - t0) > 1e-12 else 1.0
            w = (float(tt) - t0) / denom
            if w < 0.0:
                return 0.0
            if w > 1.0:
                return 1.0
            return w

        for tr in transfers:
            freq = float(tr.get("freq", 1.0))
            if freq < filter_below:
                continue

            src = name_to_node.get(tr.get("from"))
            dst = name_to_node.get(tr.get("to"))
            if src is None or dst is None:
                continue

            src_angle = float(src.angle)
            dst_angle = float(dst.angle)

            # Compute endpoints
            if (
                mode == "time"
                and tr.get("time") is not None
                and hasattr(src, "time_from_origin")
                and hasattr(dst, "time_from_origin")
            ):
                tt = float(tr["time"])
                w_src = where_from_time(src, tt)
                w_dst = where_from_time(dst, tt)
                sx, sy, _ = self._edge_point(src, w_src)
                ex, ey, _ = self._edge_point(dst, w_dst)

                # radii for control points
                src_r_mid = (sx * sx + sy * sy) ** 0.5
                dst_r_mid = (ex * ex + ey * ey) ** 0.5

            else:
                # midpoint fallback (old behavior)
                src_r = float(src.rad)
                dst_r = float(dst.rad)
                src_parent_r = float(src.up.rad) if src.up else (src_r - 20.0)
                dst_parent_r = float(dst.up.rad) if dst.up else (dst_r - 20.0)

                src_r_mid = (src_r + src_parent_r) / 2.0
                dst_r_mid = (dst_r + dst_parent_r) / 2.0

                sx, sy = radial_converter(src_angle, src_r_mid, self.style.rotation)
                ex, ey = radial_converter(dst_angle, dst_r_mid, self.style.rotation)

            width = (stroke_width * freq) if use_thickness else stroke_width
            path = draw.Path(stroke_width=width, fill="none", stroke_opacity=opacity)

            if use_gradient:
                grad_id = f"tr_grad_{random.randint(0, 999999)}"
                grad = draw.LinearGradient(sx, sy, ex, ey, id=grad_id)
                grad.add_stop(0, gradient_colors[0])
                grad.add_stop(1, gradient_colors[1])
                self.d.append(grad)
                path.args["stroke"] = grad
            else:
                path.args["stroke"] = color

            path.M(sx, sy)

            if curve_type.upper() == "S":
                c1x, c1y = radial_converter(src_angle, src_r_mid + arc_intensity, self.style.rotation)
                c2x, c2y = radial_converter(dst_angle, dst_r_mid - arc_intensity, self.style.rotation)
                path.C(c1x, c1y, c2x, c2y, ex, ey)
            else:
                c1x, c1y = radial_converter(src_angle, src_r_mid - arc_intensity, self.style.rotation)
                c2x, c2y = radial_converter(dst_angle, dst_r_mid - arc_intensity, self.style.rotation)
                path.C(c1x, c1y, c2x, c2y, ex, ey)

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

        # Background
        self.d.append(
            draw.Rectangle(x, y, w, box_h, fill="white", stroke="black", stroke_width=1, opacity=0.9)
        )

        cursor_y = y + top_pad + 2

        # Optional frequency scale
        if show_frequency:
            self.d.append(draw.Text(title, font_size, x + 10, cursor_y, font_family="sans-serif", font_weight="bold"))
            cursor_y += 10

            grad_id = f"legend_transfer_grad_{random.randint(0, 999999)}"
            grad = draw.LinearGradient(x + 10, cursor_y + bar_h / 2, x + 10 + bar_w, cursor_y + bar_h / 2, id=grad_id)
            grad.add_stop(0, colors[0])
            grad.add_stop(1, colors[1])
            self.d.append(grad)
            self.d.append(draw.Rectangle(x + 10, cursor_y, bar_w, bar_h, fill=grad))

            # low/high numeric labels
            self.d.append(draw.Text(f"{low}", num_font_size, x + 10, cursor_y + bar_h + 12, font_family="sans-serif"))
            self.d.append(draw.Text(f"{high}", num_font_size, x + 10 + bar_w - 15, cursor_y + bar_h + 12, font_family="sans-serif"))
            cursor_y += bar_h + 24

        # Direction swatches
        if show_direction:
            sw = 14
            self.d.append(draw.Rectangle(x + 10, cursor_y, sw, sw, fill=colors[0]))
            self.d.append(draw.Text(source_label, font_size, x + 30, cursor_y + 11, font_family="sans-serif"))
            cursor_y += row_h

            self.d.append(draw.Rectangle(x + 10, cursor_y, sw, sw, fill=colors[1]))
            self.d.append(draw.Text(arrival_label, font_size, x + 30, cursor_y + 11, font_family="sans-serif"))
