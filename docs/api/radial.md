# RadialTreeDrawer API Reference

The `RadialTreeDrawer` class renders phylogenetic trees in a radial (circular) layout.

## Class Definition

```python
class RadialTreeDrawer(BaseDrawer):
    """Draws phylogenetic trees in radial circular layout."""
```

## Constructor

### `__init__(tree, style=None)`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tree` | `ete3.Tree` | The phylogenetic tree to visualize |
| `style` | `TreeStyle` | Optional style configuration. Uses default if not provided |

**Raises:**

- `TypeError`: If tree is None

**Example:**

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)
drawer = ph.RadialTreeDrawer(t)

# Or with custom style
style = ph.TreeStyle(width=700, height=700, radius=300)
drawer = ph.RadialTreeDrawer(t, style=style)
```

## Methods

All methods are inherited from `BaseDrawer` or specific to radial layout. The radial drawer supports the same annotation methods as `VerticalTreeDrawer`.

### Drawing

#### `draw(branch2color=None)`

Draw the tree structure with optional branch coloring.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `branch2color` | `dict[Node, str]` | None | Map of nodes to CSS color strings |

**Returns:** None

**Example:**

```python
# Basic draw
drawer.draw()

# Color branches
colors = {node: "blue" for node in t.traverse()}
drawer.draw(branch2color=colors)
```

### Annotations

#### `add_leaf_names(offset=0, font_size=None)`

Display the names of all leaf nodes, radiating outward.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | `float` | 0 | Distance from leaf nodes in pixels |
| `font_size` | `int` | None | Font size (uses style default if None) |

**Returns:** None

**Example:**

```python
drawer.add_leaf_names()
drawer.add_leaf_names(offset=60, font_size=13)
```

#### `add_leaf_shapes(leaves, shape, fill, r, stroke=None, stroke_width=1.0, offset=0, rotation=0.0, opacity=1.0)`

Add geometric shapes to specific leaf nodes.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `leaves` | `list[str]` | Required | List of leaf names |
| `shape` | `str` | Required | Shape type: "circle", "square", "triangle" |
| `fill` | `str` | Required | CSS fill color |
| `r` | `float` | Required | Radius/half-size of shape |
| `stroke` | `str` | None | Optional stroke color |
| `stroke_width` | `float` | 1.0 | Stroke thickness |
| `offset` | `float` | 0 | Distance from leaf in pixels |
| `rotation` | `float` | 0.0 | Rotation angle in degrees |
| `opacity` | `float` | 1.0 | Fill opacity (0.0-1.0) |

**Returns:** None

**Example:**

```python
drawer.add_leaf_shapes(
    leaves=["A", "B", "C"],
    shape="circle",
    fill="red",
    r=6,
    stroke="black",
    offset=50
)
```

#### `add_title(text, font_size=24, position="top", pad=40.0, color="black", weight="bold")`

Add a title to the drawing.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | Required | Title text |
| `font_size` | `int` | 24 | Font size in pixels |
| `position` | `str` | "top" | Position: "top", "bottom", "left", "right" |
| `pad` | `float` | 40.0 | Padding from canvas edge |
| `color` | `str` | "black" | CSS color |
| `weight` | `str` | "bold" | Font weight |

**Returns:** None

**Raises:** `ValueError` if position is not valid

**Example:**

```python
drawer.add_title("Circular Phylogeny")
drawer.add_title("Species Tree", position="top", font_size=20)
```

#### `add_text(text, x, y, font_size=12, color="black", weight="normal", text_anchor="start", dominant_baseline="middle", rotation=0.0)`

Add arbitrary text at Cartesian coordinates.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | Required | Text content |
| `x` | `float` | Required | X coordinate |
| `y` | `float` | Required | Y coordinate |
| `font_size` | `int` | 12 | Font size |
| `color` | `str` | "black" | CSS color |
| `weight` | `str` | "normal" | Font weight |
| `text_anchor` | `str` | "start" | Horizontal alignment |
| `dominant_baseline` | `str` | "middle" | Vertical alignment |
| `rotation` | `float` | 0.0 | Rotation in degrees |

**Returns:** None

**Example:**

```python
drawer.add_text("Annotation", x=0, y=100, font_size=12)
```

### Highlights and Styling

#### `highlight_clade(clade, color="yellow", opacity=0.3, padding=2)`

Highlight a clade with a shaded background sector.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `clade` | `ete3.Tree` | Required | The clade node to highlight |
| `color` | `str` | "yellow" | CSS fill color |
| `opacity` | `float` | 0.3 | Fill opacity (0.0-1.0) |
| `padding` | `float` | 2 | Padding in pixels |

**Returns:** None

**Example:**

```python
clade = t.get_common_ancestor("A", "B")
drawer.highlight_clade(clade, color="steelblue", opacity=0.15)
```

#### `highlight_branch(node, color="red", stroke_width=3)`

Highlight a branch with a thick colored stroke.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node` | `ete3.Tree` | Required | The branch node |
| `color` | `str` | "red" | CSS stroke color |
| `stroke_width` | `float` | 3 | Stroke thickness |

