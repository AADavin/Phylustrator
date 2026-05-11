# Styling and Customization Guide

This guide explains all the styling options available through the TreeStyle configuration object.

## TreeStyle Overview

The `TreeStyle` class controls the appearance of your phylogenetic tree. Create and customize a style before passing it to a drawer:

```python
import phylustrator as ph

style = ph.TreeStyle(
    width=600,
    height=600,
    branch_stroke_width=2,
    branch_color="black"
)

drawer = ph.VerticalTreeDrawer(tree, style=style)
```

## Canvas Dimensions

### Basic Size Control

```python
style = ph.TreeStyle(
    width=1000,      # Canvas width in pixels
    height=800,      # Canvas height in pixels
)
```

### Margin and Spacing

Add padding around the tree:

```python
style = ph.TreeStyle(
    width=600,
    height=600,
    margin=80        # Pixels of padding on all sides
)
```

The margin prevents tree elements from touching the canvas edge and provides space for legends and labels.

## Tree Layout Parameters

### Vertical Tree Layout

```python
style = ph.TreeStyle(
    width=600,
    height=600,
    root_stub_length=20  # Length of the root branch
)
```

### Radial Tree Layout

```python
style = ph.TreeStyle(
    width=700,
    height=700,
    radius=300,      # Distance from center to leaves
    degrees=360,     # Angular span (360 = full circle, 180 = semicircle)
    rotation=-90     # Starting angle in degrees
)
```

## Branch Styling

### Branch Thickness

Control the width of branch lines:

```python
style = ph.TreeStyle(
    branch_stroke_width=1.0   # Thin branches
)

style = ph.TreeStyle(
    branch_stroke_width=4.0   # Thick branches
)
```

Typical values: 1.0-3.0 for standard trees, 4.0+ for emphasized features.

### Branch Color

Set the default branch color:

```python
style = ph.TreeStyle(
    branch_color="black"
)

style = ph.TreeStyle(
    branch_color="#333333"    # Hex color
)

style = ph.TreeStyle(
    branch_color="darkgray"
)
```

Supported formats:
- CSS named colors: `"red"`, `"blue"`, `"darkgreen"`, etc.
- Hex codes: `"#ff0000"`, `"#abc"`, etc.
- RGB tuples: automatically converted

## Node Styling

### Leaf Node Circles

Control the appearance of leaf-tip nodes:

```python
style = ph.TreeStyle(
    leaf_r=5.0,       # Radius of leaf circles
    leaf_color="blue"
)

style = ph.TreeStyle(
    leaf_r=0          # Hide leaf nodes
)
```

### Internal Node Circles

Control internal node appearance:

```python
style = ph.TreeStyle(
    node_r=3.0,       # Radius of internal node circles
)

style = ph.TreeStyle(
    node_r=0          # Hide internal nodes
)
```

## Font and Text Styling

### Font Selection

```python
style = ph.TreeStyle(
    font_family="Arial",        # Default
    font_size=12                # Default size
)

style = ph.TreeStyle(
    font_family="Times New Roman",
    font_size=14
)

style = ph.TreeStyle(
    font_family="Courier",
    font_size=10                # Monospace for code-like labels
)
```

Common font families:
- Arial (sans-serif, clean)
- Times New Roman (serif, traditional)
- Courier (monospace)
- Helvetica (sans-serif)
- Verdana (sans-serif, legible)

### Font Size Adjustments

Fine-tune text sizes for different elements:

```python
# In draw methods
drawer.add_leaf_names(font_size=14)
drawer.add_title("My Tree", font_size=18)
drawer.add_text("Custom label", x=100, y=100, font_size=10)
```

## Complete Style Examples

### Publication-Quality Style

For high-resolution figures:

```python
publication_style = ph.TreeStyle(
    width=1200,
    height=1000,
    margin=100,
    branch_stroke_width=2.5,
    branch_color="black",
    leaf_r=0,                   # No leaf circles
    node_r=0,                   # No internal node circles
    font_family="Arial",
    font_size=12
)

drawer = ph.VerticalTreeDrawer(tree, style=publication_style)
drawer.draw()
drawer.add_leaf_names(font_size=14)
drawer.save_png("figure.png", dpi=300)
```

### Presentation Style

For slides and talks:

```python
presentation_style = ph.TreeStyle(
    width=800,
    height=600,
    margin=60,
    branch_stroke_width=3,
    branch_color="darkblue",
    leaf_r=4,
    node_r=2,
    font_family="Arial",
    font_size=16
)

drawer = ph.VerticalTreeDrawer(tree, style=presentation_style)
drawer.draw()
drawer.add_leaf_names(font_size=18)
drawer.save_png("slide.png", dpi=150)
```

