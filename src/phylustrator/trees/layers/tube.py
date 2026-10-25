"""The tube layers — a species tree drawn as a wide branch, with a gene's history inside it.

This is the usual picture of a reconciliation: the species tree is a tube with rounded bends, and
the gene runs inside it as a thin line — along a branch, starting part-way down one, crossing to
another at a transfer, stopping at a loss.

Two layers, because they are two things. :func:`tube` draws the species tree. :func:`gene_path`
draws a lineage over whatever part of whatever branches it occupies, and knows nothing about the
tube beyond sharing the tree's coordinates, so the same layer draws a gene inside a tube, a
sub-lineage highlighted on an ordinary tree, or the part of a branch a trait is known for.
"""

from __future__ import annotations

import math


def _branch_corner(canvas, layout, node):
    """The three pixel points a branch is drawn through: where it leaves the parent, the corner it
    turns, and where it ends at the node.

    A rectangular branch is a connector down from the parent and then a run across; the corner is
    where those meet. A diagonal branch is one straight segment, so the corner is its start and
    nothing is turned."""
    ex, ey = canvas.px(layout.x(node)), canvas.py(layout.y(node))
    if node.parent is None:
        back = layout.root_branch
        if layout.kind == "diagonal" and not layout.grows_along_x:
            sx, sy = ex, canvas.py(layout.y(node) - back)
        else:
            sx, sy = canvas.px(layout.x(node) - back), ey
        return (sx, sy), (sx, sy), (ex, ey)
    px_, py_ = canvas.px(layout.x(node.parent)), canvas.py(layout.y(node.parent))
    if layout.kind == "rectangular":
        return (px_, py_), (px_, ey), (ex, ey)      # down the connector, then across
    return (px_, py_), (px_, py_), (ex, ey)         # diagonal: one straight segment


def _path_through(start, corner, end, radius: float) -> str:
    """An SVG path from ``start`` to ``end`` by way of ``corner``, with the turn rounded.

    A square corner on a wide tube reads as a mitre joint rather than as a lineage carrying on
    through a split, which is what the picture is about."""
    (sx, sy), (cx, cy), (ex, ey) = start, corner, end
    into = max(abs(cx - sx), abs(cy - sy))
    out_of = max(abs(ex - cx), abs(ey - cy))
    r = min(radius, into / 2, out_of / 2)
    if r <= 0.5:                                    # nothing worth rounding
        if (sx, sy) == (cx, cy):
            return f"M {sx:g},{sy:g} L {ex:g},{ey:g}"
        return f"M {sx:g},{sy:g} L {cx:g},{cy:g} L {ex:g},{ey:g}"
    # stop short of the corner, curve through it, carry on
    ax = cx + (sx - cx) / into * r if into else cx
    ay = cy + (sy - cy) / into * r if into else cy
    bx = cx + (ex - cx) / out_of * r if out_of else cx
    by = cy + (ey - cy) / out_of * r if out_of else cy
    return (f"M {sx:g},{sy:g} L {ax:g},{ay:g} Q {cx:g},{cy:g} {bx:g},{by:g} "
            f"L {ex:g},{ey:g}")


def _pulled_back(corner, end, by: float):
    """``end``, moved back towards ``corner`` by ``by`` pixels.

    A round cap reaches half the tube's width past the end of its path, so a tube drawn to the tip
    overhangs it and runs under the tip's own label. Pulling the path back by that much puts the
    outside of the cap exactly on the tip."""
    dx, dy = end[0] - corner[0], end[1] - corner[1]
    d = math.hypot(dx, dy)
    if d <= by:
        return end
    return (end[0] - dx / d * by, end[1] - dy / d * by)


def _supported(layout, who: str) -> None:
    if layout.kind not in ("rectangular", "diagonal"):
        raise ValueError(f"{who} needs a layout whose branches are drawn as segments across the "
                         f"page — rectangular or diagonal; got {layout.kind!r}. A radial tube would "
                         f"have to be an annulus, which is a different drawing.")


