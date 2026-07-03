# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `phylustrator.zombi2` — read [ZOMBI2](https://github.com/AADavin/zombi2) output and draw
  gene-family reconciliations on the **time-calibrated** species tree. `load()` parses a
  `Genomes.write()` folder; `draw_reconciliation()` overlays a family's originations,
  duplications and losses as markers at their true time and transfers as time-placed arcs
  (horizontal in time). Lower-level `event_markers()` / `transfer_records()` helpers, plus a
  guide and API docs. Phylustrator does not import ZOMBI2 — it only reads the written files.

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
