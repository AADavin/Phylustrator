# VerticalTreeDrawer API Reference

The `VerticalTreeDrawer` class renders phylogenetic trees in a vertical (or horizontal) layout.

## Class Definition

```python
class VerticalTreeDrawer(BaseDrawer):
    """Draws phylogenetic trees in vertical layout."""
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

t = ete3.Tree("(A:1,B:1)C;", format=1)
drawer = ph.VerticalTreeDrawer(t)

# Or with custom style
style = ph.TreeStyle(width=800, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)
```

## Methods

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

# Color branches by clade
colors = {}
for node in t.traverse():
    colors[node] = "blue" if node.is_leaf else "green"
drawer.draw(branch2color=colors)
```

### Annotations

#### `add_leaf_names(offset=0, font_size=None)`

Display the names of all leaf nodes.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `offset` | `float` | 0 | Distance from leaf nodes in pixels |
| `font_size` | `int` | None | Font size (uses style default if None) |

**Returns:** None

**Example:**

```python
drawer.add_leaf_names()
drawer.add_leaf_names(offset=30, font_size=14)
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
    leaves=["A", "B"],
    shape="circle",
    fill="red",
    r=6,
    stroke="black",
    stroke_width=1,
    offset=30
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
| `weight` | `str` | "bold" | Font weight: "bold", "normal", etc. |

**Returns:** None

**Raises:** `ValueError` if position is not valid

**Example:**

```python
drawer.add_title("My Phylogeny")
drawer.add_title("Species Tree", position="bottom", font_size=18)
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
| `text_anchor` | `str` | "start" | Horizontal alignment: "start", "middle", "end" |
| `dominant_baseline` | `str` | "middle" | Vertical alignment |
| `rotation` | `float` | 0.0 | Rotation in degrees |

**Returns:** None

**Example:**

```python
drawer.add_text("Custom label", x=100, y=50, font_size=14)
```

### Highlights and Styling

#### `highlight_clade(clade, color="yellow", opacity=0.3, padding=2)`

Highlight a clade with a shaded background box.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `clade` | `ete3.Tree` | Required | The clade node to highlight |
| `color` | `str` | "yellow" | CSS fill color |
| `opacity` | `float` | 0.3 | Fill opacity (0.0-1.0) |
| `padding` | `float` | 2 | Padding around clade in pixels |

**Returns:** None

**Example:**

```python
clade = t.get_common_ancestor("A", "B")
drawer.highlight_clade(clade, color="blue", opacity=0.2)
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
drawer.highlight_branch(branch, color="blue", stroke_width=4)
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
drawer.gradient_branch(branch, colors=("purple", "orange"), stroke_width=3)
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
    "stroke": "black",          # Optional stroke
    "stroke_width": 1           # Optional stroke width
}
```

**Returns:** None

**Example:**

```python
events = [
    {"branch": "A", "where": 0.3, "shape": "circle", "fill": "red", "r": 5},
    {"branch": "B", "where": 0.7, "shape": "square", "fill": "blue", "r": 4},
]
drawer.add_branch_shapes(events)
```

#### `plot_transfers(transfer_data, curve_type="C", stroke_width=2, opacity=0.6, gradient_colors=None)`

Visualize horizontal gene transfer events as curved connections.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transfer_data` | `list[dict]` | Required | List of transfer dicts |
| `curve_type` | `str` | "C" | Curve type: "C" (cubic), "Q" (quadratic), "L" (linear) |
| `stroke_width` | `float` | 2 | Line thickness |
| `opacity` | `float` | 0.6 | Transparency (0.0-1.0) |
| `gradient_colors` | `tuple[str, str]` | None | (start_color, end_color) for gradient |

**Transfer Dictionary Format:**

```python
{
    "from": "source_leaf",      # Source leaf name
    "to": "target_leaf",        # Target leaf name
    "freq": 1.0                 # Optional frequency (0.0-1.0)
}
```

**Returns:** None

**Example:**

```python
transfers = [
    {"from": "A", "to": "B"},
    {"from": "C", "to": "D"},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=2.5,
    opacity=0.5,
    gradient_colors=("purple", "orange")
)
```

### Heatmaps

#### `add_heatmap(data, width=15, offset=50, low_color="white", high_color="red", border_color=None, border_width=0.5)`

Display continuous data as a color-coded column.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `dict[str, float]` | Required | Mapping of leaf names to values |
| `width` | `float` | 15 | Column width in pixels |
| `offset` | `float` | 50 | Distance from tree |
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
    offset=50,
    low_color="white",
    high_color="blue",
    border_color="black"
)
```

#### `add_time_axis(ticks, label="Time", y_offset=20)`

Add a time/evolutionary scale axis.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ticks` | `list[float]` | Required | Tick positions |
| `label` | `str` | "Time" | Axis label |
| `y_offset` | `float` | 20 | Y offset in pixels |

**Returns:** None

**Example:**

```python
drawer.add_time_axis(
    ticks=[0, 0.5, 1.0, 1.5, 2.0],
    label="Million years ago",
    y_offset=30
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
    palette={"Group A": "blue", "Group B": "red"},
    title="Categories",
    x=-250,
    y=-250
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
    high_color="blue",
    vmin=0,
    vmax=1,
    title="Expression Level",
    x=100,
    y=-250
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
drawer.save_svg("tree.svg")
drawer.save_svg("tree.svg", rotation=90)
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
drawer.save_png("tree.png", dpi=300)
drawer.save_png("tree_high_res.png", dpi=600)
```

## Properties

#### `d`

Access to the underlying drawsvg Drawing object for advanced customization.

**Example:**

```python
drawer.draw()
# Access raw SVG drawing object
svg_drawing = drawer.d
```

## Complete Example

```python
import ete3
import phylustrator as ph

# Load tree
t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

# Create drawer
style = ph.TreeStyle(width=800, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw and annotate
drawer.draw()
drawer.add_leaf_names(offset=25)
drawer.add_title("My Tree")

# Add styling
ab = t.get_common_ancestor("A", "B")
drawer.highlight_clade(ab, color="blue", opacity=0.2)

# Export
drawer.save_png("tree.png", dpi=300)
```

## Error Handling

```python
import phylustrator as ph
import ete3

# TypeError if tree is None
try:
    drawer = ph.VerticalTreeDrawer(None)
except TypeError as e:
    print(f"Error: {e}")

# ValueError for invalid position in add_title
try:
    drawer.add_title("My Tree", position="invalid")
except ValueError as e:
    print(f"Error: {e}")
```
