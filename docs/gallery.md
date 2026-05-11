# Gallery

This gallery showcases Phylustrator's capabilities with code examples for each visualization type.

## Basic Vertical Tree

A simple vertical phylogenetic tree with leaf names.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:0.5)AB:1,(C:0.8,D:1.2)CD:1)root;", format=1)

style = ph.TreeStyle(
    width=600,
    height=500,
    branch_stroke_width=2
)

drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names(offset=25)
drawer.save_png("basic_vertical.png", dpi=300)
```

**Features:**
- Clean, minimalist design
- Proportional branch lengths
- Clear leaf labels

---

## Basic Radial Tree

The same tree displayed in a circular radial layout.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:0.5)AB:1,(C:0.8,D:1.2)CD:1)root;", format=1)

style = ph.TreeStyle(
    width=700,
    height=700,
    radius=300,
    rotation=-90
)

drawer = ph.RadialTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names(offset=50)
drawer.save_png("basic_radial.png", dpi=300)
```

**Features:**
- Circular layout
- All directions equally emphasized
- Good for balanced trees

---

## Branch Coloring

Color branches to distinguish major clades.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

# Create color mapping
colors = {}
ab_clade = t.get_common_ancestor("A", "B")
cd_clade = t.get_common_ancestor("C", "D")

for node in t.traverse():
    if node in ab_clade.traverse():
        colors[node] = "steelblue"
    elif node in cd_clade.traverse():
        colors[node] = "coral"
    else:
        colors[node] = "gray"

drawer = ph.VerticalTreeDrawer(t)
drawer.draw(branch2color=colors)
drawer.add_leaf_names(offset=25)
drawer.save_png("branch_coloring.png", dpi=300)
```

**Features:**
- Multiple color schemes
- Clade-based coloring
- Visual distinction of lineages

---

## Clade Highlighting

Emphasize specific clades with background highlighting.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

style = ph.TreeStyle(width=700, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw tree
drawer.draw()
drawer.add_leaf_names(offset=25)

# Highlight clades
ab = t.get_common_ancestor("A", "B")
cd = t.get_common_ancestor("C", "D")

drawer.highlight_clade(ab, color="steelblue", opacity=0.15)
drawer.highlight_clade(cd, color="coral", opacity=0.15)

drawer.add_categorical_legend(
    palette={"Clade AB": "steelblue", "Clade CD": "coral"},
    x=-300,
    y=-200
)

drawer.save_png("clade_highlighting.png", dpi=300)
```

**Features:**
- Shaded background boxes
- Customizable opacity
- Easy visual identification

---

## Trait Mapping with Heatmaps

Display continuous data (gene expression, enrichment) alongside the tree.

**Code:**
```python
import ete3
import phylustrator as ph
import random

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.add_leaf_names(offset=30)

# Expression data (0-1 scale)
expr = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(
    expr,
    width=20,
    offset=50,
    low_color="white",
    high_color="darkblue",
    border_color="black"
)

# Enrichment data (0-100 scale)
enrich = {leaf.name: random.uniform(0, 100) for leaf in t.get_leaves()}
drawer.add_heatmap(
    enrich,
    width=20,
    offset=75,
    low_color="white",
    high_color="darkred",
    border_color="black"
)

# Add color bars
drawer.add_color_bar(0, 1, "Expression", x=100, y=-200, high_color="darkblue")
drawer.add_color_bar(0, 100, "Enrichment", x=200, y=-200, high_color="darkred")

drawer.save_png("trait_mapping.png", dpi=300)
```

**Features:**
- Multiple data columns
- Color gradients
- Legend documentation

---

## Leaf Shapes for Categorical Traits

Mark leaves with different shapes to represent categories.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.add_leaf_names(offset=35)

# Habitat trait (circles for terrestrial, triangles for aquatic)
terrestrial = ["A", "C"]
aquatic = ["B", "D"]

drawer.add_leaf_shapes(
    leaves=terrestrial,
    shape="circle",
    fill="brown",
    r=6,
    stroke="darkbrown",
    stroke_width=1.5,
    offset=50
)

drawer.add_leaf_shapes(
    leaves=aquatic,
    shape="triangle",
    fill="blue",
    r=5,
    stroke="darkblue",
    stroke_width=1.5,
    offset=50
)

drawer.add_categorical_legend(
    palette={"Terrestrial": "brown", "Aquatic": "blue"},
    title="Habitat",
    x=-250,
    y=-200
)

