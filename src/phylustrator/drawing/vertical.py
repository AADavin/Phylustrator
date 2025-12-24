import drawsvg as draw
from .base import BaseDrawer
import random

class VerticalTreeDrawer(BaseDrawer):
    def __init__(self, tree, style=None):
        super().__init__(tree, style)
        self._calculate_layout()

    def _node_xy(self, node):
        if not hasattr(node, "coordinates"):
            self._calculate_layout()
        x, y = node.coordinates  # coordinates is (x,y)
        return float(x), float(y)

    def _leaf_xy(self, leaf, offset: float = 0.0):
        x, y = self._node_xy(leaf)
        return (x + float(offset), y)

    def _edge_point(self, child, where: float):
        """
        Place markers along the *horizontal* part of the rectangular edge:
        (x_parent, y_child) -> (x_child, y_child)

        This keeps y constant, so where=0 is at the elbow (NOT on the shared vertical),
        and where=1 is at the child tip.
        """
        parent = child.up
        if parent is None:
            x, y = self._node_xy(child)
            return x, y, 0.0

        # Ensure layout exists
        if not hasattr(parent, "coordinates") or not hasattr(child, "coordinates"):
            self._calculate_layout()

        x_parent, _y_parent = self._node_xy(parent)
        x_child, y_child = self._node_xy(child)

        t = max(0.0, min(1.0, float(where)))
        x = x_parent + (x_child - x_parent) * t
        y = y_child

        # Horizontal direction only (no weird rotations)
        edge_ang = 0.0 if (x_child - x_parent) >= 0 else 180.0
        return x, y, edge_ang

    def _calculate_layout(self, max_width=None):
        """
        Calculates tree coordinates. 
        :param max_width: If provided, scales the tree to this width instead of the style width.
        """
        # 1. Calculate Distances
        max_dist = 0
        for n in self.t.traverse("preorder"):
            n.dist_to_root = n.up.dist_to_root + n.dist if not n.is_root() else getattr(n, "dist", 0.0)
            if n.dist_to_root > max_dist: max_dist = n.dist_to_root
        
        self.total_tree_depth = max_dist
        
        # 2. Handle Scaling and Margins
        horizontal_padding = 100 
        target_width = max_width if max_width is not None else self.style.width
        self.sf = (target_width - (horizontal_padding * 2)) / max_dist if max_dist > 0 else 1
        
        # Center the root X based on padding
        self.root_x = -self.style.width / 2 + horizontal_padding

        # 3. Calculate Vertical Positions
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

    def draw(self, branch2color=None, right_margin=200):
        """
        Draws the tree while reserving space on the right for images.
        """
        # 1. Re-run layout calculation with the reserved right margin
        self._calculate_layout(max_width=self.style.width - right_margin)

        for n in self.t.traverse("postorder"):
            x, y = n.coordinates
            
            # Resolve Color
            color = self.style.branch_color
            if branch2color and n in branch2color:
                color = branch2color[n]

            # 2. Horizontal branch
            if not n.is_root():
                px, py = n.up.coordinates
                self.d.append(draw.Line(px, y, x, y, stroke=color, 
                                        stroke_width=self.style.branch_size, stroke_linecap="round"))
            else:
                # Root "handle"
                self.d.append(draw.Line(x - 20, y, x, y, stroke=color, stroke_width=self.style.branch_size))

            # 3. Vertical connector
            if not n.is_leaf():
                y_min = min(c.y_coord for c in n.children)
                y_max = max(c.y_coord for c in n.children)
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
        
        # Split these into two separate calls
        grad.add_stop(0, colors[0])
        grad.add_stop(1, colors[1])
        
        self.d.append(grad)
        self.d.append(draw.Line(px, y, x, y, stroke=grad, stroke_width=s_width))

    def plot_continuous_variable(self, node_to_rgb, size=None):
        """
        Colors branches using a gradient based on RGB values at each node.
        Also recolors vertical connectors (internal-node elbows) so they are not left black.
        :param node_to_rgb: Dict mapping node names or objects to (r, g, b) tuples.
        :param size: Thickness of the branches.
        """
        def _to_hex(rgb):
            return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))

        s_width = size if size is not None else self.style.branch_size

        # 1) Horizontal segments: parent -> child as a gradient
        for node in self.t.traverse():
            if node.is_root():
                continue

            parent = node.up

            color_child = node_to_rgb.get(node) or node_to_rgb.get(node.name)
            color_parent = node_to_rgb.get(parent) or node_to_rgb.get(parent.name)

            if color_child is not None and color_parent is not None:
                self.gradient_branch(
                    node,
                    colors=(_to_hex(color_parent), _to_hex(color_child)),
                    size=s_width,
                )
            else:
                # fallback
                self.highlight_branch(node, color=self.style.branch_color, size=s_width)

        # 2) Vertical connectors: redraw them on top with the internal node's color
        for n in self.t.traverse("postorder"):
            if n.is_leaf():
                continue

            col = node_to_rgb.get(n) or node_to_rgb.get(n.name)
            if col is None:
                continue

            x, y = n.coordinates
            y_min = min(c.y_coord for c in n.children)
            y_max = max(c.y_coord for c in n.children)

            self.d.append(draw.Line(
                x, y_min, x, y_max,
                stroke=_to_hex(col),
                stroke_width=s_width,
                stroke_linecap="round"
            ))
            # optional: recolor the node dot too
            self.d.append(draw.Circle(x, y, self.style.node_size, fill=_to_hex(col)))


    def add_leaf_names(
        self, 
        font_size=None, 
        color=None, 
        font_family=None, 
        rotation=0, 
        padding=10
    ):
        """
        Adds leaf labels where the center of the text is aligned with the leaf tip.
        """
        fs = font_size if font_size is not None else self.style.font_size
        ff = font_family if font_family is not None else self.style.font_family
        text_color = color if color is not None else "black"

        for l in self.t.get_leaves():
            x, y = l.coordinates
            
            # The anchor point is the leaf tip + padding
            tx = x + padding
            ty = y 

            # Rotate around the center (tx, ty)
            transform = f"rotate({rotation}, {tx}, {ty})" if rotation != 0 else ""

            self.d.append(draw.Text(
                l.name, 
                fs, 
                tx, 
                ty, 
                fill=text_color, 
                font_family=ff,
                transform=transform,
                text_anchor="middle",      # Centers horizontally
                dominant_baseline="middle" # Centers vertically
            ))
    
    def add_node_names(
        self, 
        font_size=None, 
        color="gray", 
        font_family=None, 
        x_offset=-15, 
        y_offset=-10,
        rotation=0
    ):
        """
        Adds labels to internal nodes centered on the offset coordinate.
        """
        fs = font_size if font_size is not None else self.style.font_size * 0.8
        ff = font_family if font_family is not None else self.style.font_family

        for n in self.t.traverse():
            if not n.is_leaf():
                if not n.name:
                    continue
                    
                x, y = n.coordinates
                
                # Apply offsets to the center point
                tx = x + x_offset
                ty = y + y_offset

                transform = f"rotate({rotation}, {tx}, {ty})" if rotation != 0 else ""

                self.d.append(draw.Text(
                    n.name, 
                    fs, 
                    tx, 
                    ty, 
                    fill=color, 
                    font_family=ff,
                    transform=transform,
                    text_anchor="middle",      # Centers horizontally
                    dominant_baseline="middle" # Centers vertically
                ))


    def add_time_axis(
        self,
        ticks: list[float],
        label: str = "Time",
        tick_size: float = 6.0,
        padding: float = 20.0,
        y_offset: float = 0.0,
        root_stub: float = 20.0,
        stroke: str = "black",
        stroke_width: float = 2.0,
        font_size: int | None = None,
        font_family: str | None = None,
        # --- grid options ---
        grid: bool = False,
        grid_stroke: str = "#cccccc",
        grid_stroke_width: float = 1.0,
        grid_opacity: float = 0.5,
        # --- NEW: custom tick labels ---
        tick_labels: dict[float, str] | None = None,
    ) -> None:
        """
        Draw a horizontal time axis. Optionally draw vertical grid lines at each tick
        across the tree.

        tick_labels lets you display labels that differ from the numeric tick positions,
        e.g. show "-2" at tick position 2.0 (backwards time).
        """
        if not ticks:
            return

        # Ensure layout exists
        any_node = next(self.t.traverse("preorder"))
        if not hasattr(any_node, "coordinates") or not hasattr(any_node, "y_coord"):
            self._calculate_layout()

        sf = float(self.sf)

        # Font defaults
        fs = font_size if font_size is not None else self.style.font_size
        ff = font_family if font_family is not None else self.style.font_family

        # Tree vertical extent
        leaves = self.t.get_leaves()
        min_y = min(float(l.y_coord) for l in leaves)
        max_y = max(float(l.y_coord) for l in leaves)

        # Place axis below the tree
        y_axis = max_y + float(padding) + float(y_offset)

        # Axis X range
        x_left = float(self.root_x) - float(root_stub)
        x_right = float(self.root_x) + (max(float(t) for t in ticks) * sf)

        # Baseline
        self.d.append(draw.Line(
            x_left, y_axis,
            x_right, y_axis,
            stroke=stroke,
            stroke_width=stroke_width,
        ))

        tick_labels = tick_labels or {}

        # Ticks (+ optional vertical grid lines)
        for tt in ticks:
            tt = float(tt)
            x = float(self.root_x) + tt * sf

            if grid:
                self.d.append(draw.Line(
                    x, min_y,
                    x, max_y,
                    stroke=grid_stroke,
                    stroke_width=grid_stroke_width,
                    stroke_opacity=grid_opacity,
                ))

            self.d.append(draw.Line(
                x, y_axis,
                x, y_axis + float(tick_size),
                stroke=stroke,
                stroke_width=stroke_width,
            ))

            text = tick_labels.get(tt, str(tt))
            self.d.append(draw.Text(
                text,
                fs,
                x,
                y_axis + float(tick_size) + fs,
                center=True,
                font_family=ff,
            ))

        # Axis label
        self.d.append(draw.Text(
            label,
            fs,
            (x_left + x_right) / 2.0,
            y_axis + float(tick_size) + fs * 2.2,
            center=True,
            font_family=ff,
        ))



    def plot_transfers(
        self,
        transfers,
        mode="midpoint",
        curve_type="C",
        filter_below=0.0,
        use_gradient=True,
        gradient_colors=("purple", "orange"),
        color="orange",
        use_thickness=True,
        stroke_width=5,
        arc_intensity=40,
        opacity=0.6,
    ):
        """
        Plot horizontal gene transfers as curved lines.

        Parameters
        ----------
        transfers
            Either a list of dicts OR a pandas.DataFrame with at least:
            'from', 'to', 'time' (optional), 'freq' (optional)
        mode
            "midpoint" (default) or "time".
            - midpoint: attach curves to mid-branch positions (old behavior)
            - time: attach curves at the event time along each endpoint branch using
                    node.time_from_origin (Zombi parser provides this)
        curve_type
            "C" (default) or "S"
        """
        # Accept either list[dict] or a DataFrame-like object (e.g. pandas.DataFrame)
        if hasattr(transfers, "to_dict") and hasattr(transfers, "columns"):
            transfers = transfers.to_dict(orient="records")

        name2node = {n.name: n for n in self.t.traverse()}

        # Ensure layout exists
        any_node = next(self.t.traverse("preorder"))
        if not hasattr(any_node, "coordinates") or not hasattr(any_node, "y_coord"):
            self._calculate_layout()

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

            src = name2node.get(tr.get("from"))
            dst = name2node.get(tr.get("to"))
            if src is None or dst is None:
                continue

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
                x_start, y_start, _ = self._edge_point(src, w_src)
                x_end, y_end, _ = self._edge_point(dst, w_dst)
            else:
                # midpoint fallback (old behavior)
                y_start, y_end = float(src.y_coord), float(dst.y_coord)
                src_px = src.up.coordinates[0] if src.up else (src.coordinates[0] - 20)
                dst_px = dst.up.coordinates[0] if dst.up else (dst.coordinates[0] - 20)
                x_start = (float(src_px) + float(src.coordinates[0])) / 2.0
                x_end = (float(dst_px) + float(dst.coordinates[0])) / 2.0

            # Styling
            width = (stroke_width * freq) if use_thickness else stroke_width
            path = draw.Path(stroke_width=width, fill="none", stroke_opacity=opacity)

            if use_gradient:
                grad_id = f"tr_grad_{random.randint(0, 999999)}"
                grad = draw.LinearGradient(x_start, y_start, x_end, y_end, id=grad_id)
                grad.add_stop(0, gradient_colors[0])
                grad.add_stop(1, gradient_colors[1])
                self.d.append(grad)
                path.args["stroke"] = grad
            else:
                path.args["stroke"] = color

            # Geometry
            path.M(x_start, y_start)

            if curve_type.upper() == "S":
                dx = x_end - x_start
                sgn = 1 if dx >= 0 else -1
                arc = abs(arc_intensity)
                cp1x = x_start + (sgn * arc)
                cp2x = x_end - (sgn * arc)
                path.C(cp1x, y_start, cp2x, y_end, x_end, y_end)
            else:
                # C-curve
                path.C(
                    x_start - arc_intensity, y_start,
                    x_end   - arc_intensity, y_end,
                    x_end, y_end
                )

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


    def add_heatmap(
            self,
            values,
            width: float = 20.0,
            offset: float = 10.0,
            vmin: float | None = None,
            vmax: float | None = None,
            low_color: str = "#f7fbff",
            high_color: str = "#08306b",
            missing_color: str = "white",
            border_color: str = "none",
            border_width: float = 0.5
        ):
            """Add a vertical heatmap strip next to the tree tips."""
            
            # 1. Normalize values to dict
            if hasattr(values, "to_dict") and not isinstance(values, dict):
                values = values.to_dict()
            if hasattr(values, "columns") and hasattr(values, "to_dict") and not isinstance(values, dict):
                cols = list(values.columns)
                if len(cols) >= 2:
                    values = dict(zip(values[cols[0]].astype(str), values[cols[1]].astype(float)))
                else:
                    values = {}

            # 2. Helper: Parse Color (Hex or Name) to RGB Tuple
            def _to_rgb(color_str):
                color_str = str(color_str).strip()
                
                # Handle Hex (e.g., #FF0000 or #F00)
                if color_str.startswith("#"):
                    h = color_str.lstrip("#")
                    if len(h) == 3: # Expand shorthand #fff -> #ffffff
                        h = "".join([c*2 for c in h])
                    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                
                # Handle Basic Names
                # (Simple lookup to avoid dependencies like matplotlib)
                common_names = {
                    "white": (255, 255, 255), "black": (0, 0, 0),
                    "red": (255, 0, 0),       "green": (0, 128, 0),
                    "blue": (0, 0, 255),      "orange": (255, 165, 0),
                    "purple": (128, 0, 128),  "yellow": (255, 255, 0),
                    "gray": (128, 128, 128),  "grey": (128, 128, 128),
                    "cyan": (0, 255, 255),    "magenta": (255, 0, 255),
                    "lime": (0, 255, 0),      "darkgreen": (0, 100, 0),
                    "navy": (0, 0, 128),      "teal": (0, 128, 128)
                }
                if color_str.lower() in common_names:
                    return common_names[color_str.lower()]
                
                # Fallback if unknown name
                raise ValueError(f"Heatmap interpolation needs Hex codes (e.g. '#ff0000'). Unknown name: '{color_str}'")

            def _rgb_to_hex(rgb): 
                return "#{:02x}{:02x}{:02x}".format(*rgb)
            
            # 3. Prepare data
            vals = [float(v) for v in values.values() if isinstance(v, (int, float))]
            if not vals: return
            
            vmin = vmin if vmin is not None else min(vals)
            vmax = vmax if vmax is not None else max(vals)
            if vmax == vmin: vmax = vmin + 1e-12
            
            # Convert start/end colors to RGB for math
            c0 = _to_rgb(low_color)
            c1 = _to_rgb(high_color)
            
            # 4. Draw Rectangles
            # Calculate X position
            max_x = max(l.coordinates[0] for l in self.t.get_leaves())
            start_x = max_x + offset

            leaves = self.t.get_leaves()
            # Calculate height of each block (distance between leaves)
            if len(leaves) > 1:
                y_coords = sorted([l.y_coord for l in leaves])
                # Estimate step size from the smallest difference (handles irregular trees better)
                diffs = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1)]
                y_step = min(diffs) if diffs else 20
                # If step is tiny (overlap), use average
                if y_step < 1: 
                    y_step = abs(leaves[1].y_coord - leaves[0].y_coord)
            else:
                y_step = 20 

            for l in leaves:
                name = str(l.name)
                fill = missing_color
                
                if name in values:
                    try:
                        val = float(values[name])
                        # Interpolate
                        t = (val - vmin) / (vmax - vmin)
                        t = max(0.0, min(1.0, t))
                        
                        r = int(c0[0] + (c1[0]-c0[0]) * t)
                        g = int(c0[1] + (c1[1]-c0[1]) * t)
                        b = int(c0[2] + (c1[2]-c0[2]) * t)
                        fill = _rgb_to_hex((r,g,b))
                    except Exception:
                        pass # Keep missing_color
                
                # Center rectangle on leaf Y
                self.d.append(draw.Rectangle(
                    start_x, 
                    l.y_coord - y_step/2, 
                    width, 
                    y_step, 
                    fill=fill, 
                    stroke=border_color, 
                    stroke_width=border_width
                ))


    def add_leaf_images(self, image_dir, extension=".png", width=40, height=40, offset=10, rotation=0):
        """
        Adds PNG images to the right of each leaf node with a rotation option.
        :param rotation: Degrees to rotate the image (clockwise).
        """
        import os
        import base64

        # 1. Coordinate check: Ensure we have the latest positions
        if not hasattr(self.t, 'coordinates'):
            self._calculate_layout()

        for leaf in self.t.get_leaves():
            lx, ly = leaf.coordinates
            
            # 2. Coordinate Math
            img_x = lx + offset
            img_y = ly - (height / 2)

            img_path = os.path.join(image_dir, f"{leaf.name}{extension}")
            
            if os.path.exists(img_path):
                # 3. Manual Embedding
                with open(img_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    data_uri = f"data:image/png;base64,{encoded_string}"
                
                # 4. Rotation Logic
                # We rotate around the center of the image (img_x + width/2, img_y + height/2)
                transform_str = ""
                if rotation != 0:
                    center_x = img_x + (width / 2)
                    center_y = img_y + (height / 2)
                    transform_str = f"rotate({rotation}, {center_x}, {center_y})"

                # Create the image object
                img_obj = draw.Image(
                    img_x, img_y, 
                    width, height, 
                    path=data_uri,
                    transform=transform_str # Apply the rotation transform
                )
                
                self.d.append(img_obj)
            else:
                print(f"MISSING IMAGE: No file at {img_path}")


    def add_ancestral_images(self, image_dir, extension=".png", width=40, height=40, rotation=0, omit=None):
            """
            Adds PNG images centered on ancestral (internal) nodes.
            :param rotation: Degrees to rotate the image (clockwise).
            """
            import os
            import base64

            # 1. Coordinate check: Ensure we have the latest positions
            if not hasattr(self.t, 'coordinates'):
                self._calculate_layout()

            # Traverse all nodes but filter for internal ones
            for node in self.t.traverse():
                if not node.is_leaf():

                    if omit and node.name in omit:
                        continue # Skip omitted names

                    nx, ny = node.coordinates #
                    
                    # 2. Centering Math
                    # To make the center of the image coincide with the node,
                    # we subtract half the width/height from the top-left anchor.
                    img_x = nx - (width / 2)
                    img_y = ny - (height / 2)

                    img_path = os.path.join(image_dir, f"{node.name}{extension}")
                    
                    if os.path.exists(img_path):
                        # 3. Manual Embedding
                        with open(img_path, "rb") as img_file:
                            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                            data_uri = f"data:image/png;base64,{encoded_string}"
                        
                        # 4. Rotation Logic (Centered)
                        transform_str = ""
                        if rotation != 0:
                            transform_str = f"rotate({rotation}, {nx}, {ny})"

                        # Create the image object centered on (nx, ny)
                        img_obj = draw.Image(
                            img_x, img_y, 
                            width, height, 
                            path=data_uri,
                            transform=transform_str
                        )
                        
                        self.d.append(img_obj)
                    else:
                        # Optional: Print warning for missing ancestral names
                        # print(f"MISSING ANCESTRAL IMAGE: {img_path}")
                        pass

    def plot_continuous_variable(self, node_to_rgb, size=None):
            """
            Colors branches using a gradient based on RGB values at each node.
            :param node_to_rgb: Dictionary mapping node names or objects to (r, g, b) tuples.
            :param size: Thickness of the branches.
            """
            def _to_hex(rgb):
                return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))

            for node in self.t.traverse():
                if node.is_root():
                    continue
                    
                parent = node.up
                
                # Get RGB for current node and its parent
                # Supporting both node objects and node names as keys
                color_child = node_to_rgb.get(node) or node_to_rgb.get(node.name)
                color_parent = node_to_rgb.get(parent) or node_to_rgb.get(parent.name)

                if color_child and color_parent:
                    # Use the existing gradient_branch logic
                    self.gradient_branch(
                        node, 
                        colors=(_to_hex(color_parent), _to_hex(color_child)), 
                        size=size
                    )
                else:
                    # Fallback to standard highlighting if data is missing
                    self.highlight_branch(node, color=self.style.branch_color, size=size)
                    # Fallback to standard highlighting if data is missing
                    self.highlight_branch(node, color=self.style.branch_color, size=size)