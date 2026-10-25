"""Rendering backend — the only module that touches drawsvg.

A :class:`Canvas` maps a layout's abstract coordinates onto a pixel page and offers two kinds of
drawing: **data-space** (``line`` / ``gradient_line`` / ``text``) for tree elements, transformed
through the layout extent, and **pixel-space** (``raw_*`` / ``gradient_bar``) for chrome that sits at a
fixed spot (colour bars, axes, titles). Saving to ``.svg`` needs nothing; ``.pdf`` / ``.png`` go
through cairosvg, falling back to ``.svg`` (with a note) when it is absent.
"""

from __future__ import annotations

import math
import re
import warnings
from collections.abc import Collection
from pathlib import Path

import drawsvg as draw

from .color import colormap_hex
from .style import Style

#: Families already probed, so a figure drawn in a loop pays for the check once.
_FONT_SEEN: dict[str, bool] = {}

#: A name no machine has, to render the fallback face and compare against.
_NO_SUCH_FONT = "phylustrator no such font 8f3a"

#: The faces a renderer falls back **to** when a family is missing. One of these, asked for by
#: name, draws the same pixels as a missing font — it is what a missing font turns into — so the
#: comparison below cannot tell the two apart, and silence is the right answer: a figure asked for
#: in Helvetica and drawn in Helvetica is the figure that was asked for. The cost is that a machine
#: genuinely missing one of these names is not warned about it.
_FALLBACK_FACES = frozenset({"helvetica", "arial", "dejavu sans", "liberation sans", "nimbus sans",
                             "sans", "sans-serif", "freesans"})


def font_is_available(family: str) -> bool:
    """Whether the PNG/PDF renderer can actually find ``family``.

    There is no asking it: a missing family is substituted silently, and the figure comes back in
    the fallback face — usually a sans one, which is the opposite of what a serif figure asked for.
    So the family is drawn twice, once as asked and once under a name nothing can have, and the two
    images are compared. Same image, same font, and the one you asked for is not installed.

    A family that **is** the fallback face draws the fallback's pixels for the honest reason, so
    those names (:data:`_FALLBACK_FACES`) answer ``True`` rather than raising a false alarm on every
    default figure. Any other failure answers ``True`` too: a check that cannot run must not stop a
    figure from being saved."""
    if family in _FONT_SEEN:
        return _FONT_SEEN[family]
    if family.strip().lower() in _FALLBACK_FACES:
        _FONT_SEEN[family] = True
        return True
    try:
        import cairosvg

        def pixels(name):
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="26">'
                   f'<text x="2" y="19" font-size="17" font-family="{name}">Hamburgefons</text></svg>')
            return cairosvg.svg2png(bytestring=svg.encode())

        _FONT_SEEN[family] = pixels(family) != pixels(_NO_SUCH_FONT)
    except Exception:
        _FONT_SEEN[family] = True
    return _FONT_SEEN[family]


def _rename_ids(svg: str, tag: str) -> str:
    """Give every id in one SVG document a prefix, and follow it into the places that point at it:
    ``url(#id)`` (a gradient or a filter) and ``href="#id"`` (a ``<use>``)."""
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for name in sorted(ids, key=len, reverse=True):          # longest first: ids can share a prefix
        new = f"{tag}-{name}"
        svg = svg.replace(f'id="{name}"', f'id="{new}"')
        svg = svg.replace(f"url(#{name})", f"url(#{new})")
        svg = svg.replace(f'href="#{name}"', f'href="#{new}"')
    return svg


