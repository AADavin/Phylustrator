# Quick Start Guide

This guide will walk you through creating your first phylogenetic tree visualizations with Phylustrator.

## Basic Vertical Tree

Let's start with a simple vertical tree:

```python
import ete3
import phylustrator as ph

# 1. Load or create a tree
t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)

# 2. Define the style
style = ph.TreeStyle(
    width=600,
    height=600,
    branch_stroke_width=2,
    branch_color="black"
)

# 3. Create a drawer and render
drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()

# 4. Save the result
drawer.save_svg("tree.svg")
drawer.save_png("tree.png", dpi=300)  # Requires Cairo
```

## Basic Radial Tree

To render the same tree in a radial (circular) layout:

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)

style = ph.TreeStyle(
    width=600,
    height=600,
    radius=250,
    rotation=-90
)

drawer = ph.RadialTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()
drawer.save_png("radial_tree.png", dpi=300)
```

## Customizing Branch Colors

Color branches based on phylogenetic relationships:

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)

# Create a color mapping
node_colors = {}
for node in t.traverse():
    if node.is_leaf:
        node_colors[node] = "blue"
    else:
        node_colors[node] = "green"

style = ph.TreeStyle(width=600, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw(branch2color=node_colors)
drawer.add_leaf_names()
drawer.save_svg("colored_tree.svg")
```

## Adding Leaf Shapes

Mark specific leaves with shapes:

```python
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="red",
    r=8,
    stroke="black",
    stroke_width=1,
    offset=30
)

# Different shapes for other leaves
drawer.add_leaf_shapes(
    leaves=["C"],
    shape="triangle",
    fill="orange",
    r=6,
    offset=30
)
```

## Highlighting Clades

Draw attention to specific clades:

```python
# Highlight the clade containing A and B
target = t.get_common_ancestor("A", "B")
drawer.highlight_clade(target, color="yellow", opacity=0.3)

# Highlight specific branches
drawer.highlight_branch(target, color="red", stroke_width=5)
```

## Adding Heatmaps

Display metadata as color-coded columns:

```python
import random

# Create metadata for each leaf
gene_expression = {
    leaf.name: random.uniform(0, 1)
    for leaf in t.get_leaves()
}

# Add the heatmap
drawer.add_heatmap(
    gene_expression,
    width=20,
    offset=50,
    low_color="white",
    high_color="blue",
    border_color="black",
    border_width=0.5
)
```

## Adding Legends

Make your visualization self-documenting:

```python
# Categorical legend
drawer.add_categorical_legend(
    palette={"Clade A": "blue", "Clade B": "green"},
    title="Clades",
    x=-250,
    y=-250
)

# Continuous color bar
drawer.add_color_bar(
    low_color="white",
    high_color="blue",
    vmin=0,
    vmax=1,
    title="Expression",
    x=100,
    y=-250
)
```

## Loading Trees from Files

Phylustrator works with standard phylogenetic file formats via ete3:

```python
# From Newick file
t = ete3.Tree("path/to/tree.nwk", format=1)

# From Nexus file
t = ete3.Tree("path/to/tree.nex")

# From PhyloXML file
t = ete3.Tree("path/to/tree.xml")
```

## Complete Example: Publication-Quality Figure

Here's a more complex example combining several features:

```python
import ete3
import phylustrator as ph

# Load tree
t = ete3.Tree("(((A:1,B:1)AB:1,(C:1,D:1)CD:1)ABCD:1)root;", format=1)

# Style
style = ph.TreeStyle(
    width=800,
    height=600,
    branch_stroke_width=2.5,
    branch_color="black",
    leaf_r=0,
    node_r=0,
    font_size=14
)

# Create drawer
drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw base tree
drawer.draw()
drawer.add_leaf_names(offset=20)

# Add title
drawer.add_title("Species Phylogeny", font_size=20)

# Color major clades
ab_clade = t.get_common_ancestor("A", "B")
cd_clade = t.get_common_ancestor("C", "D")

branch_colors = {n: "black" for n in t.traverse()}
for n in ab_clade.traverse():
    branch_colors[n] = "blue"
for n in cd_clade.traverse():
    branch_colors[n] = "red"

# Redraw with colors
drawer.draw(branch2color=branch_colors)
drawer.add_leaf_names(offset=20)

# Add legend
drawer.add_categorical_legend(
    palette={"Clade AB": "blue", "Clade CD": "red"},
    x=-300,
    y=-200
)

# Export
drawer.save_png("publication_tree.png", dpi=300)
```

## Next Steps

- Explore the [User Guide](../guide/vertical.md) for more features and examples
- Learn about [Styling Options](../guide/styling.md)
- Check the [API Reference](../api/treestyle.md) for complete parameter documentation
- Browse the [Gallery](../gallery.md) for inspiration

## Common Patterns

### Adjusting Tree Layout

```python
style = ph.TreeStyle(
    width=1000,           # Canvas width
    height=800,           # Canvas height
    margin=50,            # Space around tree
    radius=300,           # For radial trees
    rotation=-90,         # Rotation offset in degrees
)
```

### Font and Text

```python
style = ph.TreeStyle(
    font_family="Arial",
    font_size=12
)

# Add custom text
drawer.add_text("Custom label", x=100, y=100, font_size=14)
drawer.add_title("My Tree", position="top", font_size=18)
```

### Export Formats

```python
# SVG (lossless, scalable)
drawer.save_svg("tree.svg")

# PNG (raster, publication-quality)
drawer.save_png("tree.png", dpi=300)

# PDF (vector, print-ready)
drawer.save_pdf("tree.pdf", dpi=300)
```

## Troubleshooting

### Tree not rendering

Make sure your tree is properly formatted:

```python
# Check that tree loads correctly
t = ete3.Tree("your_newick_string", format=1)
print(t)  # Should display tree structure
```

### Missing leaf names

Call `add_leaf_names()` after drawing:

```python
drawer.draw()
drawer.add_leaf_names()  # Don't forget this!
```

### PNG export failing

Ensure Cairo is installed:

```bash
# Test Cairo installation
python -c "import cairosvg; print('Cairo is available')"

# Install if missing
pip install phylustrator[export]
```
