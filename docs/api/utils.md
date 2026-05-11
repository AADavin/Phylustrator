# Utility Functions API Reference

Phylustrator provides utility functions for color manipulation, coordinate conversion, and tree operations.

## Color Functions

### `to_rgb(color_str)`

Parse a CSS color string into an RGB tuple.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `color_str` | `str` | A CSS color string (hex, named color) |

**Returns:** `tuple[int, int, int]` - RGB values in range [0, 255]

**Supported Formats:**
- Hex codes: `"#fff"`, `"#ffffff"`, `"#ff0000"`
- Named colors: `"red"`, `"blue"`, `"darkgreen"`, etc.
- Fallback: returns black `(0, 0, 0)` for unrecognized values

**Example:**

```python
import phylustrator as ph

rgb = ph.utils.to_rgb("red")          # Returns (255, 0, 0)
rgb = ph.utils.to_rgb("#0000ff")      # Returns (0, 0, 255)
rgb = ph.utils.to_rgb("#abc")         # Returns (170, 187, 204)
rgb = ph.utils.to_rgb("darkgreen")    # Returns (0, 100, 0)
rgb = ph.utils.to_rgb("invalid")      # Returns (0, 0, 0) with warning
```

### `to_hex(rgb)`

Convert an RGB tuple to a hex color string.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `rgb` | `tuple[int, int, int]` | RGB values (clamped to [0, 255]) |

**Returns:** `str` - Hex color string like `"#ff00ab"`

**Example:**

```python
import phylustrator as ph

hex_color = ph.utils.to_hex((255, 0, 0))       # Returns "#ff0000"
hex_color = ph.utils.to_hex((0, 128, 255))     # Returns "#0080ff"
hex_color = ph.utils.to_hex((300, -10, 128))   # Clamps to "#ffc080"
```

### `lerp_color(low_hex, high_hex, t)`

Linearly interpolate between two colors.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `low_hex` | `str` | Start color (CSS string) |
| `high_hex` | `str` | End color (CSS string) |
| `t` | `float` | Interpolation factor, clamped to [0.0, 1.0] |

**Returns:** `str` - Interpolated hex color string

**Example:**

```python
import phylustrator as ph

# Mid-point between white and blue
color = ph.utils.lerp_color("white", "blue", 0.5)

# Linear gradient along a heatmap
for i in range(10):
    t = i / 9.0
    color = ph.utils.lerp_color("white", "red", t)

# Applied to branch coloring
min_val, max_val = 0, 100
branch_value = 50
t = (branch_value - min_val) / (max_val - min_val)
branch_color = ph.utils.lerp_color("blue", "red", t)
```

## Coordinate Functions

### `polar_to_cartesian(degree, radius, rotation=0.0)`

Convert polar coordinates to Cartesian (x, y).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `degree` | `float` | Required | Angle in degrees |
| `radius` | `float` | Required | Radial distance from origin |
| `rotation` | `float` | 0.0 | Additional rotation offset in degrees |

**Returns:** `tuple[float, float]` - Cartesian (x, y) coordinates

**Example:**

```python
import phylustrator as ph

# Point at 0 degrees, radius 100
x, y = ph.utils.polar_to_cartesian(0, 100)  # (100, 0)

# Point at 90 degrees (top), radius 50
x, y = ph.utils.polar_to_cartesian(90, 50)  # (0, 50)

# With rotation offset
x, y = ph.utils.polar_to_cartesian(0, 100, rotation=-90)  # (0, -100)

# Radial tree leaf positioning
angles = [0, 60, 120, 180, 240, 300]
radius = 300
for angle in angles:
    x, y = ph.utils.polar_to_cartesian(angle, radius, rotation=-90)
    # Draw leaf at (x, y)
```

## Tree Manipulation

### `add_origin_if_root_has_dist(tree, origin_name="Origin")`

Standardize a tree by adding an explicit origin node if the root has a non-zero distance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tree` | `ete3.Tree` | Required | The phylogenetic tree |
| `origin_name` | `str` | "Origin" | Name for the new origin node |

**Returns:** `ete3.Tree` - The modified tree with explicit origin if needed

**Description:**

Some phylogenetic files include branch length for the root node, which represents a "stem" or "outgroup branch". This function creates an explicit origin node to properly represent this branch.

**Example:**

```python
import ete3
import phylustrator as ph

# Tree with root distance (represents branch length from origin)
t = ete3.Tree("(A:1,B:1)C:0.5;", format=1)

# Add origin node
t = ph.utils.add_origin_if_root_has_dist(t)

# Now tree has explicit origin: Origin -> C -> [A, B]

# With custom origin name
t = ph.utils.add_origin_if_root_has_dist(t, origin_name="Ancestor")
```

## ID Generation

### `generate_id(prefix="id", length=6)`

Generate a unique ID for SVG elements like gradients.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | `str` | "id" | String prefix for the ID |
| `length` | `int` | 6 | Number of random characters to append |

**Returns:** `str` - A unique ID string like `"prefix_a1b2c3"`

**Example:**

```python
import phylustrator as ph

