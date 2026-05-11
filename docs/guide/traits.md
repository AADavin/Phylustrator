# Trait Mapping Guide

This guide explains how to visualize phylogenetic traits, metadata, and continuous data alongside your trees.

## Overview

Phylustrator supports multiple ways to display trait data:

- **Heatmaps**: Color-coded numeric data in columns
- **Leaf Shapes**: Categorical markers on leaves
- **Branch Shapes**: Events or changes along branches
- **Branch Colors**: Visual encoding of traits

## Heatmaps: Continuous Data

Heatmaps display continuous numerical data as color-coded columns aligned with leaves.

### Basic Heatmap

```python
import phylustrator as ph
import random

# Create data for each leaf
expression_data = {
    leaf.name: random.uniform(0, 1)
    for leaf in tree.get_leaves()
}

# Add to visualization
drawer.add_heatmap(
    expression_data,
    width=15,
    offset=50,
    low_color="white",
    high_color="blue"
)
```

### Heatmap Parameters

```python
drawer.add_heatmap(
    data,                    # dict: {leaf_name: numeric_value}
    width=15,               # Width of heatmap column in pixels
    offset=50,              # Distance from tree to heatmap start
    low_color="white",      # Color for low values
    high_color="blue",      # Color for high values
    border_color="black",   # Border stroke color (optional)
    border_width=0.5        # Border stroke width (optional)
)
```

### Multiple Heatmaps

Stack heatmaps for multi-dimensional data:

```python
# Gene expression (blue scale)
expr_data = {leaf.name: random.uniform(0, 1) for leaf in tree.get_leaves()}
drawer.add_heatmap(
    expr_data,
    width=15,
    offset=50,
    high_color="blue"
)

# Enrichment (red scale)
enrich_data = {leaf.name: random.uniform(0, 100) for leaf in tree.get_leaves()}
drawer.add_heatmap(
    enrich_data,
    width=15,
    offset=70,
    low_color="#fff5f0",
    high_color="#67000d"
)

# Conservation (green scale)
conservation = {leaf.name: random.uniform(0, 1) for leaf in tree.get_leaves()}
drawer.add_heatmap(
    conservation,
    width=15,
    offset=90,
    low_color="white",
    high_color="darkgreen"
)
```

### Color Scales for Different Data Types

Choose appropriate color scales for your data:

```python
# Expression data (white to blue)
drawer.add_heatmap(expr, high_color="blue")

# Abundance (white to red)
drawer.add_heatmap(abundance, high_color="red")

# Conservation (white to darkgreen)
drawer.add_heatmap(conservation, high_color="darkgreen")

# Divergence (blue to red)
drawer.add_heatmap(
    divergence,
    low_color="blue",
    high_color="red"
)

# Percentage (light to dark)
drawer.add_heatmap(
    percentage,
    low_color="#f7fbff",
    high_color="#08306b"
)
```

## Categorical Traits with Leaf Shapes

Represent categorical data using different shapes at leaf nodes.

### Basic Leaf Shapes

```python
# Mark specific leaves with circles
drawer.add_leaf_shapes(
    leaves=["species_A", "species_B"],
    shape="circle",
    fill="red",
    r=6,
    offset=30
)

# Different shape for another group
drawer.add_leaf_shapes(
    leaves=["species_C", "species_D"],
    shape="triangle",
    fill="blue",
    r=5,
    offset=30
)
```

### Shape Options

Available shapes:

```python
# Circle: Simple, neutral
shape="circle"

# Triangle: Point upward
shape="triangle"

# Square: Geometric, orderly
shape="square"
```

### Multi-Trait Representation

Display multiple categorical traits:

```python
# Trait 1: Habitat
terrestrial = ["A", "B", "C"]
aquatic = ["D", "E"]

drawer.add_leaf_shapes(
    leaves=terrestrial,
    shape="circle",
    fill="brown",
    r=5,
    offset=30
)

drawer.add_leaf_shapes(
    leaves=aquatic,
    shape="circle",
    fill="blue",
    r=5,
    offset=30,
    stroke="darkblue",
    stroke_width=2
)

# Trait 2: Lifestyle (multiple offset levels)
parasites = ["A", "D"]
free_living = ["B", "C", "E"]

drawer.add_leaf_shapes(
    leaves=parasites,
    shape="triangle",
    fill="red",
    r=4,
    offset=50
)

drawer.add_leaf_shapes(
    leaves=free_living,
    shape="square",
    fill="green",
    r=4,
    offset=50
)
```

### Building Shape Mapping Programmatically

```python
# Create mapping from data
trait_mapping = {
    "habitat": {"terrestrial": "brown", "aquatic": "blue"},
    "lifestyle": {"parasitic": "red", "free-living": "green"}
}

# Apply shapes
for habitat, color in trait_mapping["habitat"].items():
    leaves = [l.name for l in tree.get_leaves() if l.habitat == habitat]
    drawer.add_leaf_shapes(
        leaves=leaves,
        shape="circle",
        fill=color,
        r=5,
        offset=30
    )
```

## Branch Events and Shapes

Mark events along branches (e.g., gene acquisitions, duplications, losses).

### Basic Branch Events

```python
events = [
    {
        "branch": "leaf_name",
        "where": 0.5,              # Position 0.0-1.0 along branch
        "shape": "circle",
        "fill": "red",
        "r": 5
    },
    {
        "branch": "another_leaf",
        "where": 0.3,
        "shape": "square",
        "fill": "orange",
        "r": 4
    }
]

drawer.add_branch_shapes(events)
```

