"""Rendering backend — the only module that touches drawsvg.

A :class:`Canvas` maps a layout's abstract coordinates onto a pixel page and offers two kinds of
drawing: **data-space** (``line`` / ``gradient_line`` / ``text``) for tree elements, transformed
through the layout extent, and **pixel-space** (``raw_*`` / ``gradient_bar``) for chrome that sits at a
fixed spot (colour bars, axes, titles). Saving to ``.svg`` needs nothing; ``.pdf`` / ``.png`` go
through cairosvg, falling back to ``.svg`` (with a note) when it is absent.
"""

from __future__ import annotations

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

    def line(self, x1, y1, x2, y2, color: str, width: float) -> None:
        self._d.append(draw.Line(self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                                 stroke=color, stroke_width=width, stroke_linecap="round"))

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
                 color: str | None = None, size: float | None = None, weight="normal") -> None:
        self._d.append(draw.Text(s, size or self.style.font_size, x, y,
                                 fill=color or self.style.label_color, font_family=self.style.font_family,
                                 text_anchor=anchor, dominant_baseline=baseline, font_weight=weight))

    def raw_rect(self, x, y, w, h, *, fill, stroke="none", stroke_width=0.0, opacity=1.0) -> None:
        self._d.append(draw.Rectangle(x, y, w, h, fill=fill, stroke=stroke,
                                      stroke_width=stroke_width, fill_opacity=opacity))

    def region(self, x0, y0, x1, y1, *, fill, opacity=1.0) -> None:
        """A filled rectangle given in *data* coordinates (for shading a clade behind the tree)."""
        px0, px1 = self.px(x0), self.px(x1)
        py0, py1 = self.py(y0), self.py(y1)
        self.raw_rect(min(px0, px1), min(py0, py1), abs(px1 - px0), abs(py1 - py0),
                      fill=fill, opacity=opacity)

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
