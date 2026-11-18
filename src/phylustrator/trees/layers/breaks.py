"""The break mark — what a branch drawn shortened says about itself.

``plot(..., cut=…)`` caps every branch at a length, so one absurd branch does not take the whole
page. A figure laid out that way is no longer to scale, and a tree that does not say so misstates
its own data, so the mark is drawn by the figure itself rather than added as a layer: two short
strokes across the branch, and the branch's true length beside them.
"""

from __future__ import annotations

import math

#: How far along a cut branch the mark sits. Near the end, where the branch is about to stop short.
_AT = 0.75

#: Half the angle the two strokes lean from the perpendicular, in degrees. Upright they would read
#: as a tick or a node mark; leaning, as the break they are.
_LEAN = 30.0


def _across(canvas, layout, node, at: float) -> tuple[float, float]:
    """A unit vector across the branch at ``at``, in pixel space.

    Measured in pixels, not in layout units: the two axes are scaled apart on every flat layout, so
    a direction perpendicular in the tree's own coordinates comes out slanted on the page."""
    from ..layout import along_branch
    ax, ay = along_branch(layout, node, max(at - 0.02, 0.0))
    bx, by = along_branch(layout, node, min(at + 0.02, 1.0))
    dx = canvas.px(bx) - canvas.px(ax)
    dy = canvas.py(by) - canvas.py(ay)
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 1.0
    return -dy / d, dx / d


def draw_break_marks(canvas, tree, layout, style, *, color: str | None = None,
                     size: float = 7.0, width: float = 1.4, label: bool = True) -> None:
    """Mark every branch the layout cut, and write its true length beside it."""
    if not layout.cut_at:
        return
    from ..layout import along_branch
    paint = color or style.branch_color
    fs = style.font_size * 0.8
    for node in sorted(layout.cut_at, key=lambda n: (n.name or "")):
        x, y = along_branch(layout, node, _AT)
        cx, cy = canvas.px(x), canvas.py(y)
        nx, ny = _across(canvas, layout, node, _AT)
        ax, ay = -ny, nx                                   # along the branch
        lean = math.radians(_LEAN)
        # the stroke leans from the perpendicular, so the pair reads as a break and not as a tick
        sx = nx * math.cos(lean) + ax * math.sin(lean)
        sy = ny * math.cos(lean) + ay * math.sin(lean)
        for step in (-1.6, 1.6):                           # two strokes, a little apart
            mx, my = cx + ax * step, cy + ay * step
            canvas.raw_path(f"M {mx - sx * size / 2:g},{my - sy * size / 2:g} "
                            f"L {mx + sx * size / 2:g},{my + sy * size / 2:g}",
                            stroke=paint, stroke_width=width, cap="butt")
        if label:
            # beside the mark, on the side the strokes lean away from, so the text clears them
            reach = size / 2 + fs * 0.7
            canvas.raw_text(cx + nx * reach, cy + ny * reach, f"{float(node.length or 0.0):g}",
                            anchor="middle", size=fs, color=paint,
                            family=style.label_family)
