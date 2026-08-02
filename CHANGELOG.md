# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
