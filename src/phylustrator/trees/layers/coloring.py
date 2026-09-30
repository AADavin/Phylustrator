"""The colouring layer — paint the branches by a per-node value.

``color_branches`` dispatches on the data: **numbers** get a colormap and a gradient down each branch
(and record a continuous scale, so ``colorbar()`` can draw itself); **labels** get a categorical
palette and solid branches (recording a palette, so ``legend()`` can). Values are keyed by node name
(or by node), and nodes with no value keep the default branch colour. ``color_history`` dispatches
its segment states by the same rule, for a value that changes *along* a branch rather than once per
branch. Works on any layout, because it
draws through :func:`phylustrator.skeleton.draw_branches`.
"""

from __future__ import annotations

from ...color import map_values
from ..skeleton import draw_branches


def _dashed_or_figure(dashed, canvas) -> set:
    """The layer's own ``dashed``, or the figure's if it was not given one.

    A colouring layer overdraws the skeleton, so unless it knows which branches were dashed it paints
    them solid and a run's extinct lineages quietly become survivors. `plot(dashed=...)` puts the set
    on the canvas for exactly this."""
    if dashed is not None:
        return set(dashed)
    return set(getattr(canvas, "dashed", None) or ())


def color_branches(values, *, cmap: str = "viridis", palette: dict | None = None, width=None,
                   dashed=None, limits: tuple[float, float] | None = None,
                   gradient: bool | None = None, others: str = "repaint"):
    """Colour every branch by ``values`` (``{node name: value}``). Numeric → colormap gradient;
    categorical → palette. ``dashed`` is an optional set of node names to draw dashed (e.g. extinct
    lineages), since the colour overdraws the base skeleton. Returns a layer.

    ``limits`` fixes the numeric range rather than deriving it from ``values``, so several figures
    can share one colour scale — without it each normalises to its own min and max, and the same
    colour means a different number in each. A ``colorbar`` on the same figure follows the range.

    ``gradient`` overrides how a branch is painted. Left unset, numbers run from the parent's colour
    to the node's and labels are flat. Set it to ``False`` for a number that belongs to the branch as
    a whole — a count of events on it, a rate fitted for it, a support value — which a gradient
    misreads twice over: it shades the branch by its *parent's* value, and it suggests a change along
    a branch the data says nothing about. The colormap and the colorbar are unaffected.

    ``width`` is a number for every branch, or ``{node name: width}`` for a few — one lineage drawn
    thicker than the rest, say. A branch with no width of its own takes the style's. The drop into a
    child follows the child's width, so a thick lineage does not fatten the whole bar at a node.

    ``others`` says what happens to a branch with no value: ``"repaint"`` (the default) draws it in
    the style's branch colour, and ``"keep"`` leaves it exactly as the base plot drew it. Two layers,
    each mapping a few branches, need ``"keep"``: otherwise the second repaints the first's work."""
    if others not in ("repaint", "keep"):
        raise ValueError(f"others must be 'repaint' or 'keep', not {others!r}")
    widths = dict(width) if isinstance(width, dict) else None

    def layer(canvas, tree, layout, style):
        by_name, scale = map_values(values, cmap=cmap, palette=palette, limits=limits)
        if scale is None:
            return
        canvas.scale = scale
        default = style.branch_color

        def color(node):
            return by_name.get(node.name, default)

        def wide(node):
            if widths is None:
                return width or style.branch_width
            return float(widths.get(node.name, style.branch_width))

        fade = (scale["kind"] == "continuous") if gradient is None else gradient
        draw_branches(canvas, tree, layout, color=color, width=wide, gradient=fade,
                      dashed=_dashed_or_figure(dashed, canvas),
                      include=(lambda n: n.name in by_name) if others == "keep" else None)

    return layer


def _ends(state):
    """A segment's state as ``(from, to)``. A plain state begins and ends the same; a **pair**
    ``(a, b)`` fades from one to the other along the segment, for a trait that shifts gradually
    rather than switching at an instant."""
    if isinstance(state, (tuple, list)) and len(state) == 2:
        return state[0], state[1]
    return state, state


def _paint(canvas, x0, y0, x1, y1, state, colors, base, width, dash) -> None:
    """One segment of a branch's history: flat, or a fade when its state is a pair."""
    a, b = _ends(state)
    c0, c1 = colors.get(a, base), colors.get(b, base)
    if dash or c0 == c1:
        # a dashed line cannot carry a gradient, so a dashed fade is drawn in the state it ends in
        canvas.line(x0, y0, x1, y1, c1, width, dash=dash)
    else:
        canvas.gradient_line(x0, y0, x1, y1, c0, c1, width)


