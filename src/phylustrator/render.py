"""Rendering backend — the only module that touches drawsvg.

A :class:`Canvas` maps a layout's abstract coordinates onto a pixel page and offers two kinds of
drawing: **data-space** (``line`` / ``gradient_line`` / ``text``) for tree elements, transformed
through the layout extent, and **pixel-space** (``raw_*`` / ``gradient_bar``) for chrome that sits at a
fixed spot (colour bars, axes, titles). Saving to ``.svg`` needs nothing; ``.pdf`` / ``.png`` go
through cairosvg, falling back to ``.svg`` (with a note) when it is absent.
"""

from __future__ import annotations

import math
from pathlib import Path

import drawsvg as draw

from .color import colormap_hex
from .style import Style


class Canvas:
    """A pixel canvas with a data→pixel transform fixed by the layout's extent."""

    def __init__(self, style: Style, xlim: tuple[float, float], ylim: tuple[float, float],
                 *, equal_aspect: bool = False) -> None:
        self.style = style
        self.scale = None  # set by a colouring layer; read by colorbar()/legend()
        self._d = draw.Drawing(style.width, style.height, origin=(0, 0))
        if style.background:
            self._d.append(draw.Rectangle(0, 0, style.width, style.height, fill=style.background))
        self._x0, self._x1 = xlim
        self._y0, self._y1 = ylim
        self._m = style.margin
        # equal_aspect keeps circles round (radial/unrooted): one scale for x and y, centred.
        self._equal = None
        if equal_aspect:
            xspan = (self._x1 - self._x0) or 1.0
            yspan = (self._y1 - self._y0) or 1.0
            s = min((style.width - 2 * self._m) / xspan, (style.height - 2 * self._m) / yspan)
            self._equal = (s, style.width / 2 - s * (self._x0 + self._x1) / 2,
                           style.height / 2 - s * (self._y0 + self._y1) / 2)

    # --- data-space (transformed through the layout extent) ---------------

    def px(self, x: float) -> float:
        if self._equal:
            s, ox, _ = self._equal
            return ox + s * x
        span = (self._x1 - self._x0) or 1.0
        return self._m + (x - self._x0) / span * (self.style.width - 2 * self._m)

    def py(self, y: float) -> float:
        if self._equal:
            s, _, oy = self._equal
            return oy + s * y
        span = (self._y1 - self._y0) or 1.0
        return self._m + (y - self._y0) / span * (self.style.height - 2 * self._m)

    def line(self, x1, y1, x2, y2, color: str, width: float, *, dash: bool = False) -> None:
        extra = {"stroke_dasharray": "5,4"} if dash else {}
        self._d.append(draw.Line(self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                                 stroke=color, stroke_width=width,
                                 stroke_linecap="butt" if dash else "round", **extra))

    def gradient_line(self, x1, y1, x2, y2, color1: str, color2: str, width: float) -> None:
        """A branch coloured with a gradient from ``color1`` (start) to ``color2`` (end)."""
        grad = draw.LinearGradient(self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                                   gradientUnits="userSpaceOnUse")
        grad.add_stop(0, color1)
        grad.add_stop(1, color2)
        self._d.append(grad)
        self._d.append(draw.Line(self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                                 stroke=grad, stroke_width=width, stroke_linecap="round"))

    def text(self, x, y, s: str, *, dx=0.0, dy=0.0, anchor="start",
             color: str | None = None, size: float | None = None) -> None:
        self.raw_text(self.px(x) + dx, self.py(y) + dy, s, anchor=anchor, color=color, size=size)

    # --- pixel-space (fixed page position) --------------------------------

    def raw_line(self, x1, y1, x2, y2, color: str, width: float) -> None:
        self._d.append(draw.Line(x1, y1, x2, y2, stroke=color, stroke_width=width))

    def raw_text(self, x, y, s: str, *, anchor="start", baseline="central",
                 color: str | None = None, size: float | None = None, weight="normal",
                 rotate: float = 0.0) -> None:
        extra = {"transform": f"rotate({rotate} {x} {y})"} if rotate else {}
        self._d.append(draw.Text(s, size or self.style.font_size, x, y,
                                 fill=color or self.style.label_color, font_family=self.style.font_family,
                                 text_anchor=anchor, dominant_baseline=baseline, font_weight=weight, **extra))

    def raw_rect(self, x, y, w, h, *, fill, stroke="none", stroke_width=0.0, opacity=1.0,
                 rx=0.0) -> None:
        self._d.append(draw.Rectangle(x, y, w, h, fill=fill, stroke=stroke, rx=rx,
                                      stroke_width=stroke_width, fill_opacity=opacity))

    def region(self, x0, y0, x1, y1, *, fill, opacity=1.0, stroke="none", stroke_width=0.0,
               rx=0.0) -> None:
        """A filled rectangle given in *data* coordinates (shade a clade, mark a segment)."""
        px0, px1 = self.px(x0), self.px(x1)
        py0, py1 = self.py(y0), self.py(y1)
        self.raw_rect(min(px0, px1), min(py0, py1), abs(px1 - px0), abs(py1 - py0),
                      fill=fill, opacity=opacity, stroke=stroke, stroke_width=stroke_width, rx=rx)

    # --- genome primitives (gene arrows, synteny ribbons, coordinate rings, embedded rasters) ---

    def polygon(self, points, *, fill, stroke="none", stroke_width=0.0) -> None:
        """A filled polygon; ``points`` are ``(x, y)`` in *data* coordinates (gene arrows)."""
        flat = []
        for x, y in points:
            flat.append(self.px(x))
            flat.append(self.py(y))
        self._d.append(draw.Lines(*flat, fill=fill, stroke=stroke, stroke_width=stroke_width,
                                  close=True))

    def ribbon(self, xa0, xa1, ya, xb0, xb1, yb, *, fill: str, opacity: float = 0.32,
               stroke: str = "none") -> None:
        """A filled S-curved band linking footprint ``[xa0,xa1]`` at ``ya`` to ``[xb0,xb1]`` at ``yb``
        (all *data* coordinates) — a synteny link between two stacked genomes."""
        ax0, ax1, ay = self.px(xa0), self.px(xa1), self.py(ya)
        bx0, bx1, by = self.px(xb0), self.px(xb1), self.py(yb)
        my = (ay + by) / 2.0
        p = draw.Path(fill=fill, fill_opacity=opacity, stroke=stroke, stroke_width=0.5)
        p.M(ax0, ay).L(ax1, ay)
        p.C(ax1, my, bx1, my, bx1, by)
        p.L(bx0, by)
        p.C(bx0, my, ax0, my, ax0, ay)
        p.Z()
        self._d.append(p)

    def data_ring(self, r: float, color: str, width: float, *, dash: bool = False) -> None:
        """A circle of *data* radius ``r`` centred on the data origin (a chromosome backbone / ruler)."""
        cx, cy = self.px(0.0), self.py(0.0)
        rpx = self.px(r) - cx
        extra = {"stroke_dasharray": "5,4"} if dash else {}
        self._d.append(draw.Circle(cx, cy, abs(rpx), fill="none", stroke=color,
                                   stroke_width=width, **extra))

    def embed_png(self, data: bytes, x, y, w, h) -> None:
        """Place a PNG (bytes) at pixel ``(x, y)`` sized ``w×h`` — drops a rendered tree into a
        composite figure (see :func:`~phylustrator.compose.beside`)."""
        self._d.append(draw.Image(x, y, w, h, data=data, embed=True, mime_type="image/png"))

    def raw_marker(self, cx, cy, shape: str, color: str, size: float, *,
                   stroke: str = "#ffffff", stroke_width: float = 0.8) -> None:
        """A small glyph at pixel ``(cx, cy)``: ``circle`` / ``square`` / ``triangle`` / ``diamond``
        (filled) or ``cross`` (an ✕, for a loss)."""
        r = size
        if shape == "square":
            self._d.append(draw.Rectangle(cx - r, cy - r, 2 * r, 2 * r, fill=color,
                                          stroke=stroke, stroke_width=stroke_width))
        elif shape == "cross":
            for a, b, c, d in ((-r, -r, r, r), (-r, r, r, -r)):
                self._d.append(draw.Line(cx + a, cy + b, cx + c, cy + d, stroke=color,
                                         stroke_width=max(1.6, r * 0.55), stroke_linecap="round"))
        elif shape in ("triangle", "diamond"):
            pts = ([(cx, cy - r), (cx + r, cy + r * 0.85), (cx - r, cy + r * 0.85)]
                   if shape == "triangle"
                   else [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])
            self._d.append(draw.Lines(*[c for p in pts for c in p], fill=color,
                                      stroke=stroke, stroke_width=stroke_width, close=True))
        else:
            self._d.append(draw.Circle(cx, cy, r, fill=color, stroke=stroke,
                                       stroke_width=stroke_width))

    def marker(self, x, y, shape: str, color: str, size: float, **kw) -> None:
        """A glyph placed at *data* coordinates (see :meth:`raw_marker`)."""
        self.raw_marker(self.px(x), self.py(y), shape, color, size, **kw)

    def arrow(self, x0, y0, x1, y1, color: str, width: float, *, curve: float = 20.0,
              head: float = 8.0) -> None:
        """A curved arrow from *data* ``(x0, y0)`` to ``(x1, y1)``, head at the end — e.g. a gene
        transfer from a donor lineage to a recipient lineage."""
        ax, ay, bx, by = self.px(x0), self.py(y0), self.px(x1), self.py(y1)
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        cx, cy = (ax + bx) / 2 - dy / L * curve, (ay + by) / 2 + dx / L * curve   # bow sideways
        p = draw.Path(fill="none", stroke=color, stroke_width=width)
        p.M(ax, ay).Q(cx, cy, bx, by)
        self._d.append(p)
        ang = math.atan2(by - cy, bx - cx)                                        # tangent at the tip
        for s in (0.5, -0.5):
            self._d.append(draw.Line(bx, by, bx - head * math.cos(ang - s),
                                     by - head * math.sin(ang - s), stroke=color,
                                     stroke_width=width, stroke_linecap="round"))

    def gradient_bar(self, cmap: str, x, y, w, h) -> None:
        """A horizontal rectangle filled with the multi-stop gradient of ``cmap``."""
        grad = draw.LinearGradient(x, y, x + w, y, gradientUnits="userSpaceOnUse")
        stops = colormap_hex(cmap)
        for i, c in enumerate(stops):
            grad.add_stop(i / (len(stops) - 1), c)
        self._d.append(grad)
        self._d.append(draw.Rectangle(x, y, w, h, fill=grad, stroke="#666", stroke_width=0.5))

    @property
    def size(self) -> tuple[float, float]:
        return self.style.width, self.style.height

    # --- output -----------------------------------------------------------

    def as_svg(self) -> str:
        return self._d.as_svg()

    def save(self, path: str | Path) -> Path:
        """Write the figure; format follows the extension (``.svg`` direct, ``.pdf`` / ``.png`` via
        cairosvg, falling back to ``.svg`` with a note if cairosvg is missing)."""
        path = Path(path)
        ext = path.suffix.lower()
        svg = self.as_svg()
        if ext == ".svg":
            path.write_text(svg)
            return path
        if ext in (".pdf", ".png"):
            try:
                import cairosvg
            except ImportError:
                fallback = path.with_suffix(".svg")
                fallback.write_text(svg)
                print(f"[phylustrator] cairosvg not installed — wrote {fallback.name} instead of "
                      f"{path.name}. Install phylustrator[export] for PDF/PNG.")
                return fallback
            data = svg.encode()
            if ext == ".pdf":
                cairosvg.svg2pdf(bytestring=data, write_to=str(path))
            else:
                cairosvg.svg2png(bytestring=data, write_to=str(path), scale=2.0)
            return path
        raise ValueError(f"unsupported output extension {path.suffix!r}; use .svg, .pdf or .png")
