# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-09-21

### Added
- An event given to `trees.branch_events` may carry its own style. `weight` (0-1) scales the arrow's
  width, the glyph's size and the opacity of both, between a floor and the kind's full style — the
  figure this is for is transfers summed over gene families, where every pair carries a count and a
  few hundred arcs only read if width follows it (`weight = n / n_max`). `color` and `size` override
  the kind's colour and the layer's size for that one event. An event with no override is drawn
  exactly as before, and the legend keeps showing the kind's own colour. `weight_floor` (default
  0.25) is how much of the style a weight of 0 keeps, so the lightest mark stays on the page (#11).
- `Canvas.arrow` and `Canvas.raw_marker` take an `opacity`. A fully opaque arrow or glyph writes no
  opacity attribute, so every figure drawn before this renders byte for byte as it did.

## [0.4.0] - 2026-09-21

### Added
- `trees.title(text)` — a title centred over the panel, in the top margin above the tree. `note`
  pins text to a corner, which is where something *about* a figure belongs; a title belongs over the
  middle of it. `size`, `dy` and `color` set the rest, and the title stays on the page even on a
  thin top margin (#9).
- `trees.legend` gains `loc`, the four corners `branch_events` already takes. The default stays
  `"top-left"`, so no existing figure moves its legend. A right corner right-aligns the block on the
  right margin, and a bottom corner ends it on the bottom margin. A rectangular tree fills the upper
  left of its panel, so the top left is often the one corner a legend cannot share (#10).

### Changed
- `note` and `legend` raise on a `loc` that is not one of the four corners, at the point it is
  written. `note(loc="top-centre")` used to fall through the `"left" in loc` test and print
  right-aligned; the message names `title()` for the centred case.

## [0.3.1] - 2026-09-17

### Fixed
- `trees.time_marker` drew nothing on the radial and unrooted layouts, silently. It now draws a
  circle at that distance from the centre on a radial tree, with the same colour, width and dash
  arguments. A radial time is shifted by the root stem, as `branch_events` already shifts its
  events, because the radial layout starts at the crown. The unrooted layout raises instead of
  skipping: it places branches by angle, so a distance from the origin is not a place on it (#8).

## [0.3.0] - 2026-09-14

### Added
- `ph.below(tree, panel)` — the x-axis twin of `beside`: a panel under a rectangular tree that shares
  its time axis, with an optional time axis under the panel. The tree keeps its size and margins,
  every node stays on its pixel, and the composite is drawn as vectors, so it needs no cairosvg (#7).
- `trees.node_points({node: value})` — the panel for it: one point per named node, internal nodes
  included, at the node's time. Options: per-node `colors`, `line=True` to join the points, a zero
  line when the range crosses 0, and round y ticks. A name not in the tree raises an error.
- `Figure.geometry()` now also gives `nodes` (every node's pixel position, internal ones included)
  and `px(x)`, the time-to-pixel mapping, so other panels can line up with the x axis.
- `Style` gains `margin_left`, `margin_right`, `margin_top` and `margin_bottom`. Each defaults to
  `margin`, so existing figures render byte for byte as before. The tree guides use the side they sit on.

## [0.2.17] - 2026-08-23

### Added
- `trees.color_history` works on the radial layout. Each branch is painted as its state mosaic,
  running outward along the node's angle, and the arc at a speciation takes the branch's end state.
- `trees.branch_events` works on the radial layout. Point marks and transfer arrows are placed in
  polar coordinates, and each glyph turns to follow its branch.
- `trees.ring` gains `edge` and `edge_width`, which outline every sector in one colour, so a white
  sector still shows as a cell.
- `trees.legend` gains `entries`, an explicit `{label: colour}` list, for a figure whose scale slot
  holds a continuous ring. It also gains `dy`, to sit below a `colorbar` in the same corner.
- `trees.legend` and `trees.colorbar` gain `inset`, which anchors the corner at a fixed distance
  instead of the figure margin. A figure with a large margin keeps its guides in the corner, clear
  of its rings.
- `CITATION.cff`, the citation metadata for the Zenodo DOI.

### Fixed
- On a radial tree, `branch_events` marks landed one stem length too far out. The radial layout
  drops the root stem, and the event distances now drop it too.
- On a radial tree, a state-switch triangle puts its tip at the event's time, with its body over the
  state it leaves, and has a thin dark outline. Before, its wide base read as the point.

## [0.2.16] - 2026-08-22

### Added
- `trees.ring(values)` — an outer ring of coloured arcs around a radial tree, one contiguous segment
  per tip merging same-coloured neighbours into a band; `radius_pct` sets where the ring sits.
- `trees.tip_track(..., shape=…)` — the tip chip can now be any marker glyph (`"circle"`, `"square"`,
  …), not only a square.
- `trees.rubberband(values)` — a smooth, round population band wrapped around a radial tree, coloured
  by `values` like `color_branches`. It traces the tree's outline from the root, holds it a constant
  distance out from the branches (so the margin is even all the way around), rounds it by smoothing
  over angle, and clamps it so it never crosses a branch. `gap` sets that constant distance, `smooth`
  the roundness (fraction of the turn averaged over), `width` the band thickness.

## [0.1.4] - 2026-08-03

### Added
- `genomes.grid(matrix)` — a `Matrix` as a standalone figure, rows x columns of coloured cells with
  no tree beside it. `heatmap` is a *panel*: `beside()` hands it one pixel row per tree tip, so it
  only exists next to a tree, and a phyletic profile of a few hundred families sorted by prevalence
  is a companion to nothing. `palette` colours values as categories (presence/absence), and
  `borders` draws the line between cells — a colour, `False`, or by default by size, since at a few
  hundred rows a hairline is a tenth of a cell and a solid block reads as criss-crossed.

## [0.1.3] - 2026-08-02

### Added
- `genomes.tracks()` — genomes as a panel beside a tree, with homologues joined by ribbons.
- Circular genomes: chunky strand-arrows, a `gene_style` option (`"wedge"` restores the classic thin
  ring), and a curved highlight band.
- `colorbar` gains `loc` (`"top-left"` default, or `"bottom-left"`) and `labels=` for the two ends.
- `color_branches` gains `limits=`, so several figures can share one colour scale.
- Colour maps: `magma`, `cividis`, and a diverging `coolwarm`.

### Changed
- `read_alignment` accepts genome-qualified FASTA headers.
- The arrowhead flare is capped on a gene-dense ring.

### Fixed
- The README's figure and LICENSE link now use absolute GitHub URLs. PyPI does not rewrite relative
  paths, so on the project page the figure rendered as a broken image and the link 404'd.

## [0.1.2] - 2026-07-27

### Added
- `genomes.bars()`, a bar panel; `trees.time_axis` gains a bold toggle.

## [0.1.1] - 2026-07-27

### Added
- Automated PyPI releases via trusted publishing.

### Changed
- `branch_events` scales the transfer arrow with `size`.

## [0.1.0] - 2026-07-27

### Added
- `phyl`, a one-shot command-line viewer: `phyl tree.nwk` renders a Newick tree to a temporary PDF
  and opens it; `-o FILE` saves to SVG/PDF/PNG instead. Flags for layout (`--radial`/`--unrooted`),
  labels (`--no-labels`/`--node-labels`), and `--no-stem`.
- The `genomes` domain (merged in from Genustrator): genome maps, synteny, and `states()` /
  `heatmap` / `alignment` panels placed beside a tree.
- Tree layers `branch_events`, `color_history`, `color_lanes`, `note`, `legend`, `time_marker`, and
  dashed branches for extinct lineages.

### Changed
- **Full rewrite** into a small, composable tree plotter. Read a tree with `loads`/`read`, build a
  figure with the layer grammar (`plot(tree) + color_branches(...) + tip_labels() + colorbar() + …`),
  and save to SVG/PDF/PNG. Own Newick parser (differential-tested against ete3), stem-aware layouts
  (`rectangular`, `radial`, `unrooted`), and a matplotlib-free viridis/palette colour module.
- `drawsvg` is now the only runtime dependency (cairosvg stays optional, for PDF/PNG).

### Removed
- The ete3-based `TreeStyle` / `VerticalTreeDrawer` API, the `phylustrator.zombi2` reconciliation
  bridge, and the `ete3` and `pandas` dependencies. ZOMBI2 support will return on the new core.

## [0.0.1] - 2025-01-01

### Added
- Initial release of Phylustrator
- VerticalTreeDrawer class for drawing phylogenetic trees in vertical orientation
- RadialTreeDrawer class for drawing phylogenetic trees in radial orientation
- TreeStyle dataclass for customizable tree visualization
- SVG export functionality
- PNG export functionality
- PDF export functionality
- Trait mapping visualization via heatmaps
- Categorical trait visualization support
- Continuous trait visualization support
- Horizontal Gene Transfer (HGT) visualization
- Clade highlighting and styling
- Leaf shape customization
- Node shape customization
- Time axes support
- Scale bars for distance reference
- Legends for trait and style information
- Jupyter notebook integration and display support