### Multiple Events on Same Branch

```python
# Gene transfer events along a single branch
gene_transfer_events = [
    {"branch": "species_A", "where": 0.2, "shape": "circle", "fill": "purple", "r": 4},
    {"branch": "species_A", "where": 0.5, "shape": "circle", "fill": "purple", "r": 4},
    {"branch": "species_A", "where": 0.8, "shape": "circle", "fill": "purple", "r": 4},
]

drawer.add_branch_shapes(gene_transfer_events)
```

## Branch Colors by Trait

Color branches according to trait values:

```python
# Map nodes to colors based on trait
trait_colors = {}
for node in tree.traverse():
    if node.clade_size < 5:
        trait_colors[node] = "blue"
    elif node.clade_size < 10:
        trait_colors[node] = "orange"
    else:
        trait_colors[node] = "red"

drawer.draw(branch2color=trait_colors)
```

### Continuous Trait to Color

```python
import phylustrator as ph

# Map continuous trait values to color scale
trait_values = {node: float(node.dist) for node in tree.traverse()}
min_val = min(trait_values.values())
max_val = max(trait_values.values())

trait_colors = {}
for node, value in trait_values.items():
    t = (value - min_val) / (max_val - min_val)
    color = ph.utils.lerp_color("blue", "red", t)
    trait_colors[node] = color

drawer.draw(branch2color=trait_colors)
```

## Complete Example: Trait Visualization

```python
import ete3
import phylustrator as ph
import random

# Load tree
t = ete3.Tree(
    "(((A:1,B:0.5)AB:1,(C:0.8,D:0.8)CD:1)ABCD:1)root;",
    format=1
)

# Define traits for each species
traits = {
    "A": {"habitat": "terrestrial", "size": "large", "expr": 0.8},
    "B": {"habitat": "aquatic", "size": "small", "expr": 0.3},
    "C": {"habitat": "terrestrial", "size": "medium", "expr": 0.6},
    "D": {"habitat": "aquatic", "size": "large", "expr": 0.9},
}

# Create style
style = ph.TreeStyle(width=800, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw base tree
drawer.draw()
drawer.add_leaf_names(offset=25)

# 1. Add categorical trait as leaf shapes (habitat)
terrestrial = [name for name, trait in traits.items() if trait["habitat"] == "terrestrial"]
aquatic = [name for name, trait in traits.items() if trait["habitat"] == "aquatic"]

drawer.add_leaf_shapes(
    leaves=terrestrial,
    shape="circle",
    fill="brown",
    r=6,
    offset=40
)

drawer.add_leaf_shapes(
    leaves=aquatic,
    shape="circle",
    fill="blue",
    r=6,
    offset=40,
    stroke="darkblue",
    stroke_width=2
)

# 2. Add continuous trait as heatmap (expression)
expr_data = {name: trait["expr"] for name, trait in traits.items()}
drawer.add_heatmap(
    expr_data,
    width=20,
    offset=55,
    low_color="white",
    high_color="red",
    border_color="black"
)

# 3. Add size information as second heatmap
size_map = {"small": 0.3, "medium": 0.6, "large": 1.0}
size_data = {
    name: size_map[trait["size"]]
    for name, trait in traits.items()
}
drawer.add_heatmap(
    size_data,
    width=20,
    offset=80,
    low_color="white",
    high_color="green"
)

# Add legend
drawer.add_categorical_legend(
    palette={"Terrestrial": "brown", "Aquatic": "blue"},
    title="Habitat",
    x=-300,
    y=-200
)

drawer.add_color_bar(
    low_color="white",
    high_color="red",
    vmin=0,
    vmax=1,
    title="Expression",
    x=-100,
    y=-200
)

drawer.add_color_bar(
    low_color="white",
    high_color="green",
    vmin=0,
    vmax=1,
    title="Size",
    x=150,
    y=-200
)

# Save
drawer.save_png("trait_visualization.png", dpi=300)
```

## Trait Data Import

Load trait data from external sources:

### From Dictionary

```python
traits = {
    "species_A": 0.75,
    "species_B": 0.32,
    "species_C": 0.89,
}
drawer.add_heatmap(traits, width=15, offset=50, high_color="blue")
```

### From DataFrame

```python
import pandas as pd

# Read from CSV
df = pd.read_csv("traits.csv", index_col="species")

# Convert to dictionary
for column in df.columns:
    data_dict = df[column].to_dict()
    drawer.add_heatmap(
        data_dict,
        width=15,
        offset=50 + list(df.columns).index(column) * 20,
        high_color="blue"
    )
```

### From Newick Attributes

```python
# If your Newick tree has numeric node attributes
trait_values = {}
for leaf in tree.get_leaves():
    if hasattr(leaf, "dist"):
        trait_values[leaf.name] = float(leaf.dist)

drawer.add_heatmap(trait_values, width=15, offset=50, high_color="blue")
```

## Tips and Best Practices

1. **Align heatmaps carefully**: Use consistent offsets and widths
2. **Use meaningful colors**: Blue for expression, red for enrichment, green for conservation
3. **Label clearly**: Add legends for all categorical traits
4. **Limit heatmaps**: 3-4 columns maximum for readability
5. **Test color schemes**: Ensure they're colorblind-friendly
6. **Separate concerns**: Use shapes for categories, heatmaps for continuous data
7. **Document data source**: Include in figure caption where data comes from
