"""Text layers — names, or any per-node value, beside tips and internal nodes.

Both layers write a node's name by default. ``values`` (a dict keyed by node name, spelled like
``color_branches``) or ``text`` (a callable) writes something else instead: an ancestral estimate, a
support value, a node age. The library could colour by a dict and not label by one, which is an odd
pair of capabilities.
"""

from __future__ import annotations

import math

from ...render import text_width


def _as_text(value) -> str | None:
    """A value as label text. Numbers are written plainly — 81, not 81.0."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return f"{value:g}"


#: What marks a stretch of a label as italic. One character, doubled around the words, as it is in
#: every plain-text convention a reader already knows. ``\*`` writes one.
_MARK = "*"


def split_markup(written: str) -> list[tuple[str, str]]:
    """``"gene 1 (*Escherichia coli*)"`` as ``[("gene 1 (", "normal"), ("Escherichia coli",
    "italic"), (")", "normal")]``.

    A lone ``*`` with no partner closes nothing and is written as itself, so a label that happens
    to carry one — a footnote mark, a significance star — comes out as it was handed over rather
    than turning the rest of the name italic."""
    pieces: list[tuple[str, str]] = []
    buf: list[str] = []
    style = "normal"
    i = 0
    while i < len(written):
        c = written[i]
        if c == "\\" and i + 1 < len(written) and written[i + 1] == _MARK:
            buf.append(_MARK)                             # an asterisk the label wanted
            i += 2
            continue
        if c == _MARK:
            closing = style == "italic"
            # an opening mark needs a partner, or it is just a character
            if closing or _MARK in written[i + 1:]:
                pieces.append(("".join(buf), style))
                buf = []
                style = "normal" if closing else "italic"
                i += 1
                continue
        buf.append(c)
        i += 1
    if style == "italic":                                 # never closed: it was not markup at all
        return [(written.replace("\\" + _MARK, _MARK), "normal")]
    pieces.append(("".join(buf), style))
    return [(s, st) for s, st in pieces if s]


def _face(style) -> str:
    """The family a label is actually drawn in, which is what it has to be measured in."""
    return str(style.label_family or style.font_family)


def _labeller(values, text):
    """What to write at a node: ``text`` if given, else ``values`` by name, else the node's name."""
    if text is not None:
        return text
    if values is not None:
        table = {str(k): v for k, v in values.items()}
        return lambda node: _as_text(table.get(node.name))
    return lambda node: node.name


#: Where a label goes beside a tip, per orientation: the offset's direction and the anchor that
#: keeps the text clear of the tip. A turned tree's names sit under (or over) the tips, upright —
#: rotating the whole drawing would turn them on their side, which is why a turned tree is a layout.
_PAST_THE_TIP = {"right": (1.0, 0.0, "start"), "left": (-1.0, 0.0, "end"),
                 "down": (0.0, 1.0, "middle"), "up": (0.0, -1.0, "middle")}


#: Which coordinate carries the depth, and which end of it the tips are at, per orientation. An
#: aligned column stands at the furthest tip's depth, and "furthest" is the far end of that axis.
_DEPTH_AXIS = {"right": (0, max), "left": (0, min), "down": (1, max), "up": (1, min)}


def _column(tree, layout) -> float:
    """The depth coordinate every aligned name is written at: past the furthest tip."""
    which, far = _DEPTH_AXIS[layout.orientation]
    return float(far(layout.coords[leaf][which] for leaf in tree.leaves))


def _leader(canvas, layout, leaf, at_x, at_y, ox, oy, gap, color, width, dash) -> None:
    """The thin dotted join from a tip to its name in the column.

    Drawn from a little past the tip to a little before the text, so it touches neither: a leader
    that runs into the glyphs reads as an underline, and one that starts on the tip reads as more
    branch."""
    sx, sy = canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf))
    # measured to the **column**, not to the text: every name stands one gap past the column, so a
    # tip already at it would still look a gap short and get a stub of a leader lying on itself
    if math.hypot(canvas.px(at_x) - sx, canvas.py(at_y) - sy) < 1.0:
        return
    ex, ey = canvas.px(at_x) + ox * gap, canvas.py(at_y) + oy * gap
    clear = 2.0
    sx, sy = sx + ox * clear, sy + oy * clear
    ex, ey = ex - ox * clear, ey - oy * clear
    canvas.raw_path(f"M {sx:g},{sy:g} L {ex:g},{ey:g}", stroke=color, stroke_width=width,
                    dash=dash, cap="butt")


