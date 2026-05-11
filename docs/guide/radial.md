# Radial Trees Guide

This guide covers creating and customizing radial (circular) phylogenetic trees with Phylustrator.

## Basic Radial Tree

A radial tree displays the root at the center with leaves radiating outward in a circular pattern:

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1,C:1,D:1)E;", format=1)

style = ph.TreeStyle(
    width=700,
    height=700,
    radius=300,
    rotation=-90      # Start from top
)

drawer = ph.RadialTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()
drawer.save_svg("radial_tree.svg")
```

## Radial Layout Parameters

### Radius and Angular Span

Control the size and coverage of the radial tree:

```python
style = ph.TreeStyle(
    width=800,
    height=800,
    radius=350,       # Distance from center to leaves
    degrees=360,      # Full circle (use <360 for partial trees)
    rotation=-90      # Starting angle in degrees
)
```

### Partial Circle Trees

Display only a portion of the circle:

```python
style = ph.TreeStyle(
    width=600,
    height=600,
    radius=250,
    degrees=180,      # Semicircle
    rotation=0        # Start from right
)

drawer = ph.RadialTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()
```

### Rotation Control

Start the tree at different angles:

```python
# Top (12 o'clock)
rotation=-90

# Right (3 o'clock)
rotation=0

# Bottom (6 o'clock)
rotation=90

# Left (9 o'clock)
rotation=180
```

## Customizing Branches

### Branch Colors

Color radial tree branches by clade:

```python
# Map nodes to colors
colors = {}
for node in t.traverse():
    if node.is_leaf:
        colors[node] = "blue"
    else:
        colors[node] = "green"

drawer.draw(branch2color=colors)
drawer.add_leaf_names()
```

### Highlighting Branches

Emphasize important branches:

```python
target = t.get_common_ancestor("A", "B")
drawer.highlight_branch(
    target,
    color="red",
    stroke_width=4
)

drawer.draw()
drawer.add_leaf_names()
```

### Gradient Branches

Add color gradients along branches:

```python
target = t.get_common_ancestor("C", "D")
drawer.gradient_branch(
    target,
    colors=("purple", "orange"),
    stroke_width=3
)

drawer.draw()
drawer.add_leaf_names()
```

## Clade Highlighting

### Background Highlighting

Highlight clades with colored background sectors:

```python
ab_clade = t.get_common_ancestor("A", "B")
drawer.highlight_clade(
    ab_clade,
    color="yellow",
    opacity=0.2
)

drawer.draw()
drawer.add_leaf_names()
```

### Multiple Clade Highlights

Distinguish multiple groups:

```python
clade1 = t.get_common_ancestor("A", "B")
clade2 = t.get_common_ancestor("C", "D")

drawer.highlight_clade(clade1, color="blue", opacity=0.15)
drawer.highlight_clade(clade2, color="orange", opacity=0.15)

drawer.draw()
drawer.add_leaf_names()
```

## Annotations

### Leaf Names

Display leaf labels radiating outward:

```python
drawer.add_leaf_names()

# With custom offset
drawer.add_leaf_names(offset=50)
```

### Leaf Shapes

Mark specific leaves with geometric shapes:

```python
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="red",
    r=6,
    stroke="black",
    stroke_width=1,
    offset=40
)

drawer.add_leaf_shapes(
    leaves=["C"],
    shape="triangle",
    fill="blue",
    r=5,
    offset=40
)
```

### Branch Events

Mark specific positions along radial branches:

```python
events = [
    {"branch": "A", "where": 0.5, "shape": "circle", "fill": "green", "r": 4},
    {"branch": "B", "where": 0.7, "shape": "square", "fill": "purple", "r": 3},
]

drawer.add_branch_shapes(events)
```

## Heatmaps in Radial Trees

### Radial Heatmaps

Display data columns around the circle:

```python
import random

# Create data
gene_expr = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}

# Add heatmap extending radially outward
drawer.add_heatmap(
    gene_expr,
    width=20,
    offset=350,          # Start at radius edge
    low_color="white",
    high_color="blue"
)
```

### Multiple Radial Heatmaps

Stack multiple data columns:

```python
expr_data = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
enrich_data = {leaf.name: random.uniform(0, 100) for leaf in t.get_leaves()}

