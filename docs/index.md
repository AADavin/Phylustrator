# Phylustrator

Phylustrator is a Python library for rendering highly customizable phylogenetic trees. Built on top of ete3 and drawsvg, it provides a flexible and intuitive interface for creating publication-quality tree visualizations.

## Features

- **Vertical and Radial Trees**: Render phylogenetic trees in multiple orientations
- **Customizable Styling**: Control branch colors, widths, fonts, node sizes, and more
- **Trait Mapping**: Visualize categorical and continuous traits alongside your tree
- **Heatmaps**: Display multi-column metadata as color-coded heatmaps
- **HGT Visualization**: Plot horizontal gene transfer events as curved connections
- **Advanced Annotations**: Add markers, highlights, gradients, and legends to your visualizations
- **Multiple Export Formats**: Save as SVG, PNG, or PDF (PNG/PDF requires Cairo)
- **Pure Python**: Easy installation and integration into existing workflows

## Quick Example

```python
import ete3
import phylustrator as ph

# Load your tree
t = ete3.Tree("(A:1,B:1)C;", format=1)

# Define styling
style = ph.TreeStyle(width=600, height=600, branch_stroke_width=2)

# Create and customize the visualization
drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()
drawer.save_png("mytree.png", dpi=300)
```

## What's Next?

- **New to Phylustrator?** Start with the [Installation Guide](getting-started/installation.md) and [Quick Start](getting-started/quickstart.md)
- **Learn the Basics**: Explore the [User Guide](guide/vertical.md) for detailed examples
- **API Reference**: Check the [API Documentation](api/treestyle.md) for all available parameters and methods
- **Visual Examples**: Browse the [Gallery](gallery.md) for inspiration

## Getting Help

- Report issues on [GitHub](https://github.com/AADavin/Phylustrator/issues)
- Contribute to the project by reading [Contributing Guidelines](contributing.md)
- Check the [Changelog](changelog.md) for recent updates

## Installation

Install Phylustrator with pip (Python 3.8+):

```bash
pip install git+https://github.com/AADavin/Phylustrator.git
```

Optional: For PNG/PDF export, install Cairo system libraries:

```bash
# Conda (recommended)
conda install -c conda-forge cairo pango

# Ubuntu/Debian
sudo apt-get install libcairo2-dev

# macOS (Homebrew)
brew install cairo
```

For more details, see the [Installation Guide](getting-started/installation.md).
