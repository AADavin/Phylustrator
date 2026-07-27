"""Panels — a matrix or an alignment drawn as a grid, its rows placed by whatever calls it.

A **panel** knows its ``rows`` (labels) and draws itself into a pixel band with :meth:`draw`, given the
pixel ``y`` of each row it should draw. :func:`~genustrator.compose.beside` supplies those y's from a
Phylustrator tree's tips, so the grid lines up with the phylogeny; a panel never positions its own
rows. ``heatmap`` shows a :class:`~genustrator.matrix.Matrix`; ``alignment`` shows residues.
"""

from __future__ import annotations

from ..color import colormap, to_hex

# A clean nucleotide palette; unknown residues fall back to a neutral grey.
NT_COLORS = {"A": "#3a923a", "C": "#3a6ea5", "G": "#e0a327", "T": "#c1443c",
             "U": "#c1443c", "-": "#e9ecef", "N": "#c8cdd2"}


def _row_height(rows) -> float:
    ys = sorted(y for _, y in rows)
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    return (min(gaps) if gaps else 40.0) * 0.82


class Heatmap:
    def __init__(self, matrix, *, cmap="viridis", vmin=None, vmax=None,
                 col_labels=None, grid="#ffffff", title=None):
        self.matrix = matrix
        self.cmap = cmap
        vals = [v for r in matrix.values for v in r]
        self.vmin = 0.0 if vmin is None else vmin
        self.vmax = (max(vals) if vals else 1.0) if vmax is None else vmax
        # label columns only when there are few enough to read
        self.col_labels = (len(matrix.cols) <= 26) if col_labels is None else col_labels
        self.grid = grid
        self.title = title

    @property
    def rows(self):
        return self.matrix.rows

    def draw(self, canvas, x0, x1, rows, style):
        sample = colormap(self.cmap)
        span = (self.vmax - self.vmin) or 1.0
        ncol = len(self.matrix.cols)
        cw = (x1 - x0) / ncol
        rh = _row_height(rows)
        for label, y in rows:
            values = self.matrix.row(label)
            for j, v in enumerate(values):
                t = (v - self.vmin) / span
                canvas.raw_rect(x0 + j * cw, y - rh / 2, cw, rh,
                                fill=to_hex(sample(t)), stroke=self.grid, stroke_width=0.6)
        top = min(y for _, y in rows) - rh / 2
        if self.col_labels:
            for j, c in enumerate(self.matrix.cols):
                cx = x0 + (j + 0.5) * cw
                canvas.raw_text(cx, top - 6, str(c), anchor="start", baseline="alphabetic",
                                size=style.font_size * 0.8, rotate=-60)
        if self.title:
            canvas.raw_text((x0 + x1) / 2, top - 26, self.title, anchor="middle",
                            size=style.font_size, weight="bold")
        self._colorbar(canvas, x0, x1, max(y for _, y in rows) + rh / 2 + 16, style)

    def _colorbar(self, canvas, x0, x1, y, style):
        w, h = min(200.0, x1 - x0), 12.0
        canvas.gradient_bar(self.cmap, x0, y, w, h)
        small = style.font_size * 0.85
        lo, hi = int(round(self.vmin)), int(round(self.vmax))
        vals = list(range(lo, hi + 1))
        if len(vals) > 9:                                  # thin out to ~7 integer ticks
            step = max(1, round((hi - lo) / 7))
            vals = list(range(lo, hi + 1, step))
            if vals[-1] != hi:
                vals.append(hi)
        span = (self.vmax - self.vmin) or 1.0
        for v in vals:
            tx = x0 + (v - self.vmin) / span * w
            canvas.raw_line(tx, y + h, tx, y + h + 4, "#555555", 1.0)
            canvas.raw_text(tx, y + h + 6 + small * 0.7, str(v), anchor="middle", size=small)
        canvas.raw_text(x0 + w + 12, y + h / 2, "copies", anchor="start", size=small)


