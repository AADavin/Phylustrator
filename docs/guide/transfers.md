# HGT Visualization Guide

This guide explains how to visualize horizontal gene transfer (HGT) and other inter-lineage events.

## Overview

HGT events can be visualized as curved connections between lineages. Phylustrator supports flexible styling for these transfers, including:

- Multiple transfer events
- Curved paths (cubic, quadratic, linear)
- Color gradients
- Opacity control
- Frequency-based sizing

## Basic HGT Visualization

### Simple Transfers

```python
import phylustrator as ph

# Define transfers as a list of dictionaries
transfers = [
    {"from": "species_A", "to": "species_B"},
    {"from": "species_C", "to": "species_D"},
]

drawer.plot_transfers(transfers)
```

### With Styling

```python
transfers = [
    {"from": "A", "to": "B"},
    {"from": "C", "to": "D"},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",           # Cubic curves (smooth)
    stroke_width=2,           # Line thickness
    opacity=0.6,              # Semi-transparent
    gradient_colors=("purple", "orange")  # Start to end color
)
```

## Transfer Parameters

### Transfer Dictionary

Each transfer entry contains:

```python
{
    "from": "source_leaf_name",      # Required: source lineage
    "to": "target_leaf_name",        # Required: target lineage
    "freq": 1.0,                     # Optional: frequency/weight (0-1)
}
```

### Styling Parameters

```python
drawer.plot_transfers(
    transfers,
    curve_type="C",           # "C" (cubic), "Q" (quadratic), "L" (linear)
    stroke_width=2,           # Line thickness in pixels
    opacity=0.6,              # Transparency (0.0-1.0)
    gradient_colors=("purple", "orange")  # (start_color, end_color)
)
```

## Curve Types

### Cubic Curves (Default)

Smooth, professional-looking curves:

```python
drawer.plot_transfers(
    transfers,
    curve_type="C"
)
```

Best for: Publication figures, complex transfer networks

### Quadratic Curves

Slightly less smooth than cubic:

```python
drawer.plot_transfers(
    transfers,
    curve_type="Q"
)
```

Best for: Simple networks, quick visualizations

### Linear Paths

Direct straight connections:

```python
drawer.plot_transfers(
    transfers,
    curve_type="L"
)
```

Best for: Clarity, when curves would overlap

## Styling Transfers

### Color Gradients

Apply a color gradient from source to destination:

```python
drawer.plot_transfers(
    transfers,
    gradient_colors=("blue", "red")    # Blue source to red destination
)

drawer.plot_transfers(
    transfers,
    gradient_colors=("purple", "orange")
)
```

### Single Color

Use a uniform color for all transfers:

```python
drawer.plot_transfers(
    transfers,
    gradient_colors=("darkgreen", "darkgreen")
)
```

### Opacity

Control transparency:

```python
# Mostly transparent
drawer.plot_transfers(transfers, opacity=0.2)

# Semi-transparent
drawer.plot_transfers(transfers, opacity=0.5)

# Fully opaque
drawer.plot_transfers(transfers, opacity=1.0)
```

Use lower opacity when transfers overlap, to show density.

### Line Width

Control stroke thickness:

```python
# Thin lines
drawer.plot_transfers(transfers, stroke_width=1)

# Medium lines
drawer.plot_transfers(transfers, stroke_width=2.5)

# Thick lines (emphasis)
drawer.plot_transfers(transfers, stroke_width=4)
```

## Complex Transfer Networks

### Multiple Transfer Events

Visualize many transfers with clear styling:

```python
transfers = [
    {"from": "A", "to": "B"},
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
    {"from": "C", "to": "E"},
    {"from": "D", "to": "E"},
]

drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=2,
    opacity=0.5,
    gradient_colors=("steelblue", "coral")
)
```

### Weighted Transfers

Use frequency to indicate confidence or importance:

```python
transfers = [
    {"from": "A", "to": "B", "freq": 1.0},      # High confidence
    {"from": "A", "to": "C", "freq": 0.7},      # Medium confidence
    {"from": "B", "to": "D", "freq": 0.3},      # Low confidence
]

drawer.plot_transfers(transfers)
```

### Transfers by Type

Draw different types of events with different colors:

```python
# Gene transfer events
gene_transfers = [
    {"from": "A", "to": "B"},
    {"from": "C", "to": "D"},
]

# Symbiosis events
symbiosis = [
    {"from": "E", "to": "F"},
]

# Gene loss events
losses = [
    {"from": "G", "to": "H"},
]

drawer.plot_transfers(
    gene_transfers,
    gradient_colors=("purple", "orange"),
    stroke_width=2,
    opacity=0.6
)

drawer.plot_transfers(
    symbiosis,
    gradient_colors=("green", "lightgreen"),
    stroke_width=1.5,
    opacity=0.4
)

drawer.plot_transfers(
    losses,
    gradient_colors=("red", "darkred"),
    stroke_width=1,
    opacity=0.3
)
```

## Complete HGT Example

