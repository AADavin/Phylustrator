"""Track layers — data drawn beside the tips (coloured chips, and later heatmaps)."""

from __future__ import annotations

import math

from ...color import map_values


def tip_track(values, *, cmap: str = "viridis", palette: dict | None = None,
              size: float = 11.0, offset: float = 8.0, shape: str = "square"):
    """A coloured chip at each tip, coloured by ``values`` the same way ``color_branches`` colours
    branches (so the two share a scale). Also records the scale, so a ``colorbar``/``legend`` can
    follow even without ``color_branches``. ``shape`` is any glyph
    :meth:`~phylustrator.render.Canvas.raw_marker` draws (``"square"``, ``"circle"``, …).
    Returns a layer."""

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
            canvas.raw_marker(cx, cy, shape, color, size / 2, stroke="white", stroke_width=0.5)

    return layer


def ring(values, *, cmap: str = "viridis", palette: dict | None = None,
         gap: float | None = None, width: float | None = None, radius_pct: float = 100.0,
         opacity: float = 1.0):
    """An outer ring of coloured arcs — one contiguous segment per tip at a fixed radius — the
    classic circular-tree "population ring". Best with a ``radial`` (or ``unrooted``) layout: each
    tip's arc spans the angle halfway to its neighbours, so same-coloured neighbours merge into a
    band. ``radius_pct`` sets the ring's radius as that percentile of the tip distances (100 = at the
    outermost tip; lower brings it in, so a few long branches can extend past it instead of blowing
    the ring outward). Colours ``values`` like :func:`color_branches` and records the scale for a
    ``legend``. Returns a layer."""

    def layer(canvas, tree, layout, style):
        colors, scale = map_values(values, cmap=cmap, palette=palette)
        if scale is not None:
            canvas.scale = scale
        cx0, cy0 = canvas.px(0.0), canvas.py(0.0)
        leaves = list(tree.leaves)
        ang, radii = {}, []
        for lf in leaves:
            cx, cy = canvas.px(layout.x(lf)), canvas.py(layout.y(lf))
            # angle from the layout (canonical); radius from the pixel transform
            ang[lf.name] = layout.angle[lf]
            radii.append(math.hypot(cx - cx0, cy - cy0))
        radii.sort()
        k = min(len(radii) - 1, max(0, int(round((radius_pct / 100.0) * (len(radii) - 1)))))
        r_ring = radii[k]
        # default gap/width scale with the ring radius so it stays slim at any size
        g = r_ring * 0.02 if gap is None else gap
        w = r_ring * 0.035 if width is None else width
        r_in = r_ring + g
        r_out = r_in + w
        ordered = sorted(leaves, key=lambda lf: ang[lf.name])
        a = [ang[lf.name] for lf in ordered]
        n = len(a)
        if n < 2:
            return
        # segment boundaries: midpoints between neighbours, ends mirrored
        b = [a[0] - (a[1] - a[0]) / 2]
        b += [(a[i - 1] + a[i]) / 2 for i in range(1, n)]
        b.append(a[-1] + (a[-1] - a[-2]) / 2)
        for i, lf in enumerate(ordered):
            color = colors.get(lf.name)
            if color is not None:
                canvas.raw_annulus_sector(cx0, cy0, r_in, r_out, b[i], b[i + 1],
                                          fill=color, stroke=color, stroke_width=0.4,
                                          opacity=opacity)

    return layer


