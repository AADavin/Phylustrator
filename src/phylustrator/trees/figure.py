"""The figure — compose a tree plot from layers, then render.

``plot(tree)`` returns a :class:`Figure`; decorations are added with ``+`` (the composable grammar);
``.save(path)`` lays the tree out, draws the branch skeleton, runs each layer, and writes the file.

    >>> fig = plot(tree) + color_branches(values) + tip_labels()   # doctest: +SKIP
    >>> fig.save("tree.pdf")                                        # doctest: +SKIP

A **layer** is just a callable ``(canvas, tree, layout, style) -> None``; that is the whole extension
contract, so new decorations never touch the figure.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field, replace
from typing import Callable

from ..render import OUTWARD, Canvas
from ..style import Style
from .layers.breaks import draw_break_marks
from .layers.clades import clade_extent
from .layout import Layout, diagonal, radial, rectangular, unrooted
from .skeleton import draw_branches
from .tree import Tree

Layer = Callable[[Canvas, Tree, Layout, Style], None]

# Annotated, because the four do not take the same keywords — only the flat two take an
# orientation, and only three take align_tips — so the call below passes what each one accepts.
_LAYOUTS: dict[str, Callable[..., Layout]] = {
    "rectangular": rectangular, "radial": radial, "unrooted": unrooted, "diagonal": diagonal}

#: Layouts that take an ``orientation``: the flat ones. A round layout places its branches by angle
#: from a centre, so there is no direction left to choose.
_TURNS = ("rectangular", "diagonal")

#: The layouts drawn at one scale for both axes, where a circle has to come out round. The others
#: give each axis the whole panel: tip order fills one and depth fills the other, as a phylogram is
#: drawn. The diagonal layout carries the rectangular coordinates, so it belongs with those — at
#: one scale a tree of forty tips and branch lengths near 0.1 was drawn flat, eight pixels of an
#: eight-hundred-pixel panel.
_ROUND = ("radial", "unrooted")

#: How many times the margin is measured and grown before the figure is drawn. The two settle on
#: each other rather than one following from the other: growing the margin narrows the panel, which
#: brings the tips in, which shortens what their names reach past. A name on the panel's own edge
#: settles in one pass, one further in takes a few, and past four there is no pixel left at stake.
_FIT_PASSES = 4

#: The most of one dimension an automatic margin will ever take, as a fraction. A round tree claims
#: on both sides at once, and a name wider than the page would otherwise squeeze the panel out of
#: existence between two margins that each keep growing. At the cap the name is clipped, which is
#: the old behaviour and the honest one: the page is too small for the figure that was asked for.
_FIT_CAP = 0.45

#: Layouts that can end every lineage on the furthest tip's row. The unrooted layout has no row to
#: end on: it places branches by angle from a centre, so there is no tip edge to line them up with.
_ALIGNS = ("rectangular", "radial", "diagonal")

#: Layouts that take the equal-daylight refinement. Only the one it is a refinement of.
_DAYLIGHT = ("unrooted",)


@dataclass
class TipPos:
    """Where a leaf lands on the rendered page, in pixels."""

    name: str
    x: float
    y: float


@dataclass
class NodePos:
    """Where any node — a tip or an internal node — lands on the rendered page, in pixels."""

    name: str
    x: float
    y: float
    is_leaf: bool


@dataclass
class Geometry:
    """The rendered figure's pixel geometry — enough to align something else (a heatmap, an
    alignment) to the tree's tips without redrawing the tree. ``tips`` are in top-to-bottom order;
    ``tip_x`` is the pixel x where the tips end (where a companion panel can begin).

    The x axis too: ``nodes`` holds every node, internal ones included, in preorder, and :meth:`px`
    turns a layout x (a time, under the rectangular layout) into a pixel x. ``xlim`` is the layout's
    x range and ``x_pixels`` its two ends on the page — where a panel under the tree starts and stops
    (see :func:`~phylustrator.compose.below`)."""

    size: tuple[float, float]
    tips: list[TipPos]
    tip_x: float
    nodes: list[NodePos] = field(default_factory=list)
    xlim: tuple[float, float] = (0.0, 1.0)
    x_pixels: tuple[float, float] = (0.0, 1.0)

    def px(self, x: float) -> float:
        """The pixel x of layout x ``x``. The canvas maps x linearly in every layout, so two points
        fix it."""
        (x0, x1), (p0, p1) = self.xlim, self.x_pixels
        return p0 + (x - x0) / ((x1 - x0) or 1.0) * (p1 - p0)


@dataclass
class CladeBox:
    """Where a clade's box lands on the rendered page, in pixels — the anchor a zoom line into
    another panel is drawn to. The same box :func:`~phylustrator.trees.highlight_clade` outlines."""

    clade: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def corners(self) -> tuple:
        """The four corners, clockwise from the top left."""
        return ((self.x0, self.y0), (self.x1, self.y0), (self.x1, self.y1), (self.x0, self.y1))


class Figure:
    """A tree plus a layout, a style, and an ordered list of layers. Immutable-ish: ``+`` returns a
    new figure with one more layer, so a base figure can be reused."""

    def __init__(self, tree: Tree, *, layout: str = "rectangular", stem: bool = True,
                 style: Style | None = None, dashed=None, skeleton: bool = True,
                 cladogram: bool = False, orientation: str = "right", align_tips: bool = False,
                 cut: float | None = None, daylight: bool | int = False,
                 layers: tuple[Layer, ...] = ()) -> None:
        if layout not in _LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {sorted(_LAYOUTS)}")
        if orientation != "right" and layout not in _TURNS:
            raise ValueError(f"the {layout} layout places its branches by angle from a centre, so "
                             f"it has no orientation to take; {' and '.join(_TURNS)} do")
        if daylight and layout not in _DAYLIGHT:
            raise ValueError(f"daylight= is the equal-daylight refinement of the unrooted layout, "
                             f"which spreads it over the whole circle; the {layout} layout places "
                             f"its branches along an axis or an angle of its own, so there is no "
                             f"daylight to share out")
        if cut is not None and not (float(cut) > 0.0):
            raise ValueError(f"cut= is the length to cap a branch at, so it has to be positive; "
                             f"got {cut}")
        if align_tips and layout not in _ALIGNS:
            raise ValueError(f"the {layout} layout has no tip row to line the tips up on: it places "
                             f"branches by angle from a centre. align_tips is for "
                             f"{', '.join(_ALIGNS)}")
        self.tree = tree
        self.layout = layout
        self.stem = stem
        # ignore the branch lengths and space the nodes by topological depth. The layouts have
        # always taken it; the figure could not pass it, so a tree whose deep branches are short
        # (the usual shape of a large tree) could only be drawn with its deep nodes on top of each
        # other, or by rewriting every length to 1 first (#43).
        self.cladogram = cladogram
        self.orientation = orientation
        # end every lineage on the furthest tip's row, as a teaching diagram does: the picture is
        # about the topology, and a tip left short reads as a shallower lineage
        self.align_tips = align_tips
        # cap every branch at this length, so one absurd branch does not take the whole page. The
        # figure marks what it cut: a tree drawn out of scale has to say so.
        self.cut = float(cut) if cut is not None else None
        # spread an unrooted tree over the whole circle rather than leaving one side of it empty
        self.daylight = daylight
        self.style = style or Style()
        self.dashed = dashed  # node names whose branch is drawn dashed (e.g. extinct lineages)
        # whether to draw the default-colour base skeleton first. Turn OFF when a colouring layer
        # paints every branch itself (e.g. color_history), so dashed branches aren't underlaid by a
        # solid line showing through the gaps.
        self.skeleton = skeleton
        self.layers = tuple(layers)
        # the style with the automatic margins grown to fit (see _fitted_style); measuring it costs
        # a drawing, and the drawing, the geometry and the clade boxes all have to agree about it
        self._fitted: Style | None = None
        # the laid-out tree. Kept because the figure is drawn more than once — a measuring pass,
        # the drawing itself, a geometry a companion panel asks for — and equal-daylight takes a
        # couple of seconds on a thousand tips, which would otherwise be paid each time
        self._layout: Layout | None = None

    def __add__(self, layer: Layer) -> "Figure":
        return Figure(self.tree, layout=self.layout, stem=self.stem, style=self.style,
                      dashed=self.dashed, skeleton=self.skeleton, cladogram=self.cladogram,
                      orientation=self.orientation, align_tips=self.align_tips,
                      cut=self.cut, daylight=self.daylight, layers=self.layers + (layer,))

    def with_size(self, width: float, height: float) -> "Figure":
        """A copy of this figure rendered at a given pixel size (same tree, layers, style otherwise).
        Used to fit the tree into a column beside a companion panel."""
        return self.with_style(replace(self.style, width=width, height=height))

    def with_style(self, style: Style) -> "Figure":
        """A copy of this figure drawn with ``style`` (same tree, layers and options otherwise)."""
        return Figure(self.tree, layout=self.layout, stem=self.stem, style=style,
                      dashed=self.dashed, skeleton=self.skeleton, cladogram=self.cladogram,
                      orientation=self.orientation, align_tips=self.align_tips,
                      cut=self.cut, daylight=self.daylight, layers=self.layers)

    def _lay_out(self) -> Layout:
        """This figure's layout. One place, so an option reaches the drawing, ``geometry()`` and
        ``clade_box()` alike — a figure whose box was computed from a different layout than the one
        drawn is a figure whose zoom lines point at nothing."""
        if self._layout is not None:
            return self._layout
        extra: dict = {"orientation": self.orientation} if self.layout in _TURNS else {}
        if self.layout in _ALIGNS:
            extra["align_tips"] = self.align_tips
        if self.layout in _DAYLIGHT:
            extra["daylight"] = self.daylight
        self._layout = _LAYOUTS[self.layout](self.tree, stem=self.stem, cladogram=self.cladogram,
                                             cut=self.cut, **extra)
        return self._layout

    def geometry(self) -> Geometry:
        """The pixel positions of the tips and of every node for this figure's current style, and
        the x-to-pixel mapping — so a companion panel can line up with the tree without redrawing it."""
        layout = self._lay_out()
        canvas = Canvas(self._fitted_style(), layout.xlim, layout.ylim,
                        equal_aspect=(self.layout in _ROUND))
        tips = [TipPos(leaf.name or "", canvas.px(layout.x(leaf)), canvas.py(layout.y(leaf)))
                for leaf in self.tree.leaves]
        tip_x = max((t.x for t in tips), default=canvas.size[0])
        nodes = [NodePos(node.name or "", canvas.px(layout.x(node)), canvas.py(layout.y(node)), node.is_leaf)
                 for node in self.tree.walk()]
        x_pixels = (canvas.px(layout.xlim[0]), canvas.px(layout.xlim[1]))
        return Geometry(canvas.size, tips, tip_x, nodes, layout.xlim, x_pixels)

    def clade_box(self, clade: str, *, pad: float = 0.4) -> CladeBox:
        """The pixel box around the clade rooted at ``clade``, for this figure's current style.

        Computed from the layout, so it is there before anything is drawn: lay out the zoom lines
        from it, then draw. ``highlight_clade`` with the same ``pad`` outlines exactly this box.
        Rectangular layouts only, where a clade is a box; it raises on the others."""
        layout = self._lay_out()
        canvas = Canvas(self._fitted_style(), layout.xlim, layout.ylim,
                        equal_aspect=(self.layout in _ROUND))
        x0, y0, x1, y1 = clade_extent(self.tree, layout, clade, pad)
        return CladeBox(clade, canvas.px(x0), canvas.py(y0), canvas.px(x1), canvas.py(y1))

    def _draw_on(self, style: Style) -> Canvas:
        """Draw the whole figure at ``style`` and hand back the canvas. Used twice over: once or
        twice to measure what the layers write past the panel, and once for the drawing kept."""
        layout = self._lay_out()
        canvas = Canvas(style, layout.xlim, layout.ylim,
                        equal_aspect=(layout.kind in _ROUND))
        # A colouring layer overdraws the skeleton, so it has to know which branches were dashed or
        # it silently paints them solid — a run's extinct lineages disappearing into the colour is
        # exactly how that has gone wrong. The figure knows; the layers see the canvas; so it goes
        # here, and `color_branches(dashed=...)` overrides it when a caller wants something else.
        canvas.dashed = self.dashed
        if self.skeleton:
            _draw_skeleton(canvas, self.tree, layout, style, self.dashed)
        for layer in self.layers:
            layer(canvas, self.tree, layout, style)
        # last, so nothing drawn on the tree covers it: a figure that cut a branch has to say so
        draw_break_marks(canvas, self.tree, layout, style)
        return canvas

    def _fitted_style(self) -> Style:
        """This figure's style with the **automatic** margins grown to hold whatever the layers
        write past the panel — the tip names, chiefly, and the chips and keys past them.

        A side left at ``None`` is automatic: it never comes out narrower than ``margin``, and grows
        only when something would otherwise be drawn off the page, so a figure that already fits
        does not move by a pixel. A side given a number is that number, and a figure that wants the
        panel exactly where it put it says so.

        All four sides, because a round tree's names point outward in every direction and a turned
        tree's are centred under its tips, so the first and the last reach past the panel sideways.
        Two opposite sides growing at once could squeeze the panel away, so each stops at
        :data:`_FIT_CAP` of the page, where the name is clipped as it always was.

        Measured by drawing: only the layer that wrote the text knows how wide it came out, and it
        says so through :meth:`Canvas.claim`. The measuring passes are drawn with the warnings off,
        since a key that does not fit the trial margin is about to be given room."""
        if self._fitted is not None:
            return self._fitted
        automatic = [side for side in OUTWARD if getattr(self.style, f"margin_{side}") is None]
        if not automatic or not self.layers:
            self._fitted = self.style
            return self._fitted
        # where each margin's own page edge is, and the dimension it eats into
        edge = {"left": 0.0, "top": 0.0, "right": self.style.width, "bottom": self.style.height}
        span = {"left": self.style.width, "right": self.style.width,
                "top": self.style.height, "bottom": self.style.height}

        def grown(side: str, canvas: Canvas, trial: Style) -> float | None:
            """The margin ``side`` would need to hold what was drawn past the page, or ``None``
            when what is there already fits."""
            if side not in automatic:
                return None
            over = (canvas.claimed(side, edge[side]) - edge[side]) * OUTWARD[side]
            if over <= 0.5:
                return None
            return min(trial.margin_at(side) + over, _FIT_CAP * span[side])

        trial = self.style
        for _ in range(_FIT_PASSES):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                canvas = self._draw_on(trial)
            wider = {side: grown(side, canvas, trial) for side in OUTWARD}
            wider = {side: v for side, v in wider.items()
                     if v is not None and v > trial.margin_at(side) + 0.5}
            if not wider:
                break
            trial = replace(trial,
                            margin_left=wider.get("left", trial.margin_left),
                            margin_right=wider.get("right", trial.margin_right),
                            margin_top=wider.get("top", trial.margin_top),
                            margin_bottom=wider.get("bottom", trial.margin_bottom))
        self._fitted = trial
        return self._fitted

    def _build(self) -> Canvas:
        return self._draw_on(self._fitted_style())

    def as_svg(self) -> str:
        return self._build().as_svg()

    def save(self, path):
        """Render and write to ``path`` (format from its extension: ``.svg`` / ``.pdf`` / ``.png``)."""
        return self._build().save(path)


def plot(tree: Tree, *, layout: str = "rectangular", stem: bool = True,
         style: Style | None = None, dashed=None, skeleton: bool = True,
         cladogram: bool = False, orientation: str = "right",
         align_tips: bool = False, cut: float | None = None,
         daylight: bool | int = False) -> Figure:
    """Start a figure for ``tree``. Add layers with ``+``, then :meth:`Figure.save`. ``dashed`` is an
    optional set of node names whose branches are drawn dashed (e.g. extinct lineages). Set
    ``skeleton=False`` when a colouring layer paints every branch itself (so dashed branches are not
    underlaid by a solid line).

    ``cladogram=True`` spaces the nodes by topological depth and ignores the branch lengths, which is
    what a large tree needs: drawn to scale, a deep clade's short branches collapse onto the centre
    of a radial tree and cannot be read.

    ``orientation`` turns a flat layout, ``rectangular`` or ``diagonal`` — ``"right"`` (the
    default), ``"down"`` for the root at the top and the tips along the bottom, ``"left"`` or
    ``"up"``. Text stays upright in all four, which is why this is a layout and not a rotation of
    the finished drawing. The round layouts place branches by angle from a centre, so they have no
    orientation to take and refuse it.

    ``align_tips=True`` ends every lineage on the furthest tip's row, which is how a teaching
    diagram lines its taxa up. It changes the drawing and not the tree, so a figure that carries
    lengths should keep its time axis off.

    ``daylight=True`` spreads an **unrooted** tree over the whole circle, by Felsenstein's
    equal-daylight refinement. Equal-angle alone measures every wedge at the root, so a tree with a
    long backbone bends into a half circle and leaves one side of the picture empty.

    ``cut`` caps every branch at that length. One branch of 10 in a tree whose others are 0.1 to 1
    sets the scale and collapses the rest, which is what a gene tree with a capped branch looks
    like. Each branch it shortens is marked on the drawing with a break and its true length, since
    a figure out of scale that does not say so misstates its data.

    The right and bottom margins are **automatic** unless the style pins them: the panel narrows
    until the tip names, the chips past them and any key placed beside the figure all fit the page.
    See :attr:`Style.margin_right`."""
    return Figure(tree, layout=layout, stem=stem, style=style, dashed=dashed, skeleton=skeleton,
                  cladogram=cladogram, orientation=orientation, align_tips=align_tips, cut=cut,
                  daylight=daylight)


def _draw_skeleton(canvas: Canvas, tree: Tree, layout: Layout, style: Style, dashed=None) -> None:
    """The always-present base layer: the branches in the default colour, drawn for whichever layout
    is in force (a colouring layer later overdraws them)."""
    draw_branches(canvas, tree, layout, color=lambda node: style.branch_color,
                  width=style.branch_width, gradient=False, dashed=dashed)
