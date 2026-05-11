# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added
- Initial public release of Phylustrator
- Full vertical tree drawing support
- Full radial (circular) tree drawing support
- Branch coloring with custom color mapping
- Clade highlighting with background boxes
- Branch gradient support
- Leaf shape annotations (circles, squares, triangles)
- Branch event markers
- Heatmap visualization for continuous data
- Horizontal gene transfer (HGT) visualization with curved connections
- Categorical and continuous legends
- Color bar legends for heatmaps
- Time axis visualization
- Support for multiple export formats:
  - SVG (scalable vector graphics)
  - PNG (raster, requires Cairo)
  - PDF (print-ready, requires Cairo)
- Comprehensive API documentation
- User guides for common visualization tasks
- Gallery with example code snippets
- Contributing guidelines

### Documentation
- Installation guide with platform-specific instructions
- Quick start guide with basic examples
- Comprehensive user guide for vertical trees
- Comprehensive user guide for radial trees
- Styling and customization guide
- Trait mapping guide for categorical and continuous data
- HGT visualization guide
- File format support guide (Newick, Nexus, PhyloXML)
- Complete API reference for all classes and functions
- Utility functions documentation

## [0.0.1] - Initial Release

### Added
- Core TreeStyle configuration class
- BaseDrawer abstract base class
- VerticalTreeDrawer for linear phylogenetic trees
- RadialTreeDrawer for circular phylogenetic trees
- TreeStyle dataclass with validation
- Full drawing API:
  - draw() - render tree structure
  - add_leaf_names() - add leaf labels
  - add_title() - add title text
  - add_text() - add arbitrary text
  - add_leaf_shapes() - annotate leaves with shapes
  - add_branch_shapes() - mark branch events
  - highlight_clade() - highlight clades with background
  - highlight_branch() - emphasize specific branches
  - gradient_branch() - apply color gradients to branches
  - plot_transfers() - visualize HGT events
  - add_heatmap() - display continuous data
  - add_time_axis() - add evolutionary scale
  - add_categorical_legend() - add categorical legend
  - add_color_bar() - add continuous color legend
- Export functionality:
  - save_svg() - export to SVG
  - save_png() - export to PNG (requires cairosvg)
  - save_pdf() - export to PDF (requires cairosvg)
- Utility functions:
  - to_rgb() - parse CSS colors to RGB
  - to_hex() - convert RGB to hex
  - lerp_color() - interpolate between colors
  - polar_to_cartesian() - coordinate conversion
  - add_origin_if_root_has_dist() - tree standardization
  - generate_id() - unique ID generation
- ete3 integration for phylogenetic tree handling
- drawsvg integration for rendering
- Support for Newick, Nexus, and PhyloXML formats
- Python 3.8+ support

### Known Limitations

- No interactive visualization (output only)
- Limited to single tree per visualization
- Unicode in names may have issues in some formats
- Very large trees (10,000+ leaves) may have performance issues

### Future Roadmap

Potential features for future releases:

- Interactive HTML/JavaScript output
- Animation support
- Advanced tree manipulation (tree surgery, alignment)
- Sequence alignment visualization
- Bootstrap/confidence value visualization
- Rooting and rerooting
- Tree statistics and analysis
- Performance optimizations for large trees
- Additional export formats (EPS, TIFF)
- Plugin system for custom rendering

---

## Version History

### How to Use This Changelog

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for changes that address security vulnerabilities

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for information about contributing to Phylustrator and reporting issues.

## Release Notes Archive

### Version 0.0.1 Release Notes

Welcome to Phylustrator! This initial release includes:

- Complete vertical and radial tree rendering
- Rich annotation capabilities
- Multiple export formats
- Comprehensive documentation

See above for full feature list.

**Acknowledgments:**
- Built on top of ete3 for tree handling
- Uses drawsvg for rendering
- Inspired by popular phylogenetic visualization tools

## Deprecation Policy

Features marked as deprecated will be supported for at least 2 minor version releases before removal. Users will receive clear warnings about deprecated features.

## Security

Security issues should be reported privately to the project maintainers. Please do not open public issues for security vulnerabilities.

## Getting Help

- Check the [documentation](https://aadavin.github.io/Phylustrator)
- Search existing [GitHub issues](https://github.com/AADavin/Phylustrator/issues)
- Open a new [GitHub discussion](https://github.com/AADavin/Phylustrator/discussions)

## License

Phylustrator is released under the MIT License. See LICENSE file for details.
