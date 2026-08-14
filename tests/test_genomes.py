"""Genomes domain: the three layouts render, the gene/synteny/axis layers draw, and the
heatmap / alignment panels produce SVG. Mirrors ``test_figure.py`` for the trees domain."""

import math
import re

import pytest

from phylustrator import Style, beside
from phylustrator.genomes import (
    AA_COLORS,
    Alignment,
    Chromosome,
    Gene,
    Genome,
    Matrix,
    alignment,
    bars,
    genes,
    grid,
    heatmap,
    plot,
    position_axis,
    stack,
    states,
    synteny,
    tracks,
)
from phylustrator.genomes.layout import circular
from phylustrator.genomes.track import _draw_circular
from phylustrator.trees import loads
from phylustrator.trees import plot as tree_plot


def _genome(name, order):
    """A one-chromosome genome; ``order`` is the family per gene, left to right."""
    gs = [Gene(family=f, strand=1 if i % 2 == 0 else -1, position=i, start=i * 100, end=i * 100 + 90)
          for i, f in enumerate(order)]
    return Genome(name=name, chromosomes=[Chromosome(id="c1", genes=gs, topology="circular", length=len(gs) * 100)])


@pytest.mark.parametrize("layout", ["linear", "circular"])
def test_layouts_render_with_genes(layout):
    svg = (plot(_genome("g", ["1", "2", "3", "1"]), layout=layout) + genes(by="family")).as_svg()
    assert svg.lstrip().startswith("<") and "#" in svg


def test_genes_by_strand_uses_palette():
    svg = (plot(_genome("g", ["1", "2", "3"]))
           + genes(by="strand", palette={"1": "#3a7ca5", "-1": "#c1443c"})).as_svg()
    assert "#3a7ca5" in svg and "#c1443c" in svg


def test_stack_synteny_links_shared_families():
    a, b = _genome("a", ["1", "2", "3"]), _genome("b", ["3", "1", "2"])   # rearranged
    svg = (stack([a, b]) + genes(by="family") + synteny(opacity=0.4)).as_svg()
    assert svg.lstrip().startswith("<") and "opacity" in svg.lower()


def test_position_axis_on_nucleotide_ring():
    svg = (plot(_genome("g", ["1", "2", "3", "4"]), layout="circular", coordinates="nucleotide")
           + genes(by="strand") + position_axis()).as_svg()
    assert svg.lstrip().startswith("<")


def test_circular_shared_scale_shortens_the_small_chromosome():
    """A karyotype: under ``scale="shared"`` a short chromosome draws a short arc."""
    big = _genome("g", list("12345678")).chromosomes[0]
    small = Chromosome(id="c2", genes=_genome("s", ["9", "10"]).chromosomes[0].genes,
                       topology="circular", length=200)
    g = Genome(name="k", chromosomes=[big, small])
    arc = {}
    for scale in ("each", "shared"):
        lay = circular(g, scale=scale)
        a0, a1, _ = lay.boxes[id(small.genes[0])]
        arc[scale] = abs(a1 - a0)
    assert arc["shared"] < arc["each"] / 3          # 8 slots wide, not 2
    with pytest.raises(ValueError, match="unknown scale"):
        circular(g, scale="both")


def _karyotype():
    big = _genome("g", list("12345678")).chromosomes[0]
    small = Chromosome(id="c2", genes=_genome("s", ["9", "10"]).chromosomes[0].genes,
                       topology="circular", length=200)
    return Genome(name="k", chromosomes=[big, small]), big, small


def test_circular_row_puts_each_chromosome_on_its_own_circle():
    """A karyotype: ``arrange="row"`` gives every chromosome a centre of its own, left to right."""
    g, big, small = _karyotype()
    lay = circular(g, arrange="row")
    cx = [lay.centre(c.genes[0])[0] for c in (big, small)]
    assert cx[0] < cx[1]                                  # chromosome 0 leftmost
    assert len(set(lay.ring_centres)) == 2
    assert lay.xlim[1] - lay.xlim[0] > lay.ylim[1] - lay.ylim[0]     # a row is wider than it is tall
    assert (plot(g, layout="circular", arrange="row") + genes(by="family")).as_svg().startswith("<")
    with pytest.raises(ValueError, match="unknown arrange"):
        circular(g, arrange="stack")