**Returns:** None

**Example:**

```python
branch = t.get_common_ancestor("A", "B")
drawer.highlight_branch(branch, color="coral", stroke_width=3)
```

#### `gradient_branch(node, colors, stroke_width=2)`

Apply a color gradient along a branch.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node` | `ete3.Tree` | Required | The branch node |
| `colors` | `tuple[str, str]` | Required | (start_color, end_color) |
| `stroke_width` | `float` | 2 | Stroke thickness |

**Returns:** None

**Example:**

```python
branch = t.get_common_ancestor("A", "B")
drawer.gradient_branch(branch, colors=("steelblue", "coral"), stroke_width=2.5)
```

### Events and Transfers

#### `add_branch_shapes(events)`

Mark events at specific positions along branches.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `events` | `list[dict]` | List of event dictionaries |

**Event Dictionary Format:**

```python
{
    "branch": "leaf_name",      # Branch (leaf name it terminates at)
    "where": 0.5,               # Position 0.0-1.0 along branch
    "shape": "circle",          # "circle", "square", "triangle"
    "fill": "red",              # CSS fill color
    "r": 5,                     # Radius
}
```

**Returns:** None

**Example:**

```python
events = [
    {"branch": "A", "where": 0.3, "shape": "circle", "fill": "red", "r": 4},
    {"branch": "B", "where": 0.7, "shape": "triangle", "fill": "blue", "r": 3},
]
drawer.add_branch_shapes(events)
```

#### `plot_transfers(transfer_data, curve_type="C", stroke_width=2, opacity=0.6, gradient_colors=None)`

Visualize HGT events as curved connections across the radial tree.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transfer_data` | `list[dict]` | Required | List of transfer dicts |
| `curve_type` | `str` | "C" | Curve type: "C" (cubic), "Q" (quadratic), "L" (linear) |
| `stroke_width` | `float` | 2 | Line thickness |
| `opacity` | `float` | 0.6 | Transparency (0.0-1.0) |
| `gradient_colors` | `tuple[str, str]` | None | (start_color, end_color) |

**Transfer Dictionary Format:**

```python
{
    "from": "source_leaf",
    "to": "target_leaf",
    "freq": 1.0  # Optional
}
```

**Returns:** None

**Example:**

```python
transfers = [
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=2,
    opacity=0.4,
    gradient_colors=("steelblue", "coral")
)
```

### Heatmaps

#### `add_heatmap(data, width=15, offset=50, low_color="white", high_color="red", border_color=None, border_width=0.5)`

Display continuous data as a color-coded radial column.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `dict[str, float]` | Required | Mapping of leaf names to values |
| `width` | `float` | 15 | Column width in pixels |
| `offset` | `float` | 50 | Distance from center (radius + offset) |
| `low_color` | `str` | "white" | CSS color for minimum values |
| `high_color` | `str` | "red" | CSS color for maximum values |
| `border_color` | `str` | None | Optional border color |
| `border_width` | `float` | 0.5 | Border thickness |

**Returns:** None

**Example:**

```python
import random

expr_data = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}

drawer.add_heatmap(
    expr_data,
    width=20,
    offset=380,
    low_color="white",
    high_color="darkblue",
    border_color="black"
)
```

### Legends

#### `add_categorical_legend(palette, title="Legend", x=None, y=None, font_size=14, r=6.0)`

Add a categorical legend with colored circles and labels.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `palette` | `dict[str, str]` | Required | Mapping of label to color |
| `title` | `str` | "Legend" | Legend title |
| `x` | `float` | None | Top-left X coordinate (auto if None) |
| `y` | `float` | None | Top-left Y coordinate (auto if None) |
| `font_size` | `int` | 14 | Text size |
| `r` | `float` | 6.0 | Marker radius |