class Alignment:
    def __init__(self, alignment, *, palette=None, letters=None, title=None, legend=True):
        self.alignment = alignment
        self.palette = palette or NT_COLORS
        self.letters = letters            # None -> auto (draw letters if cells are wide enough)
        self.title = title
        self.legend = legend              # a nucleotide colour key below the alignment

    @property
    def rows(self):
        return self.alignment.rows

    def draw(self, canvas, x0, x1, rows, style):
        L = self.alignment.length
        if L == 0:
            return
        cw = (x1 - x0) / L
        rh = _row_height(rows)
        letters = (cw >= 7.0) if self.letters is None else self.letters
        for label, y in rows:
            seq = self.alignment.seqs.get(label, "")
            for s, res in enumerate(seq):
                cx = x0 + s * cw
                canvas.raw_rect(cx, y - rh / 2, cw, rh,
                                fill=self.palette.get(res, "#c8cdd2"),
                                stroke="#ffffff", stroke_width=0.4)
                if letters:
                    canvas.raw_text(cx + cw / 2, y, res, anchor="middle",
                                    color="#ffffff", size=min(rh, cw) * 0.72, weight="bold")
        top = min(y for _, y in rows) - rh / 2
        # a light ruler every 10 sites
        for s in range(0, L + 1, 10):
            cx = x0 + s * cw
            canvas.raw_line(cx, top - 4, cx, top, "#98a2a8", 1.0)
            canvas.raw_text(cx, top - 7, str(s), anchor="middle", baseline="alphabetic",
                            size=style.font_size * 0.75)
        if self.title:
            canvas.raw_text((x0 + x1) / 2, top - 24, self.title, anchor="middle",
                            size=style.font_size, weight="bold")
        if self.legend:
            self._legend(canvas, x0, max(y for _, y in rows) + rh / 2 + 22, style)

    def _legend(self, canvas, x0, y, style):
        sw, fs = 20.0, style.font_size * 1.15          # a visible key
        x = x0
        for res in ("A", "C", "G", "T"):
            canvas.raw_rect(x, y, sw, sw, fill=self.palette.get(res, "#c8cdd2"),
                            stroke="#ffffff", stroke_width=0.8)
            canvas.raw_text(x + sw + 6, y + sw / 2, res, anchor="start", size=fs, weight="bold")
            x += sw + 6 + fs * 0.8 + 16


class States:
    """A **categorical** matrix panel — each cell coloured by a value→colour ``palette`` (a discrete
    sibling of :class:`Heatmap`: no gradient, no numeric scale). For character-state / presence–absence
    matrices beside a tree — e.g. two binary characters shown as two columns of filled / open cells.
    ``legend_labels`` maps a value to the text shown for it in the key (``{"1": "present"}``)."""

    def __init__(self, matrix, *, palette=None, col_palettes=None, legend=True, legend_labels=None,
                 title=None, col_labels=True, grid="#1a1a1a", other="#c8cdd2"):
        if palette is None and col_palettes is None:
            raise ValueError("states() needs palette= (one for all columns) or col_palettes= (per column)")
        self.palette = {str(k): v for k, v in palette.items()} if palette else None
        # a per-column palette overrides the shared one for that column (e.g. one trait per column)
        self.col_palettes = ([{str(k): v for k, v in p.items()} for p in col_palettes]
                             if col_palettes else None)
        self.matrix = matrix
        self.legend = legend
        self.legend_labels = {str(k): v for k, v in (legend_labels or {}).items()}
        self.title = title
        self.col_labels = col_labels
        self.grid = grid
        self.other = other                 # colour for a value not in the palette

    @property
    def rows(self):
        return self.matrix.rows

    def _fill(self, j, v):
        pal = self.col_palettes[j] if self.col_palettes else self.palette
        return pal.get(str(v), self.other)

    def draw(self, canvas, x0, x1, rows, style):
        ncol = len(self.matrix.cols)
        cw = (x1 - x0) / ncol
        rh = _row_height(rows)
        for label, y in rows:
            for j, v in enumerate(self.matrix.row(label)):
                canvas.raw_rect(x0 + j * cw, y - rh / 2, cw, rh,
                                fill=self._fill(j, v),
                                stroke=self.grid, stroke_width=0.8)
        top = min(y for _, y in rows) - rh / 2
        if self.col_labels:
            for j, c in enumerate(self.matrix.cols):
                canvas.raw_text(x0 + (j + 0.5) * cw, top - 6, str(c), anchor="middle",
                                baseline="alphabetic", size=style.font_size, weight="bold")
        if self.title:
            canvas.raw_text((x0 + x1) / 2, top - 26, self.title, anchor="middle",
                            size=style.font_size, weight="bold")
        if self.legend and self.palette:      # a shared-palette key; per-column panels label elsewhere
            self._legend(canvas, x0, max(y for _, y in rows) + rh / 2 + 20, style)

    def _legend(self, canvas, x0, y, style):
        sw, fs = 20.0, style.font_size
        x = x0
        for val, color in self.palette.items():
            canvas.raw_rect(x, y, sw, sw, fill=color, stroke=self.grid, stroke_width=0.9)
            text = self.legend_labels.get(val, val)
            canvas.raw_text(x + sw + 6, y + sw / 2, text, anchor="start", size=fs)
            x += sw + 6 + fs * 0.62 * len(text) + 18