def color_history(history, *, palette: dict | None = None, cmap: str = "viridis", width=None,
                  default: str | None = None, dashed=None,
                  limits: tuple[float, float] | None = None):
    """Paint each branch as coloured **segments** from its per-lineage state history — a list of
    ``(state, duration)`` running from the branch's start to its end. Use this (not
    :func:`color_branches`) for a value that changes *along* a branch: the branch is a mosaic, not
    one colour. ``dashed`` is an optional set of node names to draw dashed (e.g. extinct lineages).
    Rectangular and radial layouts. ``history``: ``{node name: [(state, dur), …]}``.

    Dispatches on the states the same way :func:`color_branches` dispatches on its values:
    **labels** get a categorical palette (and record it, so ``legend`` can draw), **numbers** get a
    colormap (and record a continuous scale, so ``colorbar`` can). A quantity that steps along a
    branch — how much of a gene module a lineage still holds, say — is numeric and changes
    mid-branch, so it needs both halves at once.

    A segment's state may be a **pair** ``(from, to)``, drawn as a fade from one colour to the other
    along that segment: a trait that shifts gradually after an event, rather than switching at an
    instant. Both members take their colour from the same palette or colormap, and the branch ends
    in the second, so the connector below it follows. A dashed branch is drawn in the state it ends
    in, since a dashed line cannot carry a gradient.

    ``limits`` fixes the numeric range instead of taking it from the states, so panels drawn
    separately share one scale. Ignored for categorical data."""
    states = {end for segments in history.values() for state, _ in segments for end in _ends(state)}
    colors, scale = map_values({s: s for s in states}, cmap=cmap, palette=palette, limits=limits)

    def layer(canvas, tree, layout, style):
        if layout.kind not in ("rectangular", "radial"):
            raise ValueError("color_history supports the rectangular and radial layouts")
        marks = _dashed_or_figure(dashed, canvas)
        w = width or style.branch_width
        if scale is not None:
            canvas.scale = scale
        base = default or style.branch_color
        if layout.kind == "radial":
            _history_radial(canvas, tree, layout, history, colors, base, w, marks)
            return
        for node in tree.walk():
            y = layout.y(node)
            x_end = layout.x(node)
            x_start = (x_end - layout.root_branch) if node.is_root else layout.x(node.parent)
            d = node.name in marks
            segs = history.get(node.name)
            end_state = None
            if segs:
                total = sum(dur for _, dur in segs) or 1.0
                span = x_end - x_start
                xx = x_start
                for state, dur in segs:
                    x1 = xx + span * dur / total
                    if x1 != xx:      # two changes at the same instant leave a zero-length segment
                        _paint(canvas, xx, y, x1, y, state, colors, base, w, d)
                    xx = x1
                end_state = _ends(segs[-1][0])[1]
            else:
                canvas.line(x_start, y, x_end, y, base, w, dash=d)
            if not node.is_leaf:                              # connectors in the node's end state
                cc = colors.get(end_state, base)
                for c in node.children:
                    canvas.line(x_end, y, x_end, layout.y(c), cc, w, dash=(c.name in marks))

    return layer


def _history_radial(canvas, tree, layout, history, colors, base, w, marks) -> None:
    """The radial half of :func:`color_history`: each branch is a mosaic running OUT along the
    node's angle, from the parent's radius to the node's, and the speciation connector is an arc
    at the node's radius in the branch's end state — mirrors ``skeleton._radial``."""
    import math

    from ..skeleton import _arc

    ang = layout.angle

    def radius(node):
        return math.hypot(layout.x(node), layout.y(node))

    for node in tree.walk():
        a = ang[node]
        r_end = radius(node)
        r_start = max(0.0, r_end - layout.root_branch) if node.is_root else radius(node.parent)
        d = node.name in marks
        ca, sa = math.cos(a), math.sin(a)
        segs = history.get(node.name)
        end_state = None
        if segs:
            total = sum(dur for _, dur in segs) or 1.0
            span = r_end - r_start
            rr = r_start
            for state, dur in segs:
                r1 = rr + span * dur / total
                if r1 != rr:      # two changes at the same instant leave a zero-length segment
                    _paint(canvas, rr * ca, rr * sa, r1 * ca, r1 * sa, state, colors, base, w, d)
                rr = r1
            end_state = _ends(segs[-1][0])[1]
        else:
            canvas.line(r_start * ca, r_start * sa, r_end * ca, r_end * sa, base, w, dash=d)
        if not node.is_leaf and r_end > 1e-9:     # angular connectors in the node's end state
            cc = colors.get(end_state, base)
            for c in node.children:
                _arc(canvas, r_end, min(a, ang[c]), max(a, ang[c]), cc, w,
                     dash=(c.name in marks))