**Returns:** None

**Example:**

```python
drawer.add_categorical_legend(
    palette={"Clade A": "steelblue", "Clade B": "coral"},
    title="Groups",
    x=-350,
    y=-350
)
```

#### `add_color_bar(low_color, high_color, vmin, vmax, title="", x=None, y=None, width=100.0, height=15.0, font_size=12)`

Add a continuous gradient color bar legend.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `low_color` | `str` | Required | Color for minimum value |
| `high_color` | `str` | Required | Color for maximum value |
| `vmin` | `float` | Required | Minimum value label |
| `vmax` | `float` | Required | Maximum value label |
| `title` | `str` | "" | Bar title |
| `x` | `float` | None | Top-left X (auto if None) |
| `y` | `float` | None | Top-left Y (auto if None) |
| `width` | `float` | 100.0 | Bar width |
| `height` | `float` | 15.0 | Bar height |
| `font_size` | `int` | 12 | Label font size |

**Returns:** None

**Example:**

```python
drawer.add_color_bar(
    low_color="white",
    high_color="darkblue",
    vmin=0,
    vmax=1,
    title="Gene Expression",
    x=-300,
    y=-300
)
```

### Export

#### `save_svg(outpath, rotation=0.0)`

Export the drawing to SVG format.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outpath` | `str` or `Path` | Required | Output file path |
| `rotation` | `float` | 0.0 | Global rotation in degrees |

**Returns:** None

**Example:**

```python
drawer.save_svg("radial_tree.svg")
```

#### `save_png(outpath, dpi=300, scale=None, rotation=0.0)`

Export the drawing to PNG format.

Requires `cairosvg` library.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outpath` | `str` or `Path` | Required | Output file path |
| `dpi` | `int` | 300 | Resolution in dots per inch |
| `scale` | `float` | None | Scale factor (computed from dpi if None) |
| `rotation` | `float` | 0.0 | Global rotation in degrees |

**Returns:** None

**Raises:** `ImportError` if cairosvg is not installed

**Example:**

```python
drawer.save_png("radial_tree.png", dpi=300)
```

## Style Parameters for Radial Trees

When creating a style for radial trees, focus on these parameters:

```python
style = ph.TreeStyle(
    width=800,           # Canvas width (should equal height for circles)
    height=800,          # Canvas height
    radius=300,          # Distance from center to leaves
    degrees=360,         # Full circle (360) or partial (e.g., 180)
    rotation=-90,        # Starting angle: -90 (top), 0 (right), 90 (bottom)
    margin=50,           # Space around tree
    branch_stroke_width=2,
    font_size=12
)
```

## Complete Example

```python
import ete3
import phylustrator as ph

# Load tree
t = ete3.Tree(
    "((A:1,B:0.8)AB:1.2,(C:0.9,D:0.7,E:0.6)CDE:1.1)root;",
    format=1
)

# Create radial style
style = ph.TreeStyle(
    width=800,
    height=800,
    radius=300,
    degrees=360,
    rotation=-90,
    branch_stroke_width=2,
    font_size=12
)

drawer = ph.RadialTreeDrawer(t, style=style)

# Draw and annotate
drawer.draw()
drawer.add_leaf_names(offset=50)

# Highlight clades
ab = t.get_common_ancestor("A", "B")
cde = t.get_common_ancestor("C", "D")
drawer.highlight_clade(ab, color="blue", opacity=0.1)
drawer.highlight_clade(cde, color="orange", opacity=0.1)

# Add heatmap
import random
expr = {leaf.name: random.uniform(0, 1) for leaf in t.get_leaves()}
drawer.add_heatmap(expr, width=20, offset=330, high_color="darkblue")

# Add title
drawer.add_title("Circular Phylogeny")

# Export
drawer.save_png("radial_tree.png", dpi=300)
```

## Properties

#### `d`

Access to the underlying drawsvg Drawing object for advanced customization.

**Example:**

```python
drawer.draw()
svg = drawer.d  # Raw SVG drawing
```

## Radial-Specific Considerations

1. **Width and height should be equal** for square canvas with circular tree
2. **Radius should be less than width/2** to keep tree within bounds
3. **Use offset values** (typically radius + 20-50) for heatmaps
4. **Legend placement** is important to avoid tree overlap
5. **Test rotations** to find best starting angle for your data