drawer.save_png("leaf_shapes.png", dpi=300)
```

**Features:**
- Multiple shape types
- Categorical representation
- Customizable colors and sizes

---

## HGT Transfer Visualization

Show horizontal gene transfer events as curved connections.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.add_leaf_names(offset=30)

# Define HGT events
transfers = [
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
    {"from": "C", "to": "A"},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=2.5,
    opacity=0.5,
    gradient_colors=("purple", "orange")
)

drawer.add_categorical_legend(
    palette={"HGT Event": "#9966ff"},
    title="Events",
    x=-250,
    y=-200
)

drawer.save_png("hgt_transfers.png", dpi=300)
```

**Features:**
- Smooth cubic curves
- Gradient coloring
- Semi-transparent display

---

## Complex Integrated Visualization

Combine multiple features into a single publication-quality figure.

**Code:**
```python
import ete3
import phylustrator as ph
import random

t = ete3.Tree(
    "((A:1,B:0.8)AB:1.2,(C:0.9,D:1.1)CD:1)root;",
    format=1
)

# High-quality style
style = ph.TreeStyle(
    width=1000,
    height=800,
    margin=100,
    branch_stroke_width=2.5,
    font_size=12,
    font_family="Arial"
)

drawer = ph.VerticalTreeDrawer(t, style=style)

# Base tree
drawer.draw()
drawer.add_leaf_names(offset=35, font_size=13)

# Color branches
ab = t.get_common_ancestor("A", "B")
cd = t.get_common_ancestor("C", "D")
colors = {n: "gray" for n in t.traverse()}
for n in ab.traverse():
    colors[n] = "steelblue"
for n in cd.traverse():
    colors[n] = "coral"

drawer.draw(branch2color=colors)
drawer.add_leaf_names(offset=35, font_size=13)

# Highlight clades
drawer.highlight_clade(ab, color="steelblue", opacity=0.1)
drawer.highlight_clade(cd, color="coral", opacity=0.1)

# Add leaf shapes
drawer.add_leaf_shapes(
    leaves=["A", "B"],
    shape="circle",
    fill="white",
    r=5,
    stroke="steelblue",
    stroke_width=2,
    offset=50
)

drawer.add_leaf_shapes(
    leaves=["C", "D"],
    shape="square",
    fill="white",
    r=4,
    stroke="coral",
    stroke_width=2,
    offset=50
)

# Add heatmaps
expr = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(expr, width=20, offset=70, high_color="darkblue")

size = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(size, width=20, offset=95, high_color="darkgreen")

# Add HGT
transfers = [{"from": "A", "to": "C"}]
drawer.plot_transfers(transfers, stroke_width=2, opacity=0.5)

# Title and legends
drawer.add_title("Integrated Phylogenetic Analysis", font_size=16)

drawer.add_categorical_legend(
    palette={"Clade AB": "steelblue", "Clade CD": "coral"},
    title="Clades",
    x=-400,
    y=-300
)

drawer.add_color_bar(
    "white", "darkblue", 0, 1, "Expression",
    x=-100, y=-300
)

drawer.save_png("complex_integration.png", dpi=300)
```

**Features:**
- Multiple annotation types
- Professional styling
- Clear documentation

---

## Gradient Branch Coloring

Show continuous values along branches using color gradients.

**Code:**
```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.add_leaf_names(offset=25)

# Apply gradients to specific branches
ab = t.get_common_ancestor("A", "B")
cd = t.get_common_ancestor("C", "D")

drawer.gradient_branch(ab, colors=("purple", "orange"), stroke_width=4)
drawer.gradient_branch(cd, colors=("green", "red"), stroke_width=4)

drawer.save_png("gradient_branches.png", dpi=300)
```

**Features:**
- Smooth color transitions
- Visual emphasis
- Good for continuous data

---

## Large Tree Visualization

Handle and visualize larger trees with many leaves.

**Code:**
```python
import ete3
import phylustrator as ph

# Generate a larger tree
newick = "(" * 10 + "A:1" + ",B:1" + ")" * 10 + ";"
t = ete3.Tree(newick, format=1)

style = ph.TreeStyle(
    width=1200,
    height=2000,
    margin=150,
    branch_stroke_width=1.5,
    font_size=9,
    leaf_r=0,
    node_r=0
)

drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names(offset=20, font_size=9)

drawer.save_png("large_tree.png", dpi=300)
```

**Features:**
- Larger canvas
- Smaller fonts
- Optimized for readability

---

## Tips for Your Visualizations

1. **Start simple**: Create basic tree, add features incrementally
2. **Use meaningful colors**: Blue for expression, red for abundance
3. **Maintain clarity**: Don't overcrowd with annotations
4. **Test different layouts**: Vertical vs. radial
5. **Export multiple formats**: SVG for editing, PNG for presentations
6. **Document your choices**: Include style and data source in captions
7. **Consider accessibility**: Use colorblind-friendly palettes
