"""The branch-markers layer — a mark on a branch, coloured by a number.

``branch_events`` marks a branch with a *kind* and takes its colour from that kind. This one takes a
**value** per branch and colours it through a colormap, so a rate, a support, a posterior or a count
can be read off a scale rather than off a key. It records that scale, so ``colorbar()`` follows.
"""

from __future__ import annotations

import math

from ...color import map_values


def _along(layout, node, at: float):
    """Where a fraction ``at`` of the way along ``node``'s branch falls, in layout coordinates.

    The fraction runs from the parent (0) to the node (1), along the branch **as it is drawn**: the
    horizontal run of a rectangular branch, the radial step of a circular one, the slanted segment
    of a diagonal or unrooted one."""
    x, y = layout.x(node), layout.y(node)
    if node.parent is None:
        return x, y
    if layout.kind == "rectangular":
        # the drawn branch is the horizontal run at this node's row; the drop belongs to the parent
        return layout.x(node.parent) + at * (x - layout.x(node.parent)), y
    if layout.kind == "radial":
        a = layout.angle[node]
        r_parent = math.hypot(layout.x(node.parent), layout.y(node.parent))
        r = r_parent + at * (math.hypot(x, y) - r_parent)
        return r * math.cos(a), r * math.sin(a)
    return (layout.x(node.parent) + at * (x - layout.x(node.parent)),
            layout.y(node.parent) + at * (y - layout.y(node.parent)))


def _spread(points, gap: float, rounds: int = 60):
    """Push markers that land on top of each other apart, keeping them near where they belong.

    Near the centre of a radial tree the branches are a few pixels apart, so two marks on
    neighbouring branches cover each other and the figure shows one value where it has two. Each
    round moves an overlapping pair a little along the line between them; a pair at the same point
    is parted in an arbitrary but fixed direction, so the same figure comes out the same way twice."""
    moved = [list(p) for p in points]
    for _ in range(rounds):
        busy = False
        for i in range(len(moved)):
            for j in range(i + 1, len(moved)):
                dx, dy = moved[j][0] - moved[i][0], moved[j][1] - moved[i][1]
                d = math.hypot(dx, dy)
                if d >= gap:
                    continue
                busy = True
                if d < 1e-9:
                    dx, dy, d = 1.0, 0.0, 1.0           # exactly coincident: part them sideways
                step = (gap - d) / 2 + 0.01
                ux, uy = dx / d, dy / d
                moved[i][0] -= ux * step
                moved[i][1] -= uy * step
                moved[j][0] += ux * step
                moved[j][1] += uy * step
        if not busy:
            break
    return [tuple(p) for p in moved]


def _label_side(canvas, layout, node, px_, py_, cx0, cy0):
    """A unit vector across the branch, pointing away from the middle of the tree.

    Along the branch the text would run into the tip's own name, since a branch that carries a mark
    very often ends at one."""
    if node.parent is None:
        return 0.0, -1.0
    ax, ay = canvas.px(layout.x(node.parent)), canvas.py(layout.y(node.parent))
    bx, by = canvas.px(layout.x(node)), canvas.py(layout.y(node))
    if layout.kind == "rectangular":
        ay = by                                    # the drawn branch is the horizontal run
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, -1.0
    nx, ny = -dy / d, dx / d                       # across it
    # of the two sides, the one further from the middle of the tree; on a rectangular tree there is
    # no middle to speak of, and above the branch is where a support value goes
    if layout.kind in ("radial", "unrooted"):
        if nx * (px_ - cx0) + ny * (py_ - cy0) < 0:
            nx, ny = -nx, -ny
    elif ny > 0:
        nx, ny = -nx, -ny
    return nx, ny


def branch_markers(values, *, at: float = 0.8, cmap: str = "viridis", palette: dict | None = None,
                   limits: tuple[float, float] | None = None, size: float = 5.0,
                   shape: str = "circle", stroke: str = "#1a1a1a", stroke_width: float = 0.8,
                   labels: dict | None = None, label_size: float | None = None,
                   label_offset: float = 7.0, spread: bool = True, gap: float | None = None):
    """Mark branches with a glyph coloured by ``values`` (``{branch name: number}``).

    ``branch_events`` colours a mark by its *kind*; this colours it by its **value**, through the
    same colormap ``color_branches`` uses, and records the scale so a ``colorbar()`` added after it
    reads the right range. Categorical values work too and record a scale a ``legend()`` can read.

    ``at`` is how far along the branch the mark sits, from the parent (0) to the node (1) — 0.8 by
    default, near the end, where it reads as belonging to that branch rather than to the split above
    it. It follows the branch as drawn, so it lands on the horizontal run of a rectangular branch
    and on the radial step of a circular one.

    ``spread`` parts marks that land on top of each other: near the centre of a radial tree the
    branches are a few pixels apart, so two marks cover each other and the figure shows one value
    where it has two. ``gap`` is how close they may come, in pixels (default: a little over a
    marker's width); ``spread=False`` leaves every mark exactly where its branch is.

    ``labels`` (``{branch name: text}``) writes beside the marks, **across** the branch rather than
    along it — above it on a rectangular tree, outward on a circular one. Along the branch the text
    runs straight into the tip's own name on any branch that ends at a tip, which is where a figure
    labelling every branch puts half of them. Returns a layer."""
    if not 0.0 <= at <= 1.0:
        raise ValueError(f"at= is a fraction of the branch, from the parent (0) to the node (1); "
                         f"got {at}")

    def layer(canvas, tree, layout, style):
        colors, scale = map_values(values, cmap=cmap, palette=palette, limits=limits)
        if scale is not None:
            canvas.scale = scale
        by_name = {n.name: n for n in tree.walk() if n.name}
        missing = sorted(set(values) - set(by_name))
        if missing:
            shown = ", ".join(missing[:5]) + (", …" if len(missing) > 5 else "")
            raise ValueError(f"branch_markers: {len(missing)} name(s) not in the tree: {shown}")

        marked = [(name, by_name[name]) for name in values if colors.get(name) is not None]
        spots = [_along(layout, node, at) for _, node in marked]
        pixels = [(canvas.px(x), canvas.py(y)) for x, y in spots]
        if spread and len(pixels) > 1:
            pixels = _spread(pixels, gap if gap is not None else size * 2.2)

        cx0, cy0 = canvas.px(0.0), canvas.py(0.0)
        fs = label_size if label_size is not None else style.font_size * 0.9
        for (name, node), (px_, py_) in zip(marked, pixels):
            canvas.raw_marker(px_, py_, shape, colors[name], size,
                              stroke=stroke, stroke_width=stroke_width)
            text = (labels or {}).get(name)
            if not text:
                continue
            ox, oy = _label_side(canvas, layout, node, px_, py_, cx0, cy0)
            anchor = "middle" if abs(oy) > abs(ox) else ("start" if ox > 0 else "end")
            reach = size + label_offset + (fs * 0.4 if abs(oy) > abs(ox) else 0.0)
            canvas.raw_text(px_ + ox * reach, py_ + oy * reach, str(text), anchor=anchor, size=fs,
                            style=style.label_style, family=style.label_family)

    return layer
