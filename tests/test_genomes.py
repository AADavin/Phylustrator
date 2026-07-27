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
    heatmap,
    plot,
    position_axis,
    stack,
    states,
    synteny,
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