class Bars:
    """A per-row **bar** panel — one horizontal bar per tree tip, its length ∝ the tip's value. For a
    per-tip scalar beside a tree (a genome size, a count, a rate). ``values`` is ``{row label: number}``;
    ``colors`` optionally tints the bar per row (e.g. by a trait), else the flat ``color``. ``max_value``
    fixes the scale (default: the largest value); ``label`` names the axis."""

    def __init__(self, values, *, color="#6a9bd8", colors=None, max_value=None, label="", axis=True,
                 tick_size=None, label_size=None):
        self.values = {str(k): float(v) for k, v in values.items()}
        self.color = color
        self.colors = {str(k): v for k, v in colors.items()} if colors else None
        self.max_value = max_value
        self.label = label
        self.axis = axis
        self.tick_size = tick_size          # axis tick font (default: from the style)
        self.label_size = label_size        # axis label font (default: from the style)

    @property
    def rows(self):
        return list(self.values)

    def draw(self, canvas, x0, x1, rows, style):
        vmax = self.max_value or max(self.values.values(), default=1.0) or 1.0
        rh = _row_height(rows)
        span = x1 - x0
        for label, y in rows:
            w = span * min(max(self.values.get(label, 0.0) / vmax, 0.0), 1.0)
            fill = (self.colors or {}).get(label, self.color)
            canvas.raw_rect(x0, y - rh / 2, w, rh, fill=fill, stroke="#ffffff", stroke_width=0.6)
        if self.axis:
            # +14 below the bottom tip — the exact offset trees.time_axis uses, so in a beside()
            # composite a tree's time axis and this axis land at the identical y (and share the tick /
            # label offsets below), giving two perfectly aligned, same-size axes
            self._axis(canvas, x0, x1, max(y for _, y in rows) + 14, vmax, style)

    def _axis(self, canvas, x0, x1, y, vmax, style):
        ts = self.tick_size or style.font_size * 0.85
        ls = self.label_size or style.font_size
        canvas.raw_line(x0, y, x1, y, "#333333", 1.2)          # match trees.time_axis exactly
        for frac in (0.0, 0.5, 1.0):
            tx = x0 + (x1 - x0) * frac
            canvas.raw_line(tx, y, tx, y + 5, "#333333", 1.2)
            canvas.raw_text(tx, y + ts + 3, f"{round(vmax * frac)}", anchor="middle", size=ts)
        if self.label:
            canvas.raw_text((x0 + x1) / 2, y + ts + ls + 4, self.label, anchor="middle", size=ls)


def heatmap(matrix, **kw) -> Heatmap:
    """A heatmap panel for a :class:`~genustrator.matrix.Matrix` (genomes × families)."""
    return Heatmap(matrix, **kw)


def bars(values, **kw) -> Bars:
    """A bar panel — one horizontal bar per tree tip, length ∝ value. For a per-tip scalar (a genome
    size, a count) beside a tree; ``colors`` tints bars per row (e.g. by a trait)."""
    return Bars(values, **kw)


def states(matrix, **kw) -> States:
    """A categorical state matrix panel (rows × discrete characters), colours from a value→colour
    ``palette`` — for presence–absence or discrete character states beside a tree."""
    return States(matrix, **kw)


def alignment(aln, **kw) -> Alignment:
    """An alignment panel for an :class:`~genustrator.matrix.Alignment` (genomes × sites)."""
    return Alignment(aln, **kw)