class Canvas:
    """A pixel canvas with a data→pixel transform fixed by the layout's extent."""

    def __init__(self, style: Style, xlim: tuple[float, float], ylim: tuple[float, float],
                 *, equal_aspect: bool = False) -> None:
        self.style = style
        self.scale = None  # set by a colouring layer; read by colorbar()/legend()
        # How far into each margin the layers drawn so far have written: the names beside the tips,
        # the chips past them, the axis under the tree. A key asked to sit **outside** the panel
        # starts past this, so it lands beside the figure instead of on top of its own tip labels.
        # Keyed by side; a side nothing has claimed is absent.
        self._claimed: dict[str, float] = {}
        self._units: str | None = None       # a physical page size, set by physical_size()
        # Boxes a later layer must not cover: the tip names, the chips past them. A key measures
        # the branches itself — it has the tree — but it cannot know what text another layer wrote
        # or how wide it came out, so the layer that wrote it says so.
        self._obstacles: list[tuple[float, float, float, float]] = []
        # node names whose branch is dashed; set by the tree figure, read by a colouring layer
        self.dashed: Collection[str] | None = None
        self._d = draw.Drawing(style.width, style.height, origin=(0, 0))
        if style.background:
            self._d.append(draw.Rectangle(0, 0, style.width, style.height, fill=style.background))
        self._x0, self._x1 = xlim
        self._y0, self._y1 = ylim
        self._left = style.margin_at("left")
        self._right = style.margin_at("right")
        self._bottom = style.margin_at("bottom")
        self._top = style.margin_at("top") + getattr(style, "headroom", 0.0)
        # equal_aspect keeps circles round (radial/unrooted): one scale for x and y, centred.
        self._equal = None
        if equal_aspect:
            xspan = (self._x1 - self._x0) or 1.0
            yspan = (self._y1 - self._y0) or 1.0
            s = min((style.width - self._left - self._right) / xspan,
                    (style.height - self._bottom - self._top) / yspan)
            # centred between the margins; headroom shrinks the scale but does not shift the centre
            cx = (self._left + style.width - self._right) / 2
            cy = (style.margin_at("top") + style.height - self._bottom) / 2
            self._equal = (s, cx - s * (self._x0 + self._x1) / 2,
                           cy - s * (self._y0 + self._y1) / 2)

    def obstruct(self, x0: float, y0: float, x1: float, y1: float) -> None:
        """Record a pixel box that a key placed later must not cover."""
        self._obstacles.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))

    def obstacles(self) -> list:
        """Every box recorded so far, in the order it was drawn."""
        return list(self._obstacles)

    def claim(self, side: str, edge: float) -> None:
        """Record that something has been drawn out to pixel ``edge`` in the ``"right"`` (or
        ``"bottom"``) margin. The furthest claim wins, so the order the layers were added in does
        not change where a key beside the figure ends up."""
        if side not in ("right", "bottom"):
            raise ValueError(f"a margin claim is for 'right' or 'bottom', not {side!r}")
        self._claimed[side] = max(edge, self._claimed.get(side, edge))

    def claimed(self, side: str, default: float) -> float:
        """The furthest edge claimed on ``side``, or ``default`` when nothing has claimed it."""
        return self._claimed.get(side, default)

    # --- data-space (transformed through the layout extent) ---------------

    def px(self, x: float) -> float:
        if self._equal:
            s, ox, _ = self._equal
            return ox + s * x
        span = (self._x1 - self._x0) or 1.0
        return self._left + (x - self._x0) / span * (self.style.width - self._left - self._right)

    def py(self, y: float) -> float:
        if self._equal:
            s, _, oy = self._equal
            return oy + s * y
        span = (self._y1 - self._y0) or 1.0
        return self._top + (y - self._y0) / span * (self.style.height - self._bottom - self._top)

    def line(self, x1, y1, x2, y2, color: str, width: float, *, dash: bool = False,
             opacity: float = 1.0, cap: str | None = None) -> None:
        """A line in *data* coordinates. ``cap`` overrides the line ending for this one call
        (``"butt"`` squares off a wide bar that would otherwise read as longer than it is), and
        ``opacity`` fades it, so a broad mark drawn over the tree does not hide it. Left out, the
        ending is the style's ``line_cap`` — a dashed line is always squared off, or each dash grows
        a cap of its own and the gaps close up."""
        extra: dict = {"stroke_dasharray": "5,4"} if dash else {}
        if opacity < 1.0:
            extra["stroke_opacity"] = opacity
        self._d.append(draw.Line(self.px(x1), self.py(y1), self.px(x2), self.py(y2),
                                 stroke=color, stroke_width=width,
                                 stroke_linecap=cap or ("butt" if dash else self.style.line_cap),
                                 **extra))

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
        """A label in *data* coordinates — a node's own name, so it is written in the style's
        ``label_style``. The chrome (title, key, axis) goes through ``raw_text`` and stays roman."""
        self.raw_text(self.px(x) + dx, self.py(y) + dy, s, anchor=anchor, color=color, size=size,
                      style=self.style.label_style, family=self.style.label_family)

    # --- pixel-space (fixed page position) --------------------------------

    def raw_line(self, x1, y1, x2, y2, color: str, width: float) -> None:
        self._d.append(draw.Line(x1, y1, x2, y2, stroke=color, stroke_width=width))

    def raw_text(self, x, y, s: str, *, anchor="start", baseline="central",
                 color: str | None = None, size: float | None = None, weight="normal",
                 rotate: float = 0.0, style: str = "normal", family: str | None = None) -> None:
        extra = {"transform": f"rotate({rotate} {x} {y})"} if rotate else {}
        if style != "normal":
            extra["font_style"] = style
        self._d.append(draw.Text(s, size or self.style.font_size, x, y,
                                 fill=color or self.style.label_color,
                                 font_family=family or self.style.font_family,
                                 text_anchor=anchor, dominant_baseline=baseline, font_weight=weight, **extra))

    def raw_rect(self, x, y, w, h, *, fill, stroke="none", stroke_width=0.0, opacity=1.0,
                 rx=0.0) -> None:
        self._d.append(draw.Rectangle(x, y, w, h, fill=fill, stroke=stroke, rx=rx,
                                      stroke_width=stroke_width, fill_opacity=opacity))

    def raw_polygon(self, points, *, fill, stroke="none", stroke_width=0.0, opacity=1.0) -> None:
        """A filled polygon in **pixel** space — the twin of :meth:`polygon`, for a panel that is
        handed its row positions in pixels and so has no data coordinates of its own."""
        flat = [c for xy in points for c in xy]
        self._d.append(draw.Lines(*flat, fill=fill, fill_opacity=opacity, stroke=stroke,
                                  stroke_width=stroke_width, close=True))

    def raw_path(self, d: str, *, fill: str = "none", stroke: str = "none",
                 stroke_width: float = 0.0, opacity: float = 1.0, cap: str | None = None,
                 join: str = "round", dash: str | None = None) -> None:
        """An arbitrary SVG path in **pixel** space, from its ``d`` string.

        The escape hatch: everything else here draws one named shape, and a figure that needs a
        rounded bend, a tube's outline or a lineage cut to part of a branch has none to ask for. It
        was that or splicing hand-written paths into the output of :meth:`as_svg`, which is outside
        the library and breaks the moment the rest of it changes.

        ``d`` is passed through as written, so it is the caller's to get right — the one place in
        Phylustrator where that is true. ``cap`` defaults to the style's ``line_cap``, and ``join``
        says how two segments meet (``"round"``, ``"miter"`` for the angular corners of a LaTeX
        diagram, or ``"bevel"``). ``dash`` is an SVG dash array, e.g. ``"5,4"``."""
        extra: dict = {}
        if opacity < 1.0:
            extra["fill_opacity"] = opacity
            extra["stroke_opacity"] = opacity
        if dash:
            extra["stroke_dasharray"] = dash
        self._d.append(draw.Path(d=d, fill=fill, stroke=stroke, stroke_width=stroke_width,
                                 stroke_linecap=cap or self.style.line_cap,
                                 stroke_linejoin=join, **extra))

    def raw_annulus_sector(self, cx, cy, r_in, r_out, a0, a1, *, fill,
                           stroke="#ffffff", stroke_width=0.5, opacity=1.0) -> None:
        """A filled arc segment (annulus sector) between angles ``a0..a1`` (radians) and radii
        ``r_in..r_out``, centred at pixel ``(cx, cy)`` — the building block of an outer ring around a
        radial tree."""
        a0d, a1d = math.degrees(a0), math.degrees(a1)
        p = draw.Path(fill=fill, fill_opacity=opacity, stroke=stroke,
                      stroke_opacity=opacity, stroke_width=stroke_width)
        p.arc(cx, cy, r_out, a0d, a1d, cw=True)
        p.arc(cx, cy, r_in, a1d, a0d, cw=False, include_m=False, include_l=True)
        p.Z()
        self._d.append(p)

    def raw_ribbon(self, xa0, xa1, ya, xb0, xb1, yb, *, fill: str, opacity: float = 0.32,
                   stroke: str = "none") -> None:
        """An S-curved band linking ``[xa0,xa1]`` at ``ya`` to ``[xb0,xb1]`` at ``yb``, in **pixel**
        space — :meth:`ribbon` for a panel placed by someone else (see :func:`~genustrator.genomes.panels.tracks`)."""
        my = (ya + yb) / 2.0
        p = draw.Path(fill=fill, fill_opacity=opacity, stroke=stroke, stroke_width=0.5)
        p.M(xa0, ya).L(xa1, ya)
        p.C(xa1, my, xb1, my, xb1, yb)
        p.L(xb0, yb)
        p.C(xb0, my, xa0, my, xa0, ya)
        p.Z()
        self._d.append(p)

    def region(self, x0, y0, x1, y1, *, fill, opacity=1.0, stroke="none", stroke_width=0.0,
               rx=0.0) -> None:
        """A filled rectangle given in *data* coordinates (shade a clade, mark a segment)."""
        px0, px1 = self.px(x0), self.px(x1)
        py0, py1 = self.py(y0), self.py(y1)
        self.raw_rect(min(px0, px1), min(py0, py1), abs(px1 - px0), abs(py1 - py0),
                      fill=fill, opacity=opacity, stroke=stroke, stroke_width=stroke_width, rx=rx)

    # --- genome primitives (gene arrows, synteny ribbons, coordinate rings, embedded rasters) ---

    def polygon(self, points, *, fill, stroke="none", stroke_width=0.0, opacity=1.0) -> None:
        """A filled polygon; ``points`` are ``(x, y)`` in *data* coordinates (gene arrows)."""
        flat = []
        for x, y in points:
            flat.append(self.px(x))
            flat.append(self.py(y))
        self._d.append(draw.Lines(*flat, fill=fill, fill_opacity=opacity, stroke=stroke,
                                  stroke_width=stroke_width, close=True))

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

    def data_ring(self, r: float, color: str, width: float, *, dash: bool = False,
                  centre: tuple[float, float] = (0.0, 0.0)) -> None:
        """A circle of *data* radius ``r`` (a chromosome backbone / ruler), on the data origin unless
        ``centre`` moves it — a karyotype draws each chromosome on its own centre."""
        cx, cy = self.px(centre[0]), self.py(centre[1])
        rpx = self.px(centre[0] + r) - cx
        extra = {"stroke_dasharray": "5,4"} if dash else {}
        self._d.append(draw.Circle(cx, cy, abs(rpx), fill="none", stroke=color,
                                   stroke_width=width, **extra))

    def embed_png(self, data: bytes, x, y, w, h) -> None:
        """Place a PNG (bytes) at pixel ``(x, y)`` sized ``w×h`` — drops a rendered tree into a
        composite figure (see :func:`~phylustrator.compose.beside`)."""
        self._d.append(draw.Image(x, y, w, h, data=data, embed=True, mime_type="image/png"))

    def embed_svg(self, svg: str, x: float, y: float, *, tag: str = "") -> None:
        """Nest another figure's SVG at pixel ``(x, y)``, **as vectors**.

        The twin of :meth:`embed_png`, and the one to prefer: a figure placed on a page this way
        keeps its text as text and its lines as lines, so a journal gets a vector page rather than a
        picture of one.

        Two figures on one page each bring their own ``<defs>``, and drawsvg numbers those ids from
        zero in every figure, so a gradient in the second would answer to the first one's name and
        the wrong colours would be drawn. Every id in the nested document is renamed with ``tag``
        first, references included."""
        body = svg.split("?>", 1)[-1].lstrip() if svg.lstrip().startswith("<?xml") else svg
        if tag:
            body = _rename_ids(body, tag)
        # a nested <svg> establishes its own viewport, so the child's own width/height and viewBox
        # go on doing the work and only its position has to be said here
        body = re.sub(r"<svg\b", f'<svg x="{x:g}" y="{y:g}"', body, count=1)
        self._d.append(draw.Raw(body))

    def raw_marker(self, cx, cy, shape: str, color: str, size: float, *,
                   stroke: str = "#ffffff", stroke_width: float = 0.8,
                   angle: float = 0.0, opacity: float = 1.0) -> None:
        """A small glyph at pixel ``(cx, cy)``: ``circle`` / ``square`` / ``triangle`` /
        ``triangle_right`` (points along the time axis, for a state transition) / ``diamond``
        (filled), ``star`` (five-pointed, for the one node a figure is about), ``ring`` (open), or
        ``cross`` (an ✕, for a loss).

        ``ring`` is the marker for something that is there but not counted — a lineage alive at the
        present that sampling did not take — which is why it is the same shape as ``circle`` and
        hollow rather than a shape of its own.

        ``opacity`` fades the whole glyph, for a mark weighted by how much it stands for. A fully
        opaque glyph writes no opacity attribute at all, so an unweighted figure is unchanged."""
        r = size
        fade = {} if opacity >= 1.0 else {"fill_opacity": opacity, "stroke_opacity": opacity}
        ink = {} if opacity >= 1.0 else {"stroke_opacity": opacity}
        if shape == "square":
            self._d.append(draw.Rectangle(cx - r, cy - r, 2 * r, 2 * r, fill=color,
                                          stroke=stroke, stroke_width=stroke_width, **fade))
        elif shape == "cross":
            for a, b, c, d in ((-r, -r, r, r), (-r, r, r, -r)):
                self._d.append(draw.Line(cx + a, cy + b, cx + c, cy + d, stroke=color,
                                         stroke_width=max(1.6, r * 0.55), stroke_linecap="round",
                                         **ink))
        elif shape in ("triangle", "triangle_right", "diamond", "star"):
            star = []
            for i in range(10):                      # alternate outer and inner points
                a = -math.pi / 2 + i * math.pi / 5
                reach = r if i % 2 == 0 else r * 0.42
                star.append((cx + reach * math.cos(a), cy + reach * math.sin(a)))
            pts = {"star": star,
                   "triangle": [(cx, cy - r), (cx + r, cy + r * 0.85),
                                (cx - r, cy + r * 0.85)],
                   # points along the time axis — a state transition carries its
                   # lineage forward into the new state
                   "triangle_right": [(cx + r, cy), (cx - r * 0.85, cy - r),
                                      (cx - r * 0.85, cy + r)],
                   "diamond": [(cx, cy - r), (cx + r, cy), (cx, cy + r),
                               (cx - r, cy)]}[shape]
            if angle:
                # rotate the glyph around its centre, so "along the time axis" can follow a
                # radial branch's direction rather than always pointing right
                ca, sa = math.cos(angle), math.sin(angle)
                pts = [(cx + (x - cx) * ca - (y - cy) * sa,
                        cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
            self._d.append(draw.Lines(*[c for p in pts for c in p], fill=color,
                                      stroke=stroke, stroke_width=stroke_width, close=True, **fade))
        elif shape == "ring":
            self._d.append(draw.Circle(cx, cy, r, fill="#ffffff", stroke=color,
                                       stroke_width=max(1.4, r * 0.45), **ink))
        else:
            self._d.append(draw.Circle(cx, cy, r, fill=color, stroke=stroke,
                                       stroke_width=stroke_width, **fade))

    def marker(self, x, y, shape: str, color: str, size: float, **kw) -> None:
        """A glyph placed at *data* coordinates (see :meth:`raw_marker`)."""
        self.raw_marker(self.px(x), self.py(y), shape, color, size, **kw)

    def arrow(self, x0, y0, x1, y1, color: str, width: float, *, curve: float = 20.0,
              head: float = 8.0, opacity: float = 1.0) -> None:
        """A curved arrow from *data* ``(x0, y0)`` to ``(x1, y1)``, head at the end — e.g. a gene
        transfer from a donor lineage to a recipient lineage. ``opacity`` fades it, for an arrow
        weighted by the count it stands for; a fully opaque arrow writes no opacity attribute."""
        self.raw_arrow(self.px(x0), self.py(y0), self.px(x1), self.py(y1), color, width,
                       curve=curve, head=head, opacity=opacity)

    def raw_arrow(self, ax, ay, bx, by, color: str, width: float, *, curve: float = 20.0,
                  head: float = 8.0, opacity: float = 1.0) -> None:
        """:meth:`arrow` in **pixel** space — for an arrow whose length is set in pixels rather than
        by two nodes, such as a transfer arriving from a donor that is not in the drawn tree.
        ``curve=0`` draws it straight."""
        fade = {} if opacity >= 1.0 else {"stroke_opacity": opacity}
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        cx, cy = (ax + bx) / 2 - dy / L * curve, (ay + by) / 2 + dx / L * curve   # bow sideways
        p = draw.Path(fill="none", stroke=color, stroke_width=width, **fade)
        p.M(ax, ay).Q(cx, cy, bx, by)
        self._d.append(p)
        ang = math.atan2(by - cy, bx - cx)                                        # tangent at the tip
        for s in (0.5, -0.5):
            self._d.append(draw.Line(bx, by, bx - head * math.cos(ang - s),
                                     by - head * math.sin(ang - s), stroke=color,
                                     stroke_width=width, stroke_linecap="round", **fade))

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

    #: The units a page may be sized in, besides pixels.
    PHYSICAL_UNITS = ("pt", "mm", "cm", "in", "px")

    def physical_size(self, units: str) -> None:
        """Give the page a physical size — ``"pt"``, ``"mm"``, ``"cm"``, ``"in"`` — leaving the
        drawing in pixels underneath.

        A journal asks for a figure one column wide, and a pixel is not a width you can promise. The
        numbers stay as they are and the unit is written on them: a 482-wide page in ``"pt"`` is
        482 pt across, and everything inside keeps its proportions through the viewBox."""
        if units not in self.PHYSICAL_UNITS:
            raise ValueError(f"units must be one of {', '.join(self.PHYSICAL_UNITS)}, not {units!r}")
        self._units = None if units == "px" else units

    def as_svg(self) -> str:
        svg = str(self._d.as_svg())
        if self._units:
            w, h = self.size
            svg = re.sub(r'width="[\d.]+" height="[\d.]+"',
                         f'width="{w:g}{self._units}" height="{h:g}{self._units}"', svg, count=1)
        return svg

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
            self._warn_about_missing_fonts()
            data = svg.encode()
            if ext == ".pdf":
                cairosvg.svg2pdf(bytestring=data, write_to=str(path))
            else:
                cairosvg.svg2png(bytestring=data, write_to=str(path), scale=2.0)
            return path
        raise ValueError(f"unsupported output extension {path.suffix!r}; use .svg, .pdf or .png")

    def _warn_about_missing_fonts(self) -> None:
        """Say so when the family this figure asks for is not installed, rather than handing back a
        figure quietly set in something else. Only for PNG and PDF: an SVG carries the name and is
        resolved wherever it is opened."""
        for family in dict.fromkeys(f for f in (self.style.font_family, self.style.label_family)
                                    if f and "," not in f):
            if not font_is_available(family):
                warnings.warn(f"the font {family!r} is not installed, so this PNG/PDF is being set "
                              f"in the fallback face — usually a sans one, whatever the figure "
                              f"asked for. Install it, or pass a family this machine has. Saving "
                              f"to .svg instead keeps the name for whoever opens it.", stacklevel=3)


