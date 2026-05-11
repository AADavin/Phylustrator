# Vertical Trees Guide

This guide covers creating and customizing vertical phylogenetic trees with Phylustrator.

## Basic Vertical Tree

A vertical tree displays the root at the top (or left, depending on rotation) with leaves extending downward (or rightward):

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)

style = ph.TreeStyle(
    width=600,
    height=600,
    branch_stroke_width=2
)

drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()
drawer.save_svg("vertical_tree.svg")
```

## Customizing Branches

### Branch Colors

Color branches individually or by clade:

```python
# Map nodes to colors
node_colors = {}
for node in t.traverse():
    if node.is_leaf:
        node_colors[node] = "blue"
    else:
        node_colors[node] = "green"

drawer.draw(branch2color=node_colors)
```

You can also use specific branches:

```python
# Color a specific clade
clade_a = t.get_common_ancestor("A", "B")
node_colors = {n: "red" for n in clade_a.traverse()}
for n in t.traverse():
    if n not in node_colors:
        node_colors[n] = "black"

drawer.draw(branch2color=node_colors)
```

### Branch Thickness

Control stroke width through the style:

```python
style = ph.TreeStyle(
    width=600,
    height=600,
    branch_stroke_width=3.0  # Thicker branches
)
```

You can also apply gradients to individual branches:

```python
# Add gradient color transition along a branch
target = t.get_common_ancestor("A", "B")
drawer.gradient_branch(
    target,
    colors=("purple", "orange"),
    stroke_width=4
)
```

### Highlighting Branches

Draw attention to specific branches:

```python
# Highlight with thick stroke
target = t.get_common_ancestor("A", "B")
drawer.highlight_branch(
    target,
    color="red",
    stroke_width=5
)
```

## Adding Annotations

### Leaf Names

Display the names of leaves:

```python
drawer.add_leaf_names()
drawer.add_leaf_names(offset=30)  # Adjust distance from leaf
```

### Leaf Shapes and Markers

Mark specific leaves with geometric shapes:

```python
# Add circles to specific leaves
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="red",
    r=6,
    stroke="black",
    stroke_width=1,
    offset=30
)

# Add triangles to other leaves
drawer.add_leaf_shapes(
    leaves=["C"],
    shape="triangle",
    fill="orange",
    r=5,
    offset=30,
    rotation=45
)

# Add squares
drawer.add_leaf_shapes(
    leaves=["D"],
    shape="square",
    fill="blue",
    r=4,
    offset=30
)
```

Available shapes: `circle`, `square`, `triangle`

### Branch Events

Mark events along branches (e.g., gene acquisitions, speciation events):

```python
events = [
    {"branch": "A", "where": 0.3, "shape": "circle", "fill": "red", "r": 5},
    {"branch": "B", "where": 0.7, "shape": "square", "fill": "blue", "r": 4},
]
drawer.add_branch_shapes(events)
```

Where `where` is a position along the branch (0.0 = start, 1.0 = end).

## Clade Highlighting

### Background Highlighting

Highlight a clade with a shaded background box:

```python
# Highlight the clade containing A and B
target_clade = t.get_common_ancestor("A", "B")
drawer.highlight_clade(
    target_clade,
    color="yellow",
    opacity=0.3
)
```

### Multiple Highlights

Highlight different clades with different colors:

```python
clade1 = t.get_common_ancestor("A", "B")
clade2 = t.get_common_ancestor("C", "D")

drawer.highlight_clade(clade1, color="blue", opacity=0.2)
drawer.highlight_clade(clade2, color="orange", opacity=0.2)
```

## Heatmaps and Trait Visualization

### Basic Heatmap

Display numerical data as color-coded columns:

```python
import random

# Create data for each leaf
gene_expression = {
    leaf.name: random.uniform(0, 1)
    for leaf in t.get_leaves()
}

# Add heatmap
drawer.add_heatmap(
    gene_expression,
    width=15,
    offset=50,
    low_color="white",
    high_color="blue",
    border_color="black",
    border_width=0.5
)
```

### Multiple Heatmaps

Stack multiple data columns:

```python
# First column
expr_data = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(expr_data, width=15, offset=50, high_color="blue")

