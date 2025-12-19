import drawsvg as draw
from dataclasses import dataclass
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

    def save_figure(self, filename, scale=4.0):
        if filename.endswith(".svg"):
            self.d.save_svg(filename)
        else:
            import cairosvg
            svg_data = self.d.as_svg()
            if filename.endswith(".png"):
                cairosvg.svg2png(bytestring=svg_data, write_to=filename, scale=scale)
            elif filename.endswith(".pdf"):
                cairosvg.svg2pdf(bytestring=svg_data, write_to=filename)

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
