# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
