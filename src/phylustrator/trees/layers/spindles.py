"""The branch-spindles layer — mark an event on a branch as a spindle fused into the branch.

A spindle is a lens drawn along the branch at a time, in a colour. It sits on a stretch of the
branch in the same colour, and that stretch fades into the branch's own colour at both ends, so the
mark grows out of the line instead of floating on it.

Each mark is a dict ``{"node": name, "x": time, "color": colour, "size": length}`` or a plain
``(node, x, color)`` tuple. ``x`` is on the layout's distance axis, like ``branch_events``; without
it the spindle sits at the middle of the branch. ``color`` falls back to the layer's ``color``,
``size`` to the layer's ``length``. A mark outside its branch is pulled back onto it.
"""

from __future__ import annotations

import math


def _unpack(raw):
    if isinstance(raw, dict):
        return dict(raw)
    node, x, color = (list(raw) + [None, None])[:3]
    return {"node": node, "x": x, "color": color}


def branch_spindles(marks, *, length: float | None = None, height: float = 5.0,
                    fuse: float = 0.8, color: str = "#e07b00", opacity: float = 1.0):
    """Mark ``marks`` on the tree as spindles. ``length`` is the lens length in pixels (default: the
    shorter of 14 px and 80% of the branch); ``height`` its half-height in pixels; ``fuse`` how far
    the colour fades into the branch on each side, as a multiple of the lens length. Returns a
    layer."""

    def layer(canvas, tree, layout, style):
        by_name = {n.name: n for n in tree.walk() if n.name}
        radial = layout.kind == "radial"
        stem_off = float(tree.root.length or 0.0) if radial else 0.0

        def dist(node):
            return math.hypot(layout.x(node), layout.y(node)) if radial else layout.x(node)

        def place(node, t):
            if not radial:
                return t, layout.y(node)
            a = layout.angle[node]
            return t * math.cos(a), t * math.sin(a)

        for raw in marks:
            m = _unpack(raw)
            node = by_name.get(m.get("node"))
            if node is None:
                continue
            here = dist(node)
            up = dist(node.parent) if node.parent is not None else 0.0
            lo, hi = sorted((up, here))
            x = m.get("x")
            x = (lo + hi) / 2 if x is None else min(max(x - stem_off, lo), hi)
            col = m.get("color") or color

            # the branch direction in pixel space, from a point just before the mark to the mark
            mx, my = place(node, x)
            bx, by = place(node, max(x - 1e-6 * max(hi - lo, 1e-9), lo))
            px, py = canvas.px(mx), canvas.py(my)
            ang = math.atan2(py - canvas.py(by), px - canvas.px(bx))
            ux, uy = math.cos(ang), math.sin(ang)                      # along the branch
            span_px = math.hypot(canvas.px(place(node, hi)[0]) - canvas.px(place(node, lo)[0]),
                                 canvas.py(place(node, hi)[1]) - canvas.py(place(node, lo)[1]))
            L = float(m.get("size") or length or min(22.0, 0.8 * span_px) or 6.0)
            half = L / 2
            reach = half + fuse * L                                    # where the colour has faded

            # the coloured stretch under the lens, then a gradient on each side into the branch
            w = style.branch_width
            canvas._d.append(_line(px - ux * half, py - uy * half, px + ux * half, py + uy * half,
                                   col, w, opacity))
            for sgn in (-1, 1):
                x0, y0 = px + sgn * ux * half, py + sgn * uy * half
                x1, y1 = px + sgn * ux * reach, py + sgn * uy * reach
                canvas._d.append(_gradient(x0, y0, x1, y1, col, style.branch_color, w, opacity))

            # the lens, a polygon along the branch
            pts = []
            for i in range(41):
                t = -1 + 2 * i / 40
                d = height * (1 - t * t)
                pts.append((px + ux * t * half - uy * d, py + uy * t * half + ux * d))
            for i in range(40, -1, -1):
                t = -1 + 2 * i / 40
                d = height * (1 - t * t)
                pts.append((px + ux * t * half + uy * d, py + uy * t * half - ux * d))
            canvas.raw_polygon(pts, fill=col, opacity=opacity)

    return layer


def _line(x0, y0, x1, y1, color, width, opacity):
    import drawsvg as draw
    fade = {} if opacity >= 1.0 else {"stroke_opacity": opacity}
    return draw.Line(x0, y0, x1, y1, stroke=color, stroke_width=width, stroke_linecap="butt", **fade)


def _gradient(x0, y0, x1, y1, color_from, color_to, width, opacity):
    import drawsvg as draw
    grad = draw.LinearGradient(x0, y0, x1, y1, gradientUnits="userSpaceOnUse")
    grad.add_stop(0, color_from)
    grad.add_stop(1, color_to)
    fade = {} if opacity >= 1.0 else {"stroke_opacity": opacity}
    return draw.Line(x0, y0, x1, y1, stroke=grad, stroke_width=width, stroke_linecap="butt", **fade)