def test_circular_row_scale_shared_sizes_the_circle_by_gene_count():
    """Under ``scale="shared"`` the radius follows the gene count, so the thickness must follow it
    too — one absolute thickness would draw the short chromosome as a blob."""
    g, big, small = _karyotype()
    each, shared = circular(g, arrange="row"), circular(g, arrange="row", scale="shared")
    assert each.rings[0] == each.rings[1]                      # every circle the same
    assert shared.rings[1] == pytest.approx(shared.rings[0] * 2 / 8)
    assert shared.half_height(shared.rings[1]) < shared.half_height(shared.rings[0])
    # a number fixes the reference explicitly, so two genomes can be drawn to one scale
    assert circular(g, arrange="row", scale=16).rings[0] == pytest.approx(0.5)
    with pytest.raises(ValueError, match="positive number"):
        circular(g, scale=0)


def test_extent_reports_the_layout_the_canvas_fits_to():
    g, _, _ = _karyotype()
    fig = plot(g, layout="circular", arrange="row")
    assert fig.extent() == (circular(g, arrange="row").xlim, circular(g, arrange="row").ylim)


def test_a_circular_arrow_flares_its_head_and_caps_its_length():
    """The arrowhead is sized on the *magnitude* of the gene's arc.

    Angles run clockwise, so the arc is negative, and taking it signed made `min(0.45 * span, 11°)`
    always pick the 45% — a five-gene ring drew heads nearly half the gene long — while the flare
    term went negative and `max(hh, …)` collapsed to the body width, so no arrow ever flared. Both
    read as a wedge rather than an arrow, which is what the shape is for."""
    class _Recorder:
        def __init__(self):
            self.shapes = []

        def polygon(self, pts, **kw):
            self.shapes.append(pts)

    gs = [Gene(family=str(i), strand=1, position=i) for i in range(5)]   # long genes: 72° apiece
    lay = circular(Genome("g", [Chromosome("c1", gs, topology="circular")]))
    rec = _Recorder()
    _draw_circular(rec, lay, lambda g: "#000000", Style())
    a0, a1, R = lay.box(gs[0])
    hh = lay.half_height(R)
    radii = [math.hypot(x, y) for x, y in rec.shapes[0]]
    assert max(radii) > R + hh * 1.05                # the head flares past the body
    # the head is at most 11 degrees of arc, not 45% of a 72-degree gene
    beyond = [math.atan2(y, x) for x, y in rec.shapes[0] if math.hypot(x, y) > R + hh * 1.001]
    assert max(beyond) - min(beyond) < math.radians(11) * 1.2


def test_a_ring_runs_clockwise_from_the_top_like_the_linear_track():
    """A forward gene points the way the coordinate increases — right on a track, clockwise on a ring.

    The page's y grows downward and the layout's angles do not, so drawing sin(a) straight reflected
    the picture: the ring began at the bottom and ran anticlockwise, and a forward gene at the top of
    it pointed left — the mirror image of the same genome drawn linearly. `_polar` negates y to undo
    that, and this pins it, because it is invisible in any single ring."""
    def centres(layout_kind):
        gs = [Gene(family=str(i), strand=1, position=i) for i in range(4)]
        g = Genome("g", [Chromosome("c1", gs, topology="circular")])
        svg = (plot(g, layout=layout_kind, style=Style(width=400, height=400, margin=40))
               + genes(by="family")).as_svg()
        out = []
        for s in re.findall(r'<[^>]*?(?:points|d)="([^"]{25,})"', svg)[:4]:
            v = [float(x) for x in re.findall(r"-?\d+\.?\d*", s)]
            out.append((sum(v[0::2]) / len(v[0::2]), sum(v[1::2]) / len(v[1::2])))
        return out

    ring = centres("circular")
    assert len(ring) == 4
    # clockwise from the top, on a page whose y grows down: right, then down, then left, then up
    assert ring[0][0] > 200 and ring[0][1] < 200, "position 0 is not in the top-right quadrant"
    assert ring[1][1] > ring[0][1], "the coordinate does not run downward on the right — not clockwise"
    assert ring[2][0] < ring[1][0], "the coordinate does not run leftward along the bottom"
    assert ring[3][1] < ring[2][1], "the coordinate does not run upward on the left"


def test_heatmap_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    m = Matrix(rows=["a", "b"], cols=["f1", "f2", "f3"], values=[[1, 0, 2], [0, 1, 1]])
    assert beside(tree, heatmap(m)).as_svg().lstrip().startswith("<")


def test_alignment_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    aln = Alignment(rows=["a", "b"], seqs={"a": "ACGT", "b": "AGGT"}, kind="nt")
    assert beside(tree, alignment(aln, letters=False)).as_svg().lstrip().startswith("<")


