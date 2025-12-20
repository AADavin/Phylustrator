import drawsvg as draw
from dataclasses import dataclass
from pathlib import Path
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


    def _draw_shape_at(
        self,
        x: float,
        y: float,
        shape: str,
        fill: str,
        size: float,
        stroke: str | None,
        stroke_width: float,
        rotation: float = 0.0,
        opacity: float = 1.0,
    ) -> None:
        common = {"fill": fill, "opacity": opacity}
        if stroke is not None:
            common["stroke"] = stroke
            common["stroke_width"] = stroke_width

        shp = str(shape).lower()
        rot = float(rotation)

        # drawsvg uses SVG transforms; rotate around (x,y)
        transform = None if rot == 0 else f"rotate({rot},{x},{y})"

        if shp == "circle":
            self.d.append(draw.Circle(x, y, float(size) / 2.0, **common))
            return

        if shp == "square":
            s = float(size)
            self.d.append(
                draw.Rectangle(x - s / 2.0, y - s / 2.0, s, s, transform=transform, **common)
            )
            return

        if shp == "triangle":
            s = float(size)
            h = s * math.sqrt(3) / 2.0
            p1 = (x, y - (2.0 / 3.0) * h)
            p2 = (x - s / 2.0, y + (1.0 / 3.0) * h)
            p3 = (x + s / 2.0, y + (1.0 / 3.0) * h)

            path = draw.Path(transform=transform, **common)
            path.M(*p1).L(*p2).L(*p3).Z()
            self.d.append(path)
            return

        raise ValueError(f"Unknown shape: {shape!r}. Use circle/square/triangle.")



    def save_svg(self, outpath: str | Path) -> None:
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        self.d.save_svg(str(outpath))

    def save_png(self, outpath: str | Path, scale: float = 1.0) -> None:
        """
        Export PNG using CairoSVG (optional dependency).
        scale>1 increases resolution while keeping same logical size.
        """
        try:
            import cairosvg
        except ImportError as e:
            raise ImportError(
                "PNG export requires cairosvg. Install with: pip install 'phylustrator[export]'"
            ) from e

        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        
        svg_text = self.d.as_svg()
        cairosvg.svg2png(
            bytestring=svg_text.encode("utf-8"),
            write_to=str(outpath),
            scale=scale,
        )

    def add_legend(
        self,
        title: str,
        mapping: dict,
        position="top-left",
        symbol: str = "circle",
        text_size: int | None = None,
        padding: int = 20,
        box_padding: int = 10,
        box_fill: str = "white",
        box_opacity: float = 0.9,
        box_stroke: str = "black",
        box_stroke_width: float = 1.0,
        symbol_size: int = 10,
        row_gap: int = 6,
    ):
        """Add a simple categorical legend.

        Coordinates follow the library convention: origin at canvas center.

        Parameters
        ----------
        title:
            Legend title.
        mapping:
            Dict of {label: color}.
        position:
            "top-left", "top-right", "bottom-left", "bottom-right", or (x, y) tuple
            specifying the *top-left* corner of the legend box.
        symbol:
            "circle", "square", or "line".
        """
        if not mapping:
            return

        font_size = int(text_size) if text_size is not None else int(self.style.font_size)
        font_family = getattr(self.style, "font_family", "Arial")

        # --- Size estimation (SVG has no font metrics here, so we approximate) ---
        # Typical monospace-ish heuristic: average character ~0.6*font_size
        def est_width(s: str) -> float:
            return 0.6 * font_size * len(str(s))

        max_label_w = max([est_width(title)] + [est_width(k) for k in mapping.keys()])
        content_w = symbol_size + 8 + max_label_w
        n_rows = len(mapping)
        title_h = font_size + 4
        row_h = font_size + row_gap
        content_h = title_h + (n_rows * row_h)
        box_w = content_w + 2 * box_padding
        box_h = content_h + 2 * box_padding

        w, h = self.style.width, self.style.height

        # --- Anchor (top-left of legend box) ---
        if isinstance(position, tuple) and len(position) == 2:
            x0, y0 = position
        elif position == "top-left":
            x0, y0 = -w / 2 + padding, -h / 2 + padding
        elif position == "top-right":
            x0, y0 = w / 2 - padding - box_w, -h / 2 + padding
        elif position == "bottom-left":
            x0, y0 = -w / 2 + padding, h / 2 - padding - box_h
        elif position == "bottom-right":
            x0, y0 = w / 2 - padding - box_w, h / 2 - padding - box_h
        else:
            x0, y0 = -w / 2 + padding, -h / 2 + padding

        # Background box
        self.d.append(
            draw.Rectangle(
                x0,
                y0,
                box_w,
                box_h,
                fill=box_fill,
                opacity=box_opacity,
                stroke=box_stroke,
                stroke_width=box_stroke_width,
            )
        )

        # Title
        tx = x0 + box_padding
        ty = y0 + box_padding + font_size
        self.d.append(
            draw.Text(
                title,
                font_size + 1,
                tx,
                ty,
                font_family=font_family,
                font_weight="bold",
                fill="black",
            )
        )

        # Rows
        y = ty + (font_size + row_gap)
        sym_x = x0 + box_padding + symbol_size / 2
        text_x = x0 + box_padding + symbol_size + 8
        for label, color in mapping.items():
            if symbol == "circle":
                self.d.append(
                    draw.Circle(sym_x, y - font_size * 0.35, symbol_size / 2, fill=color, stroke="black", stroke_width=0.5)
                )
            elif symbol == "square":
                self.d.append(
                    draw.Rectangle(
                        sym_x - symbol_size / 2,
                        y - font_size * 0.85,
                        symbol_size,
                        symbol_size,
                        fill=color,
                        stroke="black",
                        stroke_width=0.5,
                    )
                )
            elif symbol == "line":
                self.d.append(
                    draw.Line(
                        sym_x - symbol_size / 2,
                        y - font_size * 0.5,
                        sym_x + symbol_size / 2,
                        y - font_size * 0.5,
                        stroke=color,
                        stroke_width=2,
                    )
                )

            self.d.append(draw.Text(str(label), font_size, text_x, y, font_family=font_family, fill="black"))
            y += row_h

    
    def add_scale_bar(
         self,
         length: float,
         label: str | None = None,
         x: float | None = None,
         y: float | None = None,
         stroke: str = "black",
         stroke_width: float = 2.0,
         tick_size: float = 6.0,
         font_size: int | None = None,
         font_family: str | None = None,
         padding: float = 10.0,
     ) -> None:
         """Add a simple scale bar (tree-length legend).

         Parameters
         ----------
         length
             Length in *tree units* (same units used to scale branches).
         label
             Text label. If None, uses the numeric length.
         x, y
             Anchor position (left end) in drawing coordinates. If omitted, places the
             bar near the bottom-left with padding.
         """
         px = float(length) * float(self.sf)
         if label is None:
             label = str(length)

         if x is None:
             x = -float(self.style.width) / 2.0 + float(padding)
         if y is None:
             y = float(self.style.height) / 2.0 - float(padding)

         fs = int(font_size) if font_size is not None else int(self.style.font_size)
         ff = font_family if font_family is not None else self.style.font_family

         # main bar
         self.d.append(draw.Line(x, y, x + px, y, stroke=stroke, stroke_width=stroke_width))
         # end ticks
         self.d.append(draw.Line(x, y - tick_size / 2.0, x, y + tick_size / 2.0, stroke=stroke, stroke_width=stroke_width))
         self.d.append(draw.Line(x + px, y - tick_size / 2.0, x + px, y + tick_size / 2.0, stroke=stroke, stroke_width=stroke_width))

         # label above the bar
         self.d.append(draw.Text(label, fs, x + px / 2.0, y - tick_size - 2, center=True, font_family=ff))

    def _leaf_xy(self, leaf, offset: float = 0.0) -> tuple[float, float]:
            """Return (x, y) coordinates for a leaf.

            Subclasses must implement this. The ``offset`` parameter is in pixels and
            should move the position away from the leaf tip (e.g., to the right for
            vertical trees, outward for radial trees).
            """
            raise NotImplementedError


    def add_leaf_shapes(
        self,
        leaves,
        shape: str = "circle",
        fill: str = "blue",
        size: float = 10,
        stroke: str | None = None,
        stroke_width: float = 1,
        offset: float = 0.0,
        rotation: float = 0.0,
        orient: str | None = None,   # NEW: "radial" or "tangent" (mainly for radial)
        opacity: float = 1.0,
    ):
        if leaves is None:
            return

        leaf_nodes = []
        for item in leaves:
            if isinstance(item, str):
                try:
                    leaf_nodes.append(self.t & item)  # ete3 lookup by name
                except Exception:
                    continue
            else:
                leaf_nodes.append(item)

        # ensure layout exists once if needed
        if leaf_nodes:
            if not hasattr(leaf_nodes[0], "rad") and not hasattr(leaf_nodes[0], "coordinates"):
                if hasattr(self, "_calculate_layout"):
                    self._calculate_layout()

        for leaf in leaf_nodes:
            x, y = self._leaf_xy(leaf, offset=float(offset))

            rot = float(rotation)
            if orient is not None:
                o = str(orient).lower().strip()

                # Use the actual rendered vector (x,y) in the drawing coordinate system.
                # SVG has y pointing DOWN, so atan2(y, x) yields a clockwise angle.
                a = math.degrees(math.atan2(y, x))

                # Our triangle path is "pointing up" when rotation=0,
                # so to point along direction angle 'a' we add +90 degrees.
                if o == "radial":
                    rot = a + 90.0
                elif o == "tangent":
                    rot = a + 180.0

            self._draw_shape_at(
                x=x, y=y,
                shape=shape,
                fill=fill,
                size=size,
                stroke=stroke,
                stroke_width=stroke_width,
                rotation=rot,
                opacity=opacity,
            )

    def _node_xy(self, node) -> tuple[float, float]:
        """Subclasses must implement: x,y coordinates of any node."""
        raise NotImplementedError

    def _edge_point(self, child, where: float) -> tuple[float, float, float]:
        """
        Default edge interpolation: straight line from parent to child.
        Returns (x,y,angle_degrees_along_edge).
        Subclasses can override (vertical should).
        """
        parent = child.up
        x0, y0 = self._node_xy(parent)
        x1, y1 = self._node_xy(child)

        t = max(0.0, min(1.0, float(where)))
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t

        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        return x, y, ang

    def _where_from_time(self, node, t: float) -> float:
        """
        Map absolute event time t to a [0,1] position along the incoming edge of `node`.
        Requires node.up.time_from_origin and node.time_from_origin (Zombi parser provides these).
        """
        parent = node.up
        if parent is None:
            return 0.0

        t0 = float(getattr(parent, "time_from_origin", 0.0))
        t1 = float(getattr(node, "time_from_origin", t0))
        denom = (t1 - t0) if abs(t1 - t0) > 1e-12 else 1.0

        w = (float(t) - t0) / denom
        if w < 0.0:
            return 0.0
        if w > 1.0:
            return 1.0
        return w


    def add_branch_shapes(
         self,
         specs,

         default_where: float = 0.5,
         orient: str | None = None,  # "along" or "perp"
         offset: float = 0.0,        # perpendicular offset in px
     ) -> None:
        """
         Add shapes on branches.
 
         Each spec dict can include:
           branch (str|node), where, shape, fill, size, stroke, stroke_width, rotation, opacity
        """
    
         
         # Accept either list[dict] or a DataFrame-like object (e.g. pandas.DataFrame)
        if hasattr(specs, "to_dict") and hasattr(specs, "columns"):
            specs = specs.to_dict(orient="records")

        for s in specs:
            br = s.get("branch", None)
            if br is None:
                continue

            # resolve
            if isinstance(br, str):
                try:
                    child = self.t & br
                except Exception:
                    continue
            else:
                child = br

            if child.up is None:
                continue  # no parent edge

            if "where" in s and s.get("where") is not None:
                where = float(s.get("where"))
            elif "time" in s and s.get("time") is not None and hasattr(child, "time_from_origin") and hasattr(child.up, "time_from_origin"):
                 where = float(self._where_from_time(child, float(s.get("time"))))
            else:
                where = float(default_where)
            x, y, edge_ang = self._edge_point(child, where=where)

            # optional perpendicular offset
            if offset != 0.0:
                perp = edge_ang + 90.0
                x += float(offset) * math.cos(math.radians(perp))
                y += float(offset) * math.sin(math.radians(perp))

            rot = float(s.get("rotation", 0.0))
            if orient is not None:
                o = str(orient).lower().strip()
                if o == "along":
                    rot = edge_ang
                elif o == "perp":
                    rot = edge_ang + 90.0

            self._draw_shape_at(
                x=x, y=y,
                shape=s.get("shape", "circle"),
                fill=s.get("fill", "blue"),
                size=float(s.get("size", 10)),
                stroke=s.get("stroke", None),
                stroke_width=float(s.get("stroke_width", 1)),
                rotation=rot,
                opacity=float(s.get("opacity", 1.0)),
            )

    def add_colorbar(
        self,
        vmin: float,
        vmax: float,
        low_color: str = "#f7fbff",
        high_color: str = "#08306b",
        label: str | None = None,
        ticks: list[float] | None = None,
        n_steps: int = 60,
        bar_width: float = 18.0,
        bar_height: float = 180.0,
        margin: float = 18.0,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
        label_pad: float = 10.0,
        tick_pad: float = 12.0,
        font_size: int | None = None,
        font_family: str | None = None,
        stroke: str = "black",
        stroke_width: float = 1.0,
    ):
        """Add a vertical colorbar to the drawing (top-right by default).

        You can reposition with x_offset / y_offset (in px), relative to top-right anchor.
        Coordinates assume drawsvg Drawing(origin='center').
        """
        def _hex_to_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        def _lerp(a: float, b: float, t: float) -> float:
            return a + (b - a) * t

        c0 = _hex_to_rgb(low_color)
        c1 = _hex_to_rgb(high_color)

        def _lerp_color(t: float) -> str:
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            r = int(_lerp(c0[0], c1[0], t))
            g = int(_lerp(c0[1], c1[1], t))
            b = int(_lerp(c0[2], c1[2], t))
            return _rgb_to_hex((r, g, b))

        fs = int(font_size) if font_size is not None else int(self.style.font_size)
        ff = font_family if font_family is not None else self.style.font_family

        # anchor top-right (origin is center)
        x0 = float(self.style.width) / 2.0 - float(margin) - float(bar_width) + float(x_offset)
        y_top = -float(self.style.height) / 2.0 + float(margin) + float(y_offset)

        # outline box
        self.d.append(draw.Rectangle(
            x0, y_top, bar_width, bar_height,
            fill="none", stroke=stroke, stroke_width=stroke_width
        ))

        # gradient fill as stacked rectangles
        steps = max(2, int(n_steps))
        step_h = float(bar_height) / steps
        for i in range(steps):
            t = i / (steps - 1)
            fill = _lerp_color(1.0 - t)  # high at top
            y = y_top + i * step_h
            self.d.append(draw.Rectangle(x0, y, bar_width, step_h + 0.5, fill=fill, stroke="none"))

        # default ticks
        if ticks is None:
            ticks = [vmin, (vmin + vmax) / 2.0, vmax]

        # tick marks + labels (right side)
        for tv in ticks:
            frac = 0.0 if vmax == vmin else (float(tv) - float(vmin)) / (float(vmax) - float(vmin))
            frac = 0.0 if frac < 0.0 else (1.0 if frac > 1.0 else frac)

            y = y_top + (1.0 - frac) * float(bar_height)
            self.d.append(draw.Line(
                x0 + bar_width, y,
                x0 + bar_width + 6, y,
                stroke=stroke, stroke_width=stroke_width
            ))
            self.d.append(draw.Text(
                str(tv), fs,
                x0 + bar_width + float(tick_pad), y + fs * 0.35,
                font_family=ff
            ))

        # label (above)
        if label:
            self.d.append(draw.Text(
                label, fs,
                x0 + bar_width / 2.0, y_top - float(label_pad),
                center=True, font_family=ff
            ))