drawer.add_heatmap(expr_data, width=15, offset=320, high_color="blue")
drawer.add_heatmap(enrich_data, width=15, offset=340, low_color="#fff5f0", high_color="#67000d")
```

## Horizontal Gene Transfer

### Simple Transfers

Plot curved connections across the radial tree:

```python
transfers = [
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
]

drawer.plot_transfers(transfers, opacity=0.5)
```

### Styled Transfers

Customize transfer visualization:

```python
transfers = [
    {"from": "A", "to": "B", "freq": 1.0},
    {"from": "C", "to": "D", "freq": 0.7},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",           # Cubic curves
    stroke_width=2,
    opacity=0.6,
    gradient_colors=("purple", "lime")
)
```

## Legends

### Categorical Legend

Add a legend for categorical data:

```python
drawer.add_categorical_legend(
    palette={"Group A": "blue", "Group B": "red", "Group C": "green"},
    title="Clades",
    x=-250,
    y=-250,
    font_size=12
)
```

### Color Bar

Add a continuous scale legend:

```python
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

## Complete Example

```python
import ete3
import phylustrator as ph
import random

# Load tree
t = ete3.Tree(
    "((A:1,B:0.8)AB:1.2,(C:0.9,D:0.7,E:0.6)CDE:1.1)root;",
    format=1
)

# Create radial style
style = ph.TreeStyle(
    width=900,
    height=900,
    radius=350,
    degrees=360,
    rotation=-90,
    branch_stroke_width=2.5,
    font_size=13
)

drawer = ph.RadialTreeDrawer(t, style=style)

# Draw base tree
drawer.draw()

# Color major clades
ab_clade = t.get_common_ancestor("A", "B")
cde_clade = t.get_common_ancestor("C", "D")

colors = {n: "gray" for n in t.traverse()}
for n in ab_clade.traverse():
    colors[n] = "steelblue"
for n in cde_clade.traverse():
    colors[n] = "coral"

# Redraw with colors
drawer.draw(branch2color=colors)

# Add leaf names
drawer.add_leaf_names(offset=60)

# Highlight clades
drawer.highlight_clade(ab_clade, color="steelblue", opacity=0.1)
drawer.highlight_clade(cde_clade, color="coral", opacity=0.1)

# Add leaf markers
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="white",
    r=5,
    stroke="steelblue",
    stroke_width=2,
    offset=75
)

drawer.add_leaf_shapes(
    leaves=["C", "D", "E"],
    shape="triangle",
    fill="white",
    r=4,
    stroke="coral",
    stroke_width=2,
    offset=75
)

# Add heatmaps
expr_data = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(
    expr_data,
    width=20,
    offset=380,
    low_color="white",
    high_color="darkblue"
)

# Add HGT visualization
transfers = [
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
]
drawer.plot_transfers(transfers, opacity=0.4, stroke_width=1.5)

# Add legend
drawer.add_categorical_legend(
    palette={"Clade AB": "steelblue", "Clade CDE": "coral"},
    title="Major Groups",
    x=-350,
    y=-350,
    font_size=11
)

# Add title
drawer.add_title("Radial Phylogenetic Tree", font_size=18)

# Export
drawer.save_png("radial_example.png", dpi=300)
```

## Tips and Best Practices

1. **Use appropriate degrees** for your data: 360 for full circles, 180 for semicircles
2. **Adjust radius** based on your tree size and desired spacing
3. **Test different rotations** to find the best orientation for your data
4. **Use colors to highlight** major phylogenetic groups
5. **Place legends outside** the radial tree to avoid overlapping
6. **For dense trees**, increase canvas size and radius for better readability
7. **Combine with heatmaps** to show trait evolution across the phylogeny

## Comparing Vertical and Radial Trees

| Aspect | Vertical | Radial |
|--------|----------|--------|
| Best for | Linear relationships, time series | Large trees, all-directions display |
| Space efficiency | Good for tall trees | Better for balanced trees |
| Readability | Clear branch ordering | Good for symmetric trees |
| Scalability | Works well for deep trees | Better for wide trees |
