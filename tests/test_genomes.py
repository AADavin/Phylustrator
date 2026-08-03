"""Genomes domain: the three layouts render, the gene/synteny/axis layers draw, and the
heatmap / alignment panels produce SVG. Mirrors ``test_figure.py`` for the trees domain."""

import pytest

from phylustrator import beside
from phylustrator.genomes import (
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


def test_heatmap_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    m = Matrix(rows=["a", "b"], cols=["f1", "f2", "f3"], values=[[1, 0, 2], [0, 1, 1]])
    assert beside(tree, heatmap(m)).as_svg().lstrip().startswith("<")


def test_alignment_panel_beside_tree():
    tree = tree_plot(loads("(a:1,b:1)R;"))
    aln = Alignment(rows=["a", "b"], seqs={"a": "ACGT", "b": "AGGT"}, kind="nt")
    assert beside(tree, alignment(aln, letters=False)).as_svg().lstrip().startswith("<")


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
