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
                # Default: only radial drawers will have "angle"
                if hasattr(leaf, "angle"):
                    base_rot = float(leaf.angle) + float(getattr(self.style, "rotation", 0.0))
                    if o == "radial":
                        rot = base_rot
                    elif o == "tangent":
                        rot = base_rot + 90.0

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

    def add_branch_shapes(
         self,
         specs: list[dict],
         default_where: float = 0.5,
         orient: str | None = None,  # "along" or "perp"
         offset: float = 0.0,        # perpendicular offset in px
     ) -> None:
         """
         Add shapes on branches.
 
         Each spec dict can include:
           branch (str|node), where, shape, fill, size, stroke, stroke_width, rotation, opacity
         """
    
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

             where = float(s.get("where", default_where))
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