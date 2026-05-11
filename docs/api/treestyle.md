# TreeStyle API Reference

The `TreeStyle` class defines all visual styling parameters for phylogenetic tree rendering.

## Class Definition

```python
@dataclass
class TreeStyle:
    """Configuration object for visual styling parameters of the phylogenetic tree."""
```

## Attributes

All dimensional values are in pixels unless otherwise noted.

### Canvas Dimensions

#### `width`
- **Type:** `int`
- **Default:** `1000`
- **Description:** Total width of the drawing canvas in pixels. Must be positive.
- **Example:**
  ```python
  style = TreeStyle(width=800)
  ```

#### `height`
- **Type:** `int`
- **Default:** `1000`
- **Description:** Total height of the drawing canvas in pixels. Must be positive.
- **Example:**
  ```python
  style = TreeStyle(height=600)
  ```

#### `margin`
- **Type:** `float`
- **Default:** `100.0`
- **Description:** Margin padding around the tree in pixels. Must be non-negative. Provides space for legends and annotations.
- **Example:**
  ```python
  style = TreeStyle(margin=80)
  ```

### Tree Layout (Radial Trees)

#### `radius`
- **Type:** `int`
- **Default:** `400`
- **Description:** Radius of the tree layout for radial (circular) trees in pixels. Distance from center to leaves. Must be positive.
- **Example:**
  ```python
  style = TreeStyle(radius=300)
  ```

#### `degrees`
- **Type:** `int`
- **Default:** `360`
- **Description:** Angular span in degrees for radial trees. Use 360 for full circle, 180 for semicircle. Must be positive.
- **Example:**
  ```python
  style = TreeStyle(degrees=180)  # Semicircle
  ```

#### `rotation`
- **Type:** `int`
- **Default:** `-90`
- **Description:** Global rotation offset in degrees. Standard values: -90 (top), 0 (right), 90 (bottom), 180 (left).
- **Example:**
  ```python
  style = TreeStyle(rotation=0)  # Start from right
  ```

### Vertical Tree Layout

#### `root_stub_length`
- **Type:** `float`
- **Default:** `20.0`
- **Description:** Length of the root branch stub in pixels.
- **Example:**
  ```python
  style = TreeStyle(root_stub_length=50)
  ```

### Branch Styling

#### `branch_stroke_width`
- **Type:** `float`
- **Default:** `2.0`
- **Description:** Thickness of branch lines in pixels. Must be positive. Typical range: 1.0-4.0.
- **Example:**
  ```python
  style = TreeStyle(branch_stroke_width=2.5)
  ```

#### `branch_color`
- **Type:** `str`
- **Default:** `"black"`
- **Description:** CSS color string for branch lines. Supports named colors, hex codes, and RGB tuples.
- **Supported formats:**
  - Named colors: `"black"`, `"blue"`, `"red"`, etc.
  - Hex codes: `"#000000"`, `"#0000ff"`, etc.
- **Example:**
  ```python
  style = TreeStyle(branch_color="darkgray")
  style = TreeStyle(branch_color="#333333")
  ```

### Node Styling

#### `leaf_r`
- **Type:** `float`
- **Default:** `5.0`
- **Description:** Radius of leaf-tip circles in pixels. Set to 0 to hide leaf nodes.
- **Example:**
  ```python
  style = TreeStyle(leaf_r=0)      # Hide leaf nodes
  style = TreeStyle(leaf_r=6)      # Larger nodes
  ```

#### `leaf_color`
- **Type:** `str`
- **Default:** `"black"`
- **Description:** CSS color string for leaf node circles. Same format as `branch_color`.
- **Example:**
  ```python
  style = TreeStyle(leaf_color="blue")
  ```

#### `node_r`
- **Type:** `float`
- **Default:** `2.0`
- **Description:** Radius of internal node circles in pixels. Set to 0 to hide internal nodes.
- **Example:**
  ```python
  style = TreeStyle(node_r=0)      # Hide internal nodes
  style = TreeStyle(node_r=3)      # Larger nodes
  ```

### Font and Text

#### `font_size`
- **Type:** `int`
- **Default:** `12`
- **Description:** Base font size for text elements in pixels. Must be positive. Individual text elements can override this.
- **Example:**
  ```python
  style = TreeStyle(font_size=14)
  ```

#### `font_family`
- **Type:** `str`
- **Default:** `"Arial"`
- **Description:** Font family for text elements. Common options: Arial, Times New Roman, Courier, Helvetica, Verdana.
- **Example:**
  ```python
  style = TreeStyle(font_family="Times New Roman")
  ```

## Methods

### `__post_init__()`
- **Signature:** `def __post_init__(self) -> None`
- **Description:** Validates all style parameters after initialization. Raises `ValueError` if any parameter is invalid.
- **Raises:**
  - `ValueError`: If width <= 0, height <= 0, radius <= 0, margin < 0, branch_stroke_width <= 0, or font_size <= 0

## Validation Rules

The following constraints are enforced at initialization:

| Parameter | Constraint | Error Message |
|-----------|-----------|----------------|
| `width` | Must be > 0 | "width must be positive, got {value}" |
| `height` | Must be > 0 | "height must be positive, got {value}" |
| `radius` | Must be > 0 | "radius must be positive, got {value}" |
| `margin` | Must be >= 0 | "margin must be non-negative, got {value}" |
| `branch_stroke_width` | Must be > 0 | "branch_stroke_width must be positive, got {value}" |
| `font_size` | Must be > 0 | "font_size must be positive, got {value}" |

## Usage Examples

### Minimal Style (Default)

```python
import phylustrator as ph

# Uses all defaults
style = ph.TreeStyle()

# Equivalent to
style = ph.TreeStyle(
    width=1000,
    height=1000,
    radius=400,
    degrees=360,
    rotation=-90,
    margin=100.0,
    root_stub_length=20.0,
    leaf_r=5.0,
    leaf_color="black",
    branch_stroke_width=2.0,
    branch_color="black",
    node_r=2.0,
    font_size=12,
    font_family="Arial"
)
```

### Custom Style for Vertical Trees

```python
import phylustrator as ph
import ete3

t = ete3.Tree("(A:1,B:1)C;", format=1)

style = ph.TreeStyle(
    width=800,
    height=600,
    margin=60,
    branch_stroke_width=2.5,
    branch_color="darkblue",
    leaf_r=4,
    node_r=2,
    font_size=13,
    font_family="Arial"
)

drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
```

### Custom Style for Radial Trees

```python
import phylustrator as ph
import ete3

t = ete3.Tree("(A:1,B:1,C:1)D;", format=1)

style = ph.TreeStyle(
    width=700,
    height=700,
    radius=300,
    degrees=360,
    rotation=-90,
    margin=50,
    branch_stroke_width=2,
    leaf_r=3,
    node_r=0,
    font_size=12
)

drawer = ph.RadialTreeDrawer(t, style=style)
drawer.draw()
```

### Publication-Quality Style

```python
import phylustrator as ph

style = ph.TreeStyle(
    width=1200,
    height=1000,
    margin=100,
    branch_stroke_width=2.5,
    branch_color="black",
    leaf_r=0,           # Hide leaf nodes for clarity
    node_r=0,           # Hide internal nodes
    font_family="Arial",
    font_size=12
)

# Use with high-resolution export
drawer.save_png("figure.png", dpi=300)
```

### Minimalist Style

```python
import phylustrator as ph

style = ph.TreeStyle(
    width=500,
    height=500,
    margin=30,
    branch_stroke_width=1.5,
    branch_color="#666666",
    leaf_r=0,
    node_r=0,
    font_size=10
)
```

## Color Reference

### Supported Color Formats

```python
# Named colors
style = ph.TreeStyle(branch_color="red")
style = ph.TreeStyle(branch_color="darkblue")

# Hex codes
style = ph.TreeStyle(branch_color="#ff0000")
style = ph.TreeStyle(branch_color="#0000ff")
```

### Common Named Colors

- **Primary:** black, white, red, green, blue, yellow, orange, purple
- **Shades:** darkred, darkgreen, darkblue, lightred, lightgreen, lightblue
- **Grays:** gray, grey, lightgray, darkgray, silver
- **Others:** brown, pink, cyan, magenta, navy, teal, coral, salmon

## Common Combinations

### Large, Presentation-Quality Trees

```python
style = ph.TreeStyle(
    width=1000,
    height=800,
    margin=80,
    branch_stroke_width=3,
    font_size=16,
    leaf_r=5,
    node_r=3
)
```

### Small, Web-Friendly Trees

```python
style = ph.TreeStyle(
    width=400,
    height=400,
    margin=30,
    branch_stroke_width=1,
    font_size=10,
    leaf_r=0,
    node_r=0
)
```

### Dense Scientific Trees

```python
style = ph.TreeStyle(
    width=2000,
    height=1500,
    margin=200,
    branch_stroke_width=1.5,
    font_size=11,
    leaf_r=0,
    node_r=0
)
```

## Error Handling

```python
import phylustrator as ph

try:
    bad_style = ph.TreeStyle(width=-100)
except ValueError as e:
    print(e)  # Output: width must be positive, got -100

try:
    bad_style = ph.TreeStyle(branch_stroke_width=0)
except ValueError as e:
    print(e)  # Output: branch_stroke_width must be positive, got 0
```

## Creating Variants

```python
import phylustrator as ph

# Base style
base = ph.TreeStyle(
    width=800,
    height=600,
    font_family="Arial"
)

# Create variants using dataclass replace
from dataclasses import replace

# High contrast variant
high_contrast = replace(base, branch_stroke_width=4)

# Minimalist variant
minimal = replace(base, leaf_r=0, node_r=0, margin=30)
```

## Tips

1. **Always set both width and height** for consistent aspect ratios
2. **Match margin to expected element sizes** (legends, labels)
3. **For radial trees, radius should be < min(width, height) / 3**
4. **Test with actual data** before finalizing style choices
5. **Use consistent font families** throughout a figure series
6. **Consider export resolution** when choosing font sizes