def test_a_protein_alignment_keys_the_chemical_classes_not_twenty_residues():
    """The nucleotide key names the four bases; the protein one names the six classes, because a row
    of twenty swatches is wider than the alignment and says less."""
    tree = tree_plot(loads("(a:1,b:1)R;"))
    aln = Alignment(rows=["a", "b"], seqs={"a": "MKLW", "b": "MRLF"}, kind="aa")
    svg = beside(tree, alignment(aln, palette=AA_COLORS, letters=False)).as_svg()
    for chemistry in ("hydrophobic", "aromatic", "positive"):
        assert chemistry in svg
    # every residue its own shade, but a class shares its hue: K and R are both reds, and neither
    # is any shade of the hydrophobic blue
    assert len({AA_COLORS[r] for r in "AVLIMCFWYSTNQKRHDEGP"}) == 20
    assert AA_COLORS["K"] != AA_COLORS["R"]
    reds = {AA_COLORS[r] for r in "KRH"}
    assert all(c[1:3] > c[5:7] for c in reds)                 # more red than blue in every one
    assert not reds & {AA_COLORS[r] for r in "AVLIMC"}

    nt = Alignment(rows=["a", "b"], seqs={"a": "ACGT", "b": "AGGT"}, kind="nt")
    assert "hydrophobic" not in beside(tree, alignment(nt, letters=False)).as_svg()


def test_states_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    m = Matrix(rows=["a", "b"], cols=["X", "Y"], values=[["1", "0"], ["1", "1"]])
    svg = beside(tree, states(m, palette={"0": "#ffffff", "1": "#1a1a1a"},
                              legend_labels={"1": "present", "0": "absent"})).as_svg()
    assert svg.lstrip().startswith("<") and "#1a1a1a" in svg


def test_states_panel_per_column_palettes():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    m = Matrix(rows=["a", "b"], cols=["X", "Y"], values=[["1", "1"], ["0", "0"]])
    svg = beside(tree, states(m, col_palettes=[{"1": "#2E6E8E"}, {"1": "#C55A3B"}],
                              legend=False)).as_svg()          # each column its own trait colour
    assert "#2E6E8E" in svg and "#C55A3B" in svg


def test_states_panel_needs_a_palette():
    m = Matrix(rows=["a"], cols=["X"], values=[["1"]])
    with pytest.raises(ValueError):
        states(m)


def test_bars_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    svg = beside(tree, bars({"a": 10.0, "b": 4.0}, colors={"a": "#123456"},
                            label="size", tick_size=12, label_size=14)).as_svg()
    assert svg.lstrip().startswith("<") and "#123456" in svg   # a per-row bar was coloured


# --- tracks: genomes as a panel beside a tree -------------------------------------------------

def _tracks_tree():
    return loads("((a:1,b:1):1,(c:1,d:1):1);")


def test_tracks_rows_are_the_genome_names():
    panel = tracks([_genome("a", "0123"), _genome("b", "0123")])
    assert panel.rows == ["a", "b"]


def test_tracks_beside_a_tree_draws_every_tip():
    """The figure this panel exists for: a tree with each leaf's gene order next to it. `stack`
    cannot make it — it places its own rows evenly and knows nothing about the tree."""
    genomes = [_genome(n, "0123") for n in ("a", "b", "c", "d")]
    svg = beside(tree_plot(_tracks_tree()), tracks(genomes), width=600).as_svg()
    assert svg.count("<path") + svg.count("<polyline") > 0        # ribbons and/or arrows drawn
    assert len(svg) > 500


def test_tracks_colours_by_position_in_the_reference():
    """``reference`` is what makes a rearrangement legible: a family's colour is its rank in the
    ancestral order, so a collinear genome reads as a gradient and a break in it is an event."""
    genomes = [_genome("a", "0123")]
    forward = tracks(genomes, reference=["0", "1", "2", "3"]).palette
    reversed_ = tracks(genomes, reference=["3", "2", "1", "0"]).palette
    assert forward["0"] != forward["3"]                            # the ends differ
    assert forward["0"] == reversed_["3"] and forward["3"] == reversed_["0"]


def test_tracks_palette_overrides_the_colormap():
    panel = tracks([_genome("a", "01")], palette={"0": "#ff0000", "1": "#00ff00"})
    assert panel.palette == {"0": "#ff0000", "1": "#00ff00"}


