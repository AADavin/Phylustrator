# Phylustrator

A small, composable plotter for evolutionary figures. Two domains share one grammar: **`ph.trees`**
plots phylogenetic trees and **`ph.genomes`** plots genomes, synteny and alignments. Start a figure,
add layers with `+`, and save it to SVG, PDF, or PNG.

![A 100-tip tree with branches coloured by a Brownian-motion trait](https://raw.githubusercontent.com/AADavin/Phylustrator/main/docs/img/tree.png)

## Install

```bash
pip install git+https://github.com/AADavin/Phylustrator
```

SVG output needs nothing else; for PDF/PNG also install `cairosvg` (`pip install cairosvg`).

## Trees

```python
import phylustrator as ph

tree = ph.trees.loads("((((Human:6,Chimp:6)a:2,Gorilla:8)b:3,Orang:11)c:5,Gibbon:16)root;")
brain = {"Human": 1350, "Chimp": 400, "Gorilla": 500, "Orang": 400, "Gibbon": 100,
         "a": 650, "b": 560, "c": 500, "root": 470}

(ph.trees.plot(tree)
 + ph.trees.color_branches(brain)
 + ph.trees.tip_labels()
 + ph.trees.colorbar("brain size (cc)")
 + ph.trees.time_axis("million years")).save("tree.png")
```

That is the whole idea: `plot(tree)` starts a figure and each `+ layer` adds one decoration.

- **Layouts** — `rectangular` (default), `radial`, `unrooted`, `diagonal`. The diagonal layout
  joins each parent to its child with one straight slanted segment, the shape of a textbook
  diagram, and is the one that turns: `plot(tree, layout="diagonal", orientation="down")` puts the
  root at the top with the tips along the bottom, names upright.
- **Styles** — `ph.styles.tikz()` is a whole figure's look in one call: serif text, fine black
  lines, squared-off branch ends, a white page — a small figure that sits in a LaTeX document
  without looking like it came from somewhere else. Every field is an ordinary `Style` field, so
  `tikz(branch_width=1.4)` is yours to set. With Computer Modern installed, `ph.styles.tikz_math()`
  plus `tip_labels(values={n: ph.styles.maths(n) for n in names})` matches a LaTeX document
  exactly: the title in cmr, the taxon names in cmmi, the face `$a$` is set in.
- **Layers** — `color_branches`, `color_history`, `tip_labels`, `node_labels`, `tip_track`,
  `branch_events`, `branch_markers`, `branch_spindles`, `node_halves`, `colorbar`, `legend`, `time_axis`,
  `time_marker`, `scale_bar`, `note`, `title`, `highlight_clade`, `highlight_lineage`,
  `node_intervals`, `node_dots`. `legend` and `note` take a corner, or `loc="right"` /
  `loc="below"` to sit outside the panel where no tree shape can cover them;
  `title` is centred over the panel. `branch_spindles` marks a branch with a lens that fades into
  the branch's own colour, and `node_halves` puts a two-colour disc on a node.
  An event given to `branch_events` can carry a `weight`, so arcs and marks scale with the count
  they stand for.
- **Panels** — `node_points`, placed under a rectangular tree with `ph.below(tree, panel)`. The panel
  shares the tree's time axis, so a value measured at a node sits directly under that node.

## One page, several figures

`ph.page` nests whole figures as vectors — two trees side by side, a tree beside a panel, a small
inset — with one title centred over the lot and optional panel letters:

```python
ph.page([[ph.trees.plot(t1) + ph.trees.tip_labels(),
          ph.trees.plot(t2) + ph.trees.tip_labels()]],
        width=482, units="pt", title="The same tree under two analyses",
        letters=True).save("figure1.pdf")
```

`units` gives the page a physical size, so it hits a journal's column width exactly. `ph.beside`
and `ph.below` still pair one tree with one companion panel, lined up on the tips or on the time
axis; a composite from either can itself go on a page.

## Genomes

The same grammar, for genome maps. Plot a genome as a line or a ring, colour genes by family or
strand, link two genomes with synteny ribbons, or set a copy-number heatmap / alignment beside a tree.

```python
import phylustrator as ph

G = ph.genomes.read_gff("genome.gff")           # {name: Genome}
genome = next(iter(G.values()))
(ph.genomes.plot(genome, layout="circular", coordinates="nucleotide")
 + ph.genomes.genes(by="strand")
 + ph.genomes.position_axis()).save("ring.png")
```

- **Layouts** — `linear`, `circular`, and `stack` (one genome per row, for synteny).
- **Layers** — `genes`, `synteny`, `highlight`, `position_axis`.
- **Panels** — `heatmap`, `alignment`, placed next to a tree with `ph.beside(tree, panel)`.

## ZOMBI2 I/O

`ph.zombi` reads the output of the [ZOMBI2](https://github.com/AADavin/zombi2) genome-evolution
simulator into the data models above — kept in one clearly-separated layer so the core stays
format-agnostic:

```python
import phylustrator as ph

G = ph.zombi.read_genomes("run/genomes")        # {lineage: Genome}
M = ph.zombi.read_profiles("run")               # family x genome copy-number Matrix
aln = ph.zombi.read_alignment("run", family=0)  # Alignment keyed by genome
tree = ph.zombi.read_species_tree("run")        # a Tree
```

## Command line

`phyl` is a one-shot tree viewer — hand it a Newick file:

```bash
phyl tree.nwk                 # render to a temporary PDF and open it
phyl tree.nwk -o fig.svg      # save instead (format from the extension: .svg / .pdf / .png)
phyl tree.nwk --radial --no-labels
```

Flags: `--layout {rectangular,radial,unrooted,diagonal}` (or `--radial` / `--unrooted`),
`--orientation {right,down,left,up}` for a diagonal tree, `--tikz`, `--no-labels`,
`--node-labels`, `--no-stem`, `--no-open`. Colouring and everything else live in the Python API.

## Dependencies

Only `drawsvg` (plus `cairosvg` for PDF/PNG). No `ete3`, no `matplotlib`.

## License

MIT — see [LICENSE](https://github.com/AADavin/Phylustrator/blob/main/LICENSE).