def tube(*, width: float = 16.0, fill: str = "#f2f2f2", stroke: str = "#1a1a1a",
         edge: float = 1.6, radius: float = 8.0, opacity: float = 1.0):
    """Draw the tree as a **tube**: a wide branch with an outline and rounded bends.

    The species tree of a reconciliation picture, with room inside it for :func:`gene_path` to run
    the gene through. ``width`` is the tube's outside width in pixels, ``edge`` the thickness of its
    outline, ``radius`` how much the bend at a split is rounded.

    Each branch is drawn twice, once wide in ``stroke`` and once narrower in ``fill``, so the
    outlines of two branches leaving the same node merge into one tube instead of crossing it.
    That is also why this layer goes on first, before anything that belongs inside it.

    Rectangular and diagonal layouts, where a branch is a segment across the page. Returns a layer."""

    def layer(canvas, tree, layout, style):
        _supported(layout, "tube")
        paths = []
        for node in tree.walk():
            if node.parent is None and layout.root_branch <= 0:
                continue
            start, corner, end = _branch_corner(canvas, layout, node)
            # A free end — a tip, or the open end of the root stem — is pulled back so the cap sits
            # on it rather than past it. A branch that carries on into another is left alone: there
            # the cap is what fills the wedge between two branches leaving at an angle, and without
            # it a diagonal tree shows a notch at every fork.
            if node.is_leaf:
                end = _pulled_back(corner, end, width / 2)
            if node.parent is None:
                start = _pulled_back(corner, start, width / 2)
            paths.append(_path_through(start, corner, end, radius))
        inner = max(width - 2 * edge, 0.5)
        for d in paths:                             # every outline first, so none cuts a neighbour
            canvas.raw_path(d, stroke=stroke, stroke_width=width, cap="round", opacity=opacity)
        for d in paths:
            canvas.raw_path(d, stroke=fill, stroke_width=inner, cap="round", opacity=opacity)

    return layer


def gene_path(segments, *, color: str = "#c1443c", width: float = 1.8, dash: bool = False,
              offset: float = 0.0, opacity: float = 1.0):
    """Draw a lineage along part of the tree — the gene inside the tube.

    ``segments`` is a list of the branches it occupies. Each is a branch name, or a dict naming the
    branch and how much of it to draw::

        gene_path([{"branch": "abc", "from": 0.30}, "ab", "A", "B", "C",
                   {"branch": "D", "from": 0.90}])

    ``from`` and ``to`` are **depths** on the tree's own scale, the same numbers ``branch_events``
    takes; left out, the segment runs the whole branch. A segment that starts at the top of its
    branch is drawn through the bend out of its parent, so the line follows the tube round the
    corner rather than cutting across it; one that starts part-way down begins there, which is what
    a copy born inside a branch looks like.

    ``offset`` shifts the line sideways in pixels, so two copies in one tube run side by side
    instead of on top of each other. ``dash`` draws it broken, for a lineage that is inferred
    rather than observed. Returns a layer."""
    wanted = [s if isinstance(s, dict) else {"branch": s} for s in segments]

    def layer(canvas, tree, layout, style):
        _supported(layout, "gene_path")
        by_name = {n.name: n for n in tree.walk() if n.name}
        missing = sorted({s["branch"] for s in wanted} - set(by_name))
        if missing:
            shown = ", ".join(missing[:5]) + (", …" if len(missing) > 5 else "")
            raise ValueError(f"gene_path: {len(missing)} name(s) not in the tree: {shown}")
        for piece in wanted:
            node = by_name[piece["branch"]]
            start, corner, end = _branch_corner(canvas, layout, node)
            lo = layout.depth(node) if node.parent is None else layout.depth(node.parent)
            hi = layout.depth(node)
            span = (hi - lo) or 1.0
            begins = piece.get("from")
            stops = piece.get("to")
            if begins is not None:                  # part-way down: start on the branch itself
                f = min(max((float(begins) - lo) / span, 0.0), 1.0)
                start = corner = (corner[0] + f * (end[0] - corner[0]),
                                  corner[1] + f * (end[1] - corner[1]))
            if stops is not None:
                f = min(max((float(stops) - lo) / span, 0.0), 1.0)
                end = (corner[0] + f * (end[0] - corner[0]),
                       corner[1] + f * (end[1] - corner[1]))
            if offset:
                across = (0.0, offset) if layout.grows_along_x else (offset, 0.0)
                start = (start[0] + across[0], start[1] + across[1])
                corner = (corner[0] + across[0], corner[1] + across[1])
                end = (end[0] + across[0], end[1] + across[1])
            canvas.raw_path(_path_through(start, corner, end, max(4.0, width * 2)),
                            stroke=color, stroke_width=width, cap="round",
                            dash="4,3" if dash else None, opacity=opacity)

    return layer