def test_tracks_can_omit_the_ribbons():
    genomes = [_genome(n, "0123") for n in ("a", "b")]
    with_links = beside(tree_plot(loads("(a:1,b:1);")), tracks(genomes), width=600).as_svg()
    without = beside(tree_plot(loads("(a:1,b:1);")), tracks(genomes, ribbons=False),
                     width=600).as_svg()
    assert len(without) < len(with_links)


def test_tracks_ignores_a_genome_that_is_not_a_tip():
    """`beside` matches rows to tips by name, so a genome with no tip is simply not drawn —
    the same rule every other panel follows."""
    genomes = [_genome(n, "0123") for n in ("a", "b", "stranger")]
    svg = beside(tree_plot(loads("(a:1,b:1);")), tracks(genomes), width=600).as_svg()
    assert len(svg) > 500


# --- a matrix as a figure in its own right --------------------------------------------------------

def _matrix(nrow=5, ncol=4):
    return Matrix(rows=[f"f{i}" for i in range(nrow)],
                             cols=[f"g{j}" for j in range(ncol)],
                             values=[[(i + j) % 2 for j in range(ncol)] for i in range(nrow)])


def test_grid_draws_one_cell_per_value(tmp_path):
    """`heatmap` is a panel and only exists beside a tree, which is placed by `beside`. A phyletic
    profile of a few hundred families is the whole picture, so it needs a figure of its own."""
    M = _matrix(5, 4)
    svg = grid(M).as_svg()
    assert svg.count("<rect") == 5 * 4 + 1              # cells, plus the background


def test_grid_takes_a_palette_for_categories(tmp_path):
    """Presence/absence is two categories, not a ramp: a colormap between them would imply an
    ordering they do not have."""
    svg = grid(_matrix(), palette={0: "#F4F3EE", 1: "#26565B"}).as_svg()
    assert "#F4F3EE".lower() in svg.lower() and "#26565B".lower() in svg.lower()


def test_grid_drops_the_cell_border_when_cells_are_tiny():
    """At a few thousand cells a hairline stroke is most of the ink and the data hides behind a grey
    mesh. A border needs a cell with an inside to be a border of."""
    big = Matrix(rows=[str(i) for i in range(300)], cols=[str(j) for j in range(40)],
                            values=[[1] * 40 for _ in range(300)])
    assert 'stroke="#ffffff"' not in grid(big).as_svg()
    assert 'stroke="#ffffff"' in grid(_matrix(4, 3)).as_svg()   # roomy cells keep it
    # and the decision can be taken out of its hands, either way
    assert 'stroke="#ffffff"' not in grid(_matrix(4, 3), borders=False).as_svg()
    assert 'stroke="#ff0000"' in grid(big, borders="#ff0000").as_svg()


def test_grid_is_empty_rather_than_broken_for_an_empty_matrix():
    empty = Matrix(rows=[], cols=[], values=[])
    assert grid(empty).as_svg().count("<rect") == 1              # background only


def test_a_bar_panel_puts_its_axis_under_the_tree_not_under_the_last_bar():
    """Two axes beside each other have to sit at the same height.

    `beside` used to hand a panel only the rows it had values for, and `Bars` puts its axis under the
    last row it is handed — so a tree whose bottom tips carry no value drew the bar axis above the
    tree's own time axis. Every conditioned figure with an extinct tip at the foot of the tree had
    the two out by tens of pixels."""
    def axis_y(values):
        tree = tree_plot(loads("(((a:1,b:1):1,c:2):1,d:3)R;"))
        svg = beside(tree, bars(values, label="x"), width=600).as_svg()
        ticks = re.findall(r'<text x="[\d.]+" y="([\d.]+)"[^>]*>0</text>', svg)
        return float(ticks[-1])

    all_four = axis_y({"a": 1.0, "b": 2.0, "c": 1.5, "d": 0.5})
    top_two = axis_y({"a": 1.0, "b": 2.0})          # c and d have no value
    assert top_two == all_four, ("the axis moved up to the last valued tip; it belongs under the "
                                 "tree, so that it lines up with the tree's own axis")


def test_bar_axis_ticks_say_where_they_are():
    """`round()` wrote the middle tick of a 0–3 axis as '1'. It is at 1.5."""
    svg = beside(tree_plot(loads("(a:1,b:1)R;")), bars({"a": 3.0, "b": 1.0}), width=600).as_svg()
    assert ">1.5<" in svg.replace("</text>", "<"), "the halfway tick is not labelled 1.5"