# Generate SVG element IDs
gradient_id = ph.utils.generate_id("grad")      # "grad_x7k2p1"
filter_id = ph.utils.generate_id("filter")      # "filter_m9n3q5"
unique_id = ph.utils.generate_id()              # "id_a8b2c1"

# Each call generates a new unique ID
for i in range(3):
    print(ph.utils.generate_id("elem"))
    # "elem_k3m1n7"
    # "elem_p5q9r2"
    # "elem_l8m2o6"
```

## Complete Usage Examples

### Color Gradient in Heatmap

```python
import phylustrator as ph

def create_heatmap_colors(data, low_color, high_color):
    """Generate heatmap colors for a dataset."""
    if not data:
        return {}

    values = list(data.values())
    min_val = min(values)
    max_val = max(values)

    colors = {}
    for name, value in data.items():
        t = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        colors[name] = ph.utils.lerp_color(low_color, high_color, t)

    return colors

# Usage
data = {"A": 0.2, "B": 0.5, "C": 0.9}
colors = create_heatmap_colors(data, "white", "blue")
# {"A": "#e6e6ff", "B": "#8080ff", "C": "#0000ff"}
```

### Dynamic Branch Coloring by Value

```python
import phylustrator as ph
import ete3

t = ete3.Tree("((A:1,B:0.5)AB:1,(C:0.8,D:1.2)CD:1)root;", format=1)

def color_branches_by_length(tree):
    """Color branches based on their length."""
    lengths = [n.dist for n in tree.traverse() if n.dist]
    min_len = min(lengths)
    max_len = max(lengths)

    colors = {}
    for node in tree.traverse():
        if node.dist:
            t_val = (node.dist - min_len) / (max_len - min_len)
            colors[node] = ph.utils.lerp_color("blue", "red", t_val)
        else:
            colors[node] = "gray"

    return colors

branch_colors = color_branches_by_length(t)
drawer.draw(branch2color=branch_colors)
```

### Radial Tree with Custom Positioning

```python
import phylustrator as ph
import ete3

t = ete3.Tree("(A:1,B:1,C:1,D:1,E:1)root;", format=1)

leaves = t.get_leaves()
n_leaves = len(leaves)
radius = 300

# Manually position leaves in a circle
for i, leaf in enumerate(leaves):
    angle = (360 / n_leaves) * i
    x, y = ph.utils.polar_to_cartesian(angle, radius, rotation=-90)
    leaf.x = x
    leaf.y = y
    print(f"{leaf.name}: ({x:.1f}, {y:.1f})")
```

### Conditional Color Mapping

```python
import phylustrator as ph

def map_trait_to_color(tree, trait_dict, trait_colors):
    """Map node traits to colors."""
    colors = {}
    for node in tree.traverse():
        if node.is_leaf:
            trait = trait_dict.get(node.name, "unknown")
            colors[node] = trait_colors.get(trait, "gray")
        else:
            colors[node] = "lightgray"
    return colors

# Usage
t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

traits = {"A": "herbivore", "B": "carnivore", "C": "omnivore", "D": "herbivore"}
trait_colors = {
    "herbivore": "green",
    "carnivore": "red",
    "omnivore": "orange",
    "unknown": "gray"
}

colors = map_trait_to_color(t, traits, trait_colors)
drawer.draw(branch2color=colors)
```

## Named Colors Reference

### Basic Colors

```
"black"     (0, 0, 0)
"white"     (255, 255, 255)
"red"       (255, 0, 0)
"green"     (0, 128, 0)
"blue"      (0, 0, 255)
"yellow"    (255, 255, 0)
"orange"    (255, 165, 0)
"purple"    (128, 0, 128)
```

### Extended Colors

```
"darkred"       (139, 0, 0)
"darkgreen"     (0, 100, 0)
"darkblue"      (0, 0, 139)
"lightblue"     (173, 216, 230)
"lightgreen"    (144, 238, 144)
"lightgray"     (211, 211, 211)
"darkgray"      (169, 169, 169)
"brown"         (165, 42, 42)
"pink"          (255, 192, 203)
"cyan"          (0, 255, 255)
"magenta"       (255, 0, 255)
"navy"          (0, 0, 128)
"teal"          (0, 128, 128)
"coral"         (255, 127, 80)
"salmon"        (250, 128, 114)
"gold"          (255, 215, 0)
```

## Tips for Utilities

1. **Use `lerp_color`** for smooth gradient heatmaps and branch coloring
2. **Use `to_rgb` and `to_hex`** for color format conversions in custom code
3. **Use `add_origin_if_root_has_dist`** for trees with explicit root branches
4. **Use `generate_id`** when creating dynamic SVG elements
5. **Use `polar_to_cartesian`** for positioning in radial layouts

## Error Handling

```python
import phylustrator as ph

# to_rgb with invalid color - returns black and warns
rgb = ph.utils.to_rgb("notacolor")  # (0, 0, 0) with warning

# to_hex clamps values
hex_color = ph.utils.to_hex((300, -50, 128))  # Clamps to valid range

# lerp_color clamps t value
color = ph.utils.lerp_color("red", "blue", 1.5)  # Clamps t to 1.0
```
