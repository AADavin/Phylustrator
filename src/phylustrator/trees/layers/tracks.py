"""Track layers — data drawn beside the tips (coloured chips, and later heatmaps)."""

from __future__ import annotations

import math

from ...color import map_values


def tip_track(values, *, cmap: str = "viridis", palette: dict | None = None,
              size: float = 11.0, offset: float = 8.0):
    """A coloured square at each tip, coloured by ``values`` the same way ``color_branches`` colours
    branches (so the two share a scale). Also records the scale, so a ``colorbar``/``legend`` can
    follow even without ``color_branches``. Returns a layer."""

    def layer(canvas, tree, layout, style):
        colors, scale = map_values(values, cmap=cmap, palette=palette)
        if scale is not None:
            canvas.scale = scale
        cx0, cy0 = canvas.px(0.0), canvas.py(0.0)  # the origin/centre, for pushing chips outward
        for leaf in tree.leaves:
            color = colors.get(leaf.name)
            if color is None:
                continue
            cx, cy = canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf))
            if layout.kind == "rectangular":
                cx += offset
            else:  # push out along the radial direction
                dx, dy = cx - cx0, cy - cy0
                d = math.hypot(dx, dy) or 1.0
                cx += offset * dx / d
                cy += offset * dy / d
            canvas.raw_rect(cx - size / 2, cy - size / 2, size, size,
                            fill=color, stroke="white", stroke_width=0.5)

    return layer