def tip_labels(*, size=None, color=None, offset: float = 6.0, values=None, text=None,
               upright: bool = False, markup: bool = False, aligned: bool = False,
               leader: bool = True,
               leader_color: str = "#bbbbbb", leader_width: float = 0.7,
               leader_dash: str = "1,3"):
    """Write each leaf's name just past its tip. On a rectangular tree the names sit to the right; on
    a diagonal tree they follow its orientation — to the right, or centred under the tips of a
    ``"down"`` tree — and stay upright; on a radial or unrooted tree they are rotated to run along
    the branch (flipped on the left side so they stay upright). ``values`` (``{tip name: value}``) or
    ``text`` (``text(node) -> str``) writes something else; a tip with no value of its own is left
    unlabelled.

    ``upright=True`` keeps a radial or unrooted tree's names horizontal instead of turning them
    along the branch. A turned name is what a large circular tree needs, where the names make a
    fan; a small diagram of five taxa wants them read straight, as a LaTeX figure sets them.

    ``markup=True`` reads ``*…*`` in the text as italic, so part of a name can be set apart from
    the rest: ``"gene 1 (*Escherichia coli*)"`` writes the species in italics and the gene upright.
    ``\\*`` writes a literal asterisk, and a lone one is left as it is. Off by default, so a label
    that already carries an asterisk is not re-read as markup.

    ``aligned=True`` writes every name in **one column** past the furthest tip, and joins each
    shorter tip to its name with a thin dotted leader. On a tree drawn to scale the tips are ragged
    and so are the names; the alternative was ``align_tips``, which lines them up by drawing the
    terminal branches longer than they are, so the figure no longer shows the lengths it is about.
    ``leader=False`` leaves the joins out, and ``leader_color`` / ``leader_width`` / ``leader_dash``
    set how they look. Rectangular and diagonal trees, where the tips end along one line.
    Returns a layer."""
    say = _labeller(values, text)

    def layer(canvas, tree, layout, style):
        if aligned and layout.kind not in ("rectangular", "diagonal"):
            raise ValueError(f"tip_labels(aligned=True) writes the names in one column past the "
                             f"furthest tip, which needs a layout whose tips end along a line — "
                             f"rectangular or diagonal; got {layout.kind!r}. On a round tree the "
                             f"names already fan out from one centre.")
        edge = _column(tree, layout) if aligned else None
        for leaf in tree.leaves:
            written = say(leaf)
            if not written:
                continue
            if layout.kind in ("rectangular", "diagonal"):
                ox, oy, anchor = _PAST_THE_TIP[layout.orientation]
                # across the text rather than along it, the gap has to clear the glyphs themselves,
                # since the baseline runs through the middle of them
                gap = offset + (0.0 if oy == 0 else (size or style.font_size) * 0.45)
                # aligned, the name stands at the column rather than at its own tip; the tip keeps
                # its place, and the leader is what says which name belongs to it
                at_x = layout.x(leaf) if ox == 0 else (edge if aligned else layout.x(leaf))
                at_y = layout.y(leaf) if oy == 0 else (edge if aligned else layout.y(leaf))
                if aligned and leader:
                    _leader(canvas, layout, leaf, at_x, at_y, ox, oy, gap,
                            leader_color, leader_width, leader_dash)
                fs = size or style.font_size
                tx, ty = canvas.px(at_x) + ox * gap, canvas.py(at_y) + oy * gap
                if markup:
                    wide = canvas.rich_text(tx, ty, split_markup(written), anchor=anchor,
                                            size=fs, color=color, family=style.label_family)
                else:
                    canvas.text(at_x, at_y, written, dx=ox * gap, dy=oy * gap,
                                anchor=anchor, size=size, color=color)
                    wide = text_width(written, family=_face(style), size=fs,
                                      style=style.label_style)
                # the page has to hold these and a key must not be dropped on them, and only this
                # layer knows how long they came out. A "down" tree centres its names under the
                # tips, so the first and the last reach past the panel sideways: the box is claimed
                # on every side it touches, not only the one the tips face.
                canvas.claim_text(tx, ty, wide, fs, anchor=anchor)
                continue
            # radial/unrooted: point outward — from the centre (radial) or the parent (unrooted).
            lx, ly = canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf))
            if layout.kind == "radial":
                ax, ay = canvas.px(0.0), canvas.py(0.0)
            else:
                ax, ay = canvas.px(layout.x(leaf.parent)), canvas.py(layout.y(leaf.parent))
            dx, dy = lx - ax, ly - ay
            dist = math.hypot(dx, dy) or 1.0
            ox, oy = lx + offset * dx / dist, ly + offset * dy / dist
            angle = math.degrees(math.atan2(dy, dx))
            if upright:
                # the name still steps outward from the tree, it just does not turn with it; the
                # anchor follows the side, so the text always grows away from the tip
                place, turn = ("start" if dx >= 0 else "end"), 0.0
            elif -90 <= angle <= 90:
                place, turn = "start", angle
            else:
                place, turn = "end", angle + 180
            fs = size or style.font_size
            if markup:
                wide = canvas.rich_text(ox, oy, split_markup(written), anchor=place, rotate=turn,
                                        size=size, color=color, family=style.label_family)
            else:
                canvas.raw_text(ox, oy, written, anchor=place, rotate=turn, size=size,
                                color=color, style=style.label_style, family=style.label_family)
                wide = text_width(written, family=_face(style), size=fs, style=style.label_style)
            canvas.claim_text(ox, oy, wide, fs, anchor=place, rotate=turn)

    return layer


def node_labels(*, size=None, color="#888888", offset: float = 4.0, values=None, text=None,
                leaves: bool = False, markup: bool = False):
    """Write each internal node's name just above-left of the node. ``values``
    (``{node name: value}``) or ``text`` (``text(node) -> str``) writes something else — an
    ancestral estimate, a support value, a node age — and a node with no value is left unlabelled.
    ``leaves`` also labels the tips, for a value that every node carries. ``markup=True`` reads
    ``*…*`` as italic, as :func:`tip_labels` does. Returns a layer."""
    say = _labeller(values, text)

    def layer(canvas, tree, layout, style):
        for node in tree.walk():
            if node.is_leaf and not leaves:
                continue
            written = say(node)
            if not written:
                continue
            if not layout.grows_along_x:
                # the tree runs down the page, so above-left of the node is on top of its own
                # branch: put the name beside it, clear of the fork
                dx, place = offset, "start"
            else:
                dx, place = -offset, "end"
            fs = size or style.font_size * 0.85
            if markup:
                canvas.rich_text(canvas.px(layout.x(node)) + dx, canvas.py(layout.y(node)) - offset,
                                 split_markup(written), anchor=place, size=fs, color=color,
                                 family=style.label_family)
            else:
                canvas.text(layout.x(node), layout.y(node), written, dx=dx, dy=-offset,
                            anchor=place, size=fs, color=color)

    return layer