def rubberband(values, *, cmap: str = "viridis", palette: dict | None = None,
               gap: float | None = None, width: float | None = None,
               smooth: float = 0.18, opacity: float = 1.0):
    """A smooth, round population band wrapped around the tree, instead of sitting on a fixed-radius
    circle like :func:`ring`. The tree's outline is traced from the root, held out a **constant**
    distance from the branches (so the margin is even all the way around, not tight on one side and
    loose on the other), and then rounded off by smoothing that outline over angle. A clamp keeps it
    from ever crossing a branch. Best with a ``radial`` layout, where the tips fan out from the root.

    ``gap`` is that constant distance from the branches to the band. ``smooth`` is the roundness —
    the fraction of the full turn the outline is averaged over (0 hugs the branches; larger rounds
    into big lobes and, high enough, a near-circle). ``width`` is the band thickness. ``gap`` and
    ``width`` are in pixels and default to a fraction of the tree's reach. Colours ``values`` like
    :func:`color_branches` and records the scale for a ``legend``. Returns a layer."""

    def layer(canvas, tree, layout, style):
        colors, scale = map_values(values, cmap=cmap, palette=palette)
        if scale is not None:
            canvas.scale = scale
        cx0, cy0 = canvas.px(0.0), canvas.py(0.0)
        leaves = list(tree.leaves)
        if len(leaves) < 3:
            return
        rad = []
        tips_c = []   # coloured tips, for tinting the outline by nearest population
        for lf in leaves:
            cx, cy = canvas.px(layout.x(lf)), canvas.py(layout.y(lf))
            rad.append(math.hypot(cx - cx0, cy - cy0))
            c = colors.get(lf.name)
            if c is not None:
                tips_c.append((cx - cx0, cy - cy0, c))
        rad.sort()
        # p90 is a robust measure of the tree's reach (unlike the median, it is stable when the tips
        # split into a near cluster and a far one); the defaults scale with it
        p90 = rad[min(len(rad) - 1, int(0.9 * (len(rad) - 1)))] or 1.0
        margin = p90 * 0.10 if gap is None else gap        # constant distance from the branches
        w = p90 * 0.012 if width is None else width
        near = max(margin * 0.4, w)                         # closest the band may come to a branch
        # cover the whole tree with disks — at every node and stepped along every branch — so the
        # outline is one connected shape. Points are kept relative to the root centre.
        step = max(margin * 0.4, 1.0)
        disks = []
        for node in tree.walk():
            nx, ny = canvas.px(layout.x(node)), canvas.py(layout.y(node))
            disks.append((nx - cx0, ny - cy0))
            for ch in node.children:
                mx, my = canvas.px(layout.x(ch)), canvas.py(layout.y(ch))
                seg = math.hypot(mx - nx, my - ny)
                for s in range(1, int(seg / step) + 1):
                    f = s * step / seg
                    disks.append((nx - cx0 + f * (mx - nx), ny - cy0 + f * (my - ny)))
        # at each angle, a ray from the root leaves the tree's disk-cover at its far edge — the
        # far root of |ray - centre| = r, for the wide margin and again for the tight no-cut radius
        M = max(720, 6 * len(leaves))
        mg2, nr2 = margin * margin, near * near
        r_out = [None] * M     # branches + margin (the even offset we want)
        r_min = [None] * M     # branches + near   (the clamp: band may not go inside this)
        for m in range(M):
            th = 2 * math.pi * m / M
            ux, uy = math.cos(th), math.sin(th)
            to = tn = None
            for ax, ay in disks:
                b = ux * ax + uy * ay
                base = ax * ax + ay * ay
                do = b * b - base + mg2
                if do >= 0:
                    t = b + math.sqrt(do)
                    if t > 0 and (to is None or t > to):
                        to = t
                dn = b * b - base + nr2
                if dn >= 0:
                    t = b + math.sqrt(dn)
                    if t > 0 and (tn is None or t > tn):
                        tn = t
            r_out[m], r_min[m] = to, tn

        def fill(arr):   # bridge the few angles no disk covers (the fan's mouth)
            good = [v for v in arr if v is not None]
            if not good:
                return [1.0] * M
            for i in range(M):
                if arr[i] is None:
                    j = k = i
                    while arr[j] is None:
                        j = (j - 1) % M
                    while arr[k] is None:
                        k = (k + 1) % M
                    arr[i] = (arr[j] + arr[k]) / 2
            return arr
        r_out, r_min = fill(r_out), fill(r_min)
        # round the outline: average the radius over a window that is a fraction of the whole turn,
        # then never let it dip inside the tight radius (so a branch is never crossed)
        k = int(round(smooth * M))
        if k > 0:
            win = 2 * k + 1
            r_sm = []
            for m in range(M):
                total = 0.0
                for d in range(-k, k + 1):
                    total += r_out[(m + d) % M]
                r_sm.append(total / win)
            r_out = r_sm
        rf = [max(r_out[m], r_min[m]) for m in range(M)]
        # outline points + colour (nearest coloured tip)
        pts, cols = [], []
        for m in range(M):
            th = 2 * math.pi * m / M
            bx, by = rf[m] * math.cos(th), rf[m] * math.sin(th)
            col, best = None, None
            for ax, ay, c in tips_c:
                d = (ax - bx) ** 2 + (ay - by) ** 2
                if best is None or d < best:
                    best, col = d, c
            pts.append((cx0 + bx, cy0 + by))
            cols.append(col)
        n = M
        # offset the outline by a constant width along its own normal, for a uniform visual thickness
        pin, pout = [], []
        for i in range(n):
            ex, ey = pts[i]
            tx = pts[(i + 1) % n][0] - pts[(i - 1) % n][0]
            ty = pts[(i + 1) % n][1] - pts[(i - 1) % n][1]
            tl = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / tl, tx / tl
            if nx * (ex - cx0) + ny * (ey - cy0) < 0:   # keep the normal pointing outward
                nx, ny = -nx, -ny
            pin.append((ex - 0.5 * w * nx, ey - 0.5 * w * ny))
            pout.append((ex + 0.5 * w * nx, ey + 0.5 * w * ny))

        def mid(p, q):
            return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)

        # each outline vertex owns a tile spanning to the midpoint with each neighbour, so
        # same-coloured tiles meet edge-to-edge and merge into one continuous band
        for i in range(n):
            color = cols[i]
            if color is None:
                continue
            il, ir = mid(pin[(i - 1) % n], pin[i]), mid(pin[i], pin[(i + 1) % n])
            ol, orr = mid(pout[(i - 1) % n], pout[i]), mid(pout[i], pout[(i + 1) % n])
            canvas.raw_polygon([il, pin[i], ir, orr, pout[i], ol],
                               fill=color, stroke=color, stroke_width=0.4, opacity=opacity)

    return layer