# Second column
enrich_data = {leaf.name: random.uniform(0, 100) for leaf in t.get_leaves()}
drawer.add_heatmap(
    enrich_data,
    width=15,
    offset=70,
    low_color="#fff5f0",
    high_color="#67000d"
)

# Third column
another_dataset = {leaf.name: random.uniform(0, 50) for leaf in t.get_leaves()}
drawer.add_heatmap(
    another_dataset,
    width=15,
    offset=90,
    low_color="white",
    high_color="green"
)
```

### Custom Color Schemes

Use any CSS color names or hex codes:

```python
drawer.add_heatmap(
    data,
    width=20,
    low_color="#f7fbff",     # Light blue
    high_color="#08306b"     # Dark blue
)
```

## Time Axis

Add a time scale to your tree:

```python
drawer.add_time_axis(
    ticks=[0, 0.5, 1.0, 1.5, 2.0],
    label="Time (millions of years)",
    y_offset=20
)
```

## Horizontal Gene Transfer (HGT) Visualization

### Simple Transfer Lines

Plot curved connections between lineages to represent transfers:

```python
transfer_data = [
    {"from": "A", "to": "B"},
    {"from": "C", "to": "D"},
]

drawer.plot_transfers(transfer_data)
```

### Styled Transfers

Customize transfer appearance:

```python
transfer_data = [
    {"from": "A", "to": "B", "freq": 1.0},
    {"from": "C", "to": "D", "freq": 0.5},
]

drawer.plot_transfers(
    transfer_data,
    curve_type="C",           # Cubic curves
    stroke_width=2,
    opacity=0.6,
    gradient_colors=("purple", "orange")
)
```

Available curve types: `"C"` (cubic), `"Q"` (quadratic), `"L"` (linear)

## Advanced Layouts

### Adjusting Scale and Spacing

```python
style = ph.TreeStyle(
    width=1000,
    height=800,
    margin=100,           # Space around tree
    root_stub_length=50   # Root branch length
)
```

### Tree Rotation

Rotate the entire tree after rendering:

```python
drawer.save_svg("tree.svg", rotation=90)  # 90 degrees clockwise
```

## Complete Example

```python
import ete3
import phylustrator as ph
import random

# Load tree
t = ete3.Tree(
    "(((A:1,B:0.5)AB:1,(C:0.8,D:0.8)CD:1)ABCD:1)root;",
    format=1
)

# Style
style = ph.TreeStyle(
    width=800,
    height=600,
    branch_stroke_width=2.5,
    branch_color="black",
    margin=80,
    font_size=12
)

drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw base tree
drawer.draw()
drawer.add_leaf_names(offset=25)

# Color clades
ab_clade = t.get_common_ancestor("A", "B")
cd_clade = t.get_common_ancestor("C", "D")

colors = {n: "gray" for n in t.traverse()}
for n in ab_clade.traverse():
    colors[n] = "blue"
for n in cd_clade.traverse():
    colors[n] = "red"

drawer.draw(branch2color=colors)
drawer.add_leaf_names(offset=25)

# Highlight clades
drawer.highlight_clade(ab_clade, color="blue", opacity=0.1)
drawer.highlight_clade(cd_clade, color="red", opacity=0.1)

# Add leaf markers
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="lightblue",
    r=5,
    offset=40
)

# Add heatmaps
data1 = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
data2 = {leaf.name: random.uniform(0, 100) for leaf in t.get_leaves()}

drawer.add_heatmap(data1, width=15, offset=55, high_color="blue")
drawer.add_heatmap(data2, width=15, offset=75, high_color="red")

# Add HGT
drawer.plot_transfers([{"from": "A", "to": "C"}], opacity=0.5)

# Add title and legends
drawer.add_title("Phylogenetic Relationship", font_size=16)
drawer.add_categorical_legend(
    palette={"Clade AB": "blue", "Clade CD": "red"},
    x=-350,
    y=-220
)

# Export
drawer.save_png("vertical_example.png", dpi=300)
```

## Tips and Best Practices

1. **Always call draw() first** before adding annotations
2. **Use meaningful colors** to highlight important features
3. **Keep heatmaps aligned** by using consistent offset values
4. **Test export quality** with save_png() at high DPI (300+) for publications
5. **Use leaf shapes sparingly** to avoid cluttering the visualization