```python
import ete3
import phylustrator as ph

# Load phylogenetic tree
t = ete3.Tree(
    "(((A:1,B:1)AB:1,(C:1,D:1)CD:1)ABCD:1,(E:1,F:1)EF:1)root;",
    format=1
)

# Create style
style = ph.TreeStyle(
    width=900,
    height=700,
    branch_stroke_width=2.5,
    margin=80,
    font_size=12
)

drawer = ph.VerticalTreeDrawer(t, style=style)

# Draw tree
drawer.draw()
drawer.add_leaf_names(offset=30)

# Color major clades
abcd = t.get_common_ancestor("A", "B", "C", "D")
ef = t.get_common_ancestor("E", "F")

colors = {n: "black" for n in t.traverse()}
for n in abcd.traverse():
    colors[n] = "steelblue"
for n in ef.traverse():
    colors[n] = "coral"

drawer.draw(branch2color=colors)
drawer.add_leaf_names(offset=30)

# Define HGT events
transfers = [
    {"from": "A", "to": "E", "freq": 1.0},
    {"from": "B", "to": "F", "freq": 0.8},
    {"from": "C", "to": "E", "freq": 0.6},
    {"from": "D", "to": "F", "freq": 0.4},
]

# Visualize transfers
drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=2.5,
    opacity=0.5,
    gradient_colors=("purple", "lime")
)

# Add highlighting
drawer.highlight_clade(abcd, color="steelblue", opacity=0.1)
drawer.highlight_clade(ef, color="coral", opacity=0.1)

# Add legend
drawer.add_categorical_legend(
    palette={"Clade ABCD": "steelblue", "Clade EF": "coral"},
    title="Clades",
    x=-350,
    y=-250
)

drawer.add_title("HGT Network Visualization", font_size=16)

drawer.save_png("hgt_network.png", dpi=300)
```

## Tips for Complex Networks

### Reducing Clutter

When visualizing many transfers:

```python
# Use lower opacity to show density
drawer.plot_transfers(transfers, opacity=0.3)

# Use thinner lines
drawer.plot_transfers(transfers, stroke_width=1.5)

# Use linear curves for clarity
drawer.plot_transfers(transfers, curve_type="L")
```

### Highlighting Important Transfers

```python
# Main transfers
major = [
    {"from": "A", "to": "B"},
    {"from": "C", "to": "D"},
]

# Secondary transfers
minor = [
    {"from": "A", "to": "C"},
    {"from": "B", "to": "D"},
]

# Draw major transfers with high visibility
drawer.plot_transfers(
    major,
    stroke_width=3,
    opacity=0.8,
    gradient_colors=("darkblue", "darkred")
)

# Draw minor transfers more subtly
drawer.plot_transfers(
    minor,
    stroke_width=1,
    opacity=0.3,
    gradient_colors=("lightblue", "lightcoral")
)
```

### Separating Overlapping Events

When transfers overlap:

```python
# Use different curve types to distinguish events
gene_transfers = [{"from": "A", "to": "B"}, {"from": "C", "to": "D"}]
protein_transfers = [{"from": "B", "to": "A"}, {"from": "D", "to": "C"}]

drawer.plot_transfers(
    gene_transfers,
    curve_type="C",
    gradient_colors=("blue", "orange")
)

drawer.plot_transfers(
    protein_transfers,
    curve_type="Q",
    gradient_colors=("green", "red")
)
```

## Data Import for Transfers

### From List

```python
# Simple format
transfers = [
    {"from": "A", "to": "B"},
    {"from": "B", "to": "C"},
]

drawer.plot_transfers(transfers)
```

### From DataFrame

```python
import pandas as pd

df = pd.read_csv("transfers.csv")  # Columns: 'from', 'to', 'freq'
transfers = df.to_dict('records')

drawer.plot_transfers(transfers)
```

### From Custom Data

```python
# Build transfer list from tree annotations
transfers = []
for leaf in t.get_leaves():
    if hasattr(leaf, "hgt_donor"):
        transfers.append({
            "from": leaf.hgt_donor,
            "to": leaf.name,
            "freq": getattr(leaf, "hgt_freq", 1.0)
        })

drawer.plot_transfers(transfers)
```

## Legends for HGT

Add transfer legends to your figure:

```python
# Categorical legend for transfer types
drawer.add_categorical_legend(
    palette={"Gene Transfer": "#8B4789", "Recombination": "#66AA33"},
    title="Event Type",
    x=-300,
    y=-200
)
```

## Publication Quality HGT Figures

```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

# High-quality style
style = ph.TreeStyle(
    width=1200,
    height=900,
    margin=100,
    branch_stroke_width=2.5,
    font_family="Arial",
    font_size=12
)

drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names(offset=40, font_size=14)

# Define transfers
transfers = [
    {"from": "A", "to": "C", "freq": 1.0},
    {"from": "B", "to": "D", "freq": 0.8},
]

# High-quality transfer visualization
drawer.plot_transfers(
    transfers,
    curve_type="C",
    stroke_width=3,
    opacity=0.7,
    gradient_colors=("#2166AC", "#B2182B")  # Professional color palette
)

# Add title and legend
drawer.add_title("Phylogenetic Relationships and HGT Events", font_size=18)
drawer.add_categorical_legend(
    palette={"Clade AB": "#2166AC", "Clade CD": "#B2182B"},
    x=-450,
    y=-350
)

# Export at high resolution
drawer.save_png("hgt_publication.png", dpi=300)
```

## Troubleshooting

### Transfers not visible

- Ensure `from` and `to` match leaf names exactly
- Check that `opacity` is not too low (try 0.6+)
- Verify `stroke_width` is sufficient (try 2+)

### Overlapping transfers are unclear

- Use `opacity=0.3-0.5` to show density
- Use different `curve_type` values for different transfer groups
- Try `curve_type="L"` for clarity

### Performance issues with many transfers

- Split into multiple `plot_transfers()` calls
- Use lower `stroke_width`
- Use lower `opacity` to avoid excessive rendering