### Minimal Style

For simple, clean visualizations:

```python
minimal_style = ph.TreeStyle(
    width=500,
    height=500,
    margin=40,
    branch_stroke_width=1.5,
    branch_color="#666666",
    leaf_r=0,
    node_r=0,
    font_family="Arial",
    font_size=11
)
```

### Radial Tree Style

Optimized for circular layouts:

```python
radial_style = ph.TreeStyle(
    width=800,
    height=800,
    radius=300,
    degrees=360,
    rotation=-90,
    margin=50,
    branch_stroke_width=2,
    branch_color="black",
    leaf_r=3,
    node_r=0,
    font_size=12
)

drawer = ph.RadialTreeDrawer(tree, style=radial_style)
```

## Color References

### Named Colors

Commonly used CSS color names:

```python
# Blues
"blue", "darkblue", "lightblue", "navy", "steelblue", "cyan"

# Reds
"red", "darkred", "crimson", "salmon", "pink", "coral"

# Greens
"green", "darkgreen", "lightgreen", "lime", "olive", "teal"

# Neutrals
"black", "white", "gray", "grey", "silver", "lightgray"

# Warm colors
"orange", "gold", "yellow", "brown", "maroon"

# Other
"purple", "magenta", "indigo", "violet"
```

### Hex Color Codes

Use hex codes for custom colors:

```python
"#000000"  # Black
"#ffffff"  # White
"#ff0000"  # Red
"#00ff00"  # Green
"#0000ff"  # Blue
"#ff8800"  # Orange
"#8800ff"  # Purple
```

### Color Schemes for Science

Professional color schemes suitable for scientific figures:

```python
# Tol's Viridis-like palette (print-friendly)
colors_vibrant = {
    "blue": "#0173B2",
    "orange": "#DE8F05",
    "red": "#CC78BC",
    "green": "#029E73",
    "purple": "#CA9161"
}

# Light, distinct colors
colors_light = {
    "lightblue": "#ADD8E6",
    "lightgreen": "#90EE90",
    "lightcoral": "#F08080",
    "lightyellow": "#FFFFE0"
}
```

## Dynamic Styling

### Color Nodes by Value

Map numerical values to colors:

```python
import phylustrator as ph

def value_to_color(value, min_val, max_val):
    """Map value to color gradient."""
    t = (value - min_val) / (max_val - min_val)
    return ph.utils.lerp_color("white", "red", t)

# Example usage
node_values = {n: float(n.dist) for n in tree.traverse()}
colors = {n: value_to_color(v, 0, 1) for n, v in node_values.items()}

drawer.draw(branch2color=colors)
```

### Clade-Specific Colors

Color different clades distinctly:

```python
def color_clades(tree):
    """Assign colors to different clades."""
    colors = {}
    clade_colors = ["blue", "red", "green", "orange"]

    for i, node in enumerate(tree.get_monophyletic_groups()):
        for n in node.traverse():
            colors[n] = clade_colors[i % len(clade_colors)]

    return colors
```

## Validation

The `TreeStyle` class validates parameters on initialization:

```python
try:
    bad_style = ph.TreeStyle(width=-100)  # Invalid
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: width must be positive, got -100
```

Valid constraints:
- `width` and `height`: must be positive
- `radius`: must be positive
- `margin`: must be non-negative
- `branch_stroke_width`: must be positive
- `font_size`: must be positive

## Style Best Practices

1. **For publication**: Use DPI 300+, minimal styling, clear labels
2. **For presentations**: Use larger fonts, thicker branches, bold colors
3. **For web**: Use lower DPI (72-150), smaller file sizes
4. **For printing**: Use high contrast, dark on light backgrounds
5. **Test export quality**: Always export and view at intended size
6. **Consider colorblind accessibility**: Avoid red-green only distinctions
7. **Keep consistent**: Use the same style throughout a figure series

## Common Styling Patterns

### Scientific Paper Figure

```python
style = ph.TreeStyle(
    width=1000,
    height=800,
    margin=80,
    branch_stroke_width=2,
    leaf_r=0,
    node_r=0,
    font_family="Arial",
    font_size=11
)
```

### Conference Poster

```python
style = ph.TreeStyle(
    width=1500,
    height=1200,
    margin=150,
    branch_stroke_width=4,
    leaf_r=5,
    node_r=3,
    font_family="Arial",
    font_size=20
)
```

### Interactive Web Display

```python
style = ph.TreeStyle(
    width=600,
    height=600,
    margin=50,
    branch_stroke_width=2,
    leaf_r=3,
    node_r=2,
    font_family="Arial",
    font_size=12
)
```