def color_lanes(lanes, *, width=None, gap: float = 1.0, connectors: bool = True,
                joint: str | None = None, default: str | None = None, dashed=None):
    """Paint each branch as several **parallel lanes** — one per trait — so more than one discrete
    trait shows side by side *on the same branch*, each branch a stacked two-tone (or n-tone) band.
    Each lane is a segmented colour history exactly like :func:`color_history` (``{node name:
    [(state, dur), …]}`` + its own palette), offset across the branch; lane 0 sits on one side, lane 1
    the other. ``gap`` is the lane spacing in units of the lane width (``1`` = touching, a solid band).

    Topology: by default the lanes carry their own speciation joints, but the cleanest result is to draw
    the plain grey skeleton for structure (``plot(tree)`` with ``skeleton=True``) and pass
    ``connectors=False`` here, so the lanes only paint the horizontal branches and the skeleton shows
    the tree. Rectangular layout only. ``lanes``: a list of ``(history, palette)`` pairs."""

    def layer(canvas, tree, layout, style):
        if layout.kind != "rectangular":
            raise ValueError("color_lanes needs the rectangular layout (segments run along x)")
        marks = _dashed_or_figure(dashed, canvas)
        w = width or style.branch_width
        n = len(lanes)
        # lane widths/offsets are in pixels; x, y are data-space — convert via the canvas scales so
        # the lanes sit a few pixels apart (a solid band), not whole tree rows apart. The horizontals
        # offset in y, the speciation connectors in x, so each stays a matching stacked band.
        ppu_y = (canvas.py(1.0) - canvas.py(0.0)) or 1.0
        ppu_x = (canvas.px(1.0) - canvas.px(0.0)) or 1.0
        px = [(i - (n - 1) / 2.0) * w * gap for i in range(n)]
        offs_y = [p / ppu_y for p in px]
        offs_x = [p / ppu_x for p in px]
        base = default or style.branch_color
        for node in tree.walk():
            y = layout.y(node)
            x_end = layout.x(node)
            x_start = (x_end - layout.root_branch) if node.is_root else layout.x(node.parent)
            d = node.name in marks
            end_states = []
            for (history, palette), ox, oy in zip(lanes, offs_x, offs_y):
                yy = y + oy
                # a lane's own joint sits at x_end + ox and its parent's at x_start + ox; extend the
                # end segments by |ox| so the horizontal reaches those joints (same colour → the small
                # overlap is invisible), giving clean corners. Never overshoot the root or the tips.
                el = abs(ox) if (connectors and not node.is_root) else 0.0
                er = abs(ox) if (connectors and not node.is_leaf) else 0.0
                segs = history.get(node.name)
                if segs:
                    total = sum(dur for _, dur in segs) or 1.0
                    span = x_end - x_start
                    xx = x_start
                    last = len(segs) - 1
                    for k, (state, dur) in enumerate(segs):
                        x1 = xx + span * dur / total
                        canvas.line(xx - (el if k == 0 else 0.0), yy,
                                    x1 + (er if k == last else 0.0), yy,
                                    palette.get(state, base), w, dash=d)
                        xx = x1
                    end_states.append(segs[-1][0])
                else:
                    canvas.line(x_start - el, yy, x_end + er, yy, base, w, dash=d)
                    end_states.append(None)
            if connectors and not node.is_leaf:      # one joint per lane, coloured by its end state,
                for (history, palette), ox, oy, es in zip(lanes, offs_x, offs_y, end_states):
                    cc = (joint or palette.get(es, base)) if es is not None else (joint or base)
                    for c in node.children:          # so the speciation verticals match the branches
                        canvas.line(x_end + ox, y + oy, x_end + ox, layout.y(c) + oy, cc, w,
                                    dash=(c.name in marks))

    return layer
