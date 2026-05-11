# I/O Functions API Reference

This section documents input/output operations for phylogenetic trees. Phylustrator uses ete3 for tree I/O, which supports multiple file formats.

## Tree Loading (ete3)

Phylustrator leverages ete3 for reading phylogenetic trees. The main functions are documented here with Phylustrator-specific examples.

### `ete3.Tree(source, format=1)`

Load a phylogenetic tree from a string, file path, or file handle.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str` or `Path` | Newick string, file path, or file handle |
| `format` | `int` | Format code (0=no names, 1=names+distances, 2=other formats) |

**Returns:** `ete3.Tree` - The loaded tree object

**Supported Formats:**

| Format | Description | Example |
|--------|-------------|---------|
| 0 | No names or branch lengths | `"(,(,,));"`|
| 1 | Names and branch lengths (standard) | `"(A:1,B:1)C;"`|
| 2 | Extended Newick | `"(A:1,B:1)C:0;"`|

**Example:**

```python
import ete3
import phylustrator as ph

# From Newick string
t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

# From file
with open("tree.nwk") as f:
    t = ete3.Tree(f.readline(), format=1)

# From file path (ete3 automatically reads)
t = ete3.Tree("path/to/tree.nwk")

# Without names (format 0)
t = ete3.Tree("(,());", format=0)
```

## Export Methods

### Writing Trees with ete3

The Tree object has a `write()` method for exporting trees:

```python
import ete3

t = ete3.Tree("(A:1,B:1)C;", format=1)

# Write as Newick
newick_str = t.write(format=1)

# Write to file
with open("output.nwk", "w") as f:
    f.write(t.write(format=1))
```

## Phylustrator Export Methods

### `drawer.save_svg(outpath, rotation=0.0)`

Export visualization to SVG (scalable vector graphics).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outpath` | `str` or `Path` | Required | Output file path |
| `rotation` | `float` | 0.0 | Global rotation in degrees |

**Returns:** None

**Advantages:**
- Scalable (no quality loss when resizing)
- Small file size
- Editable in vector graphics software
- Perfect for web use

**Example:**

```python
import phylustrator as ph

drawer = ph.VerticalTreeDrawer(tree)
drawer.draw()
drawer.save_svg("tree.svg")

# With rotation
drawer.save_svg("tree_rotated.svg", rotation=90)
```

### `drawer.save_png(outpath, dpi=300, scale=None, rotation=0.0)`

Export visualization to PNG (raster format).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outpath` | `str` or `Path` | Required | Output file path |
| `dpi` | `int` | 300 | Resolution in dots per inch |
| `scale` | `float` | None | Scale factor (auto-computed from dpi if None) |
| `rotation` | `float` | 0.0 | Global rotation in degrees |

**Returns:** None

**Requirements:**
- Requires `cairosvg` library
- Install with: `pip install phylustrator[export]`

**DPI Guidelines:**
- 72-150 dpi: Screen display, web
- 300 dpi: Publication quality, print
- 600 dpi: High-resolution archival

**Example:**

```python
import phylustrator as ph

drawer = ph.VerticalTreeDrawer(tree)
drawer.draw()

# Standard publication quality
drawer.save_png("tree.png", dpi=300)

# High resolution
drawer.save_png("tree_hires.png", dpi=600)

# Web quality (smaller file)
drawer.save_png("tree_web.png", dpi=150)

# With custom scale
drawer.save_png("tree_large.png", scale=2.0)
```

### `drawer.save_pdf(outpath, dpi=300, scale=None, rotation=0.0)`

Export visualization to PDF (print-ready format).

Syntax is identical to `save_png()`.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outpath` | `str` or `Path` | Required | Output file path |
| `dpi` | `int` | 300 | Resolution in dots per inch |
| `scale` | `float` | None | Scale factor (auto-computed from dpi if None) |
| `rotation` | `float` | 0.0 | Global rotation in degrees |

**Returns:** None

**Example:**

```python
import phylustrator as ph

drawer = ph.VerticalTreeDrawer(tree)
drawer.draw()
drawer.save_pdf("tree.pdf", dpi=300)
```

## Complete I/O Workflow Examples

### Load, Visualize, and Export

```python
import ete3
import phylustrator as ph

# 1. Load tree from file
t = ete3.Tree("data/phylogeny.nwk", format=1)

# 2. Create visualization
style = ph.TreeStyle(width=1000, height=800)
drawer = ph.VerticalTreeDrawer(t, style=style)

# 3. Draw and annotate
drawer.draw()
drawer.add_leaf_names(offset=30)
drawer.add_title("Species Phylogeny")

# 4. Export in multiple formats
drawer.save_svg("outputs/tree.svg")
drawer.save_png("outputs/tree.png", dpi=300)
drawer.save_pdf("outputs/tree.pdf", dpi=300)
```

### Batch Processing Multiple Trees

```python
import ete3
import phylustrator as ph
from pathlib import Path

input_dir = Path("input_trees/")
output_dir = Path("visualizations/")
output_dir.mkdir(exist_ok=True)

# Process all Newick files
for tree_file in input_dir.glob("*.nwk"):
    # Load
    t = ete3.Tree(tree_file, format=1)

    # Visualize
    drawer = ph.VerticalTreeDrawer(t)
    drawer.draw()
    drawer.add_leaf_names()

    # Export
    base_name = tree_file.stem
    drawer.save_png(output_dir / f"{base_name}.png", dpi=300)
    drawer.save_svg(output_dir / f"{base_name}.svg")

    print(f"Processed {base_name}")
```

### Convert Between Formats

```python
import ete3
from pathlib import Path

# Read from Newick
t = ete3.Tree("tree.nwk", format=1)

# Write as different format
with open("tree_output.nex", "w") as f:
    f.write(t.write(format="nexus"))

# Extract subtree and save
subtree = t.get_common_ancestor("A", "B")
with open("subtree.nwk", "w") as f:
    f.write(subtree.write(format=1))
```

### Load Multiple Trees from Single File

```python
import ete3

# Read all trees from Nexus file
tree_file = "multiple_trees.nex"

# ete3 can read multiple trees
t = ete3.Tree(tree_file)  # Reads first tree
# For multiple trees, parse manually:

with open(tree_file) as f:
    content = f.read()
    # Parse Nexus format to extract all trees
    # (This requires custom parsing)
```

## File Format Support

### Newick (.nwk, .tre)

**Pros:**
- Simple, human-readable
- Wide compatibility
- Compact

**Cons:**
- Limited metadata support
- Only single tree per file typically

**Example:**
```
((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;
```

**Loading:**
```python
t = ete3.Tree("tree.nwk", format=1)
```

### Nexus (.nex, .nxs)

**Pros:**
- Structured format
- Multiple trees in one file
- Comments and metadata

**Cons:**
- More verbose
- Requires more parsing

**Example:**
```
#NEXUS
BEGIN TREES;
  TREE tree1 = (A:1,B:1)C;
END;
```

**Loading:**
```python
t = ete3.Tree("tree.nex")  # Auto-detects Nexus
```

### PhyloXML (.xml)

**Pros:**
- Rich annotation support
- XML structure
- Species and sequence data

**Cons:**
- Verbose
- Slower to parse

**Example:**
```xml
<?xml version="1.0"?>
<phyloxml>
  <phylogeny>
    <clade>
      <name>A</name>
    </clade>
  </phylogeny>
</phyloxml>
```

**Loading:**
```python
t = ete3.Tree("tree.xml")  # Auto-detects PhyloXML
```

## Handling File Paths

```python
import phylustrator as ph
from pathlib import Path

# String path
drawer.save_png("output.png")

# Path object
output_path = Path("results") / "tree.png"
drawer.save_png(output_path)

# Create directories if needed (handled automatically)
drawer.save_png("deep/nested/output.png")  # Creates directories
```

## Error Handling

### Import Errors

```python
import phylustrator as ph

try:
    drawer.save_png("tree.png")
except ImportError as e:
    print("Cairo/cairosvg not installed. Install with:")
    print("  pip install phylustrator[export]")
```

### File Not Found

```python
import ete3

try:
    t = ete3.Tree("nonexistent.nwk", format=1)
except FileNotFoundError:
    print("Tree file not found")
```

### Invalid Tree Format

```python
import ete3

try:
    t = ete3.Tree("(invalid tree", format=1)
except Exception as e:
    print(f"Invalid tree format: {e}")
```

## Tips for I/O

1. **Validate tree loading** before creating visualizations
2. **Use Path objects** for cross-platform compatibility
3. **Export SVG for editing** in vector graphics software
4. **Use PNG for publications** at 300+ DPI
5. **Backup original files** before format conversion
6. **Test small samples first** before batch processing
7. **Check file sizes** - high DPI PNGs can be large
8. **Document formats** - keep track of which format you're using

## Export Quality Settings

### Web Display (Fast, Small)
```python
drawer.save_png("web.png", dpi=72)
```

### Standard Print (Good Quality)
```python
drawer.save_png("print.png", dpi=300)
```

### Publication (High Quality)
```python
drawer.save_png("publication.png", dpi=600)
```

### Archive (Maximum Quality)
```python
drawer.save_png("archive.png", dpi=1200)
drawer.save_pdf("archive.pdf", dpi=1200)
```

## Batch Export Script

```python
import phylustrator as ph
import ete3
from pathlib import Path

def batch_visualize_trees(input_dir, output_dir, style=None):
    """
    Visualize all trees in a directory.

    Args:
        input_dir: Directory containing .nwk files
        output_dir: Directory for output files
        style: Optional TreeStyle object
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if style is None:
        style = ph.TreeStyle()

    for tree_file in sorted(input_path.glob("*.nwk")):
        try:
            # Load and visualize
            t = ete3.Tree(tree_file, format=1)
            drawer = ph.VerticalTreeDrawer(t, style=style)
            drawer.draw()
            drawer.add_leaf_names()

            # Export
            base = tree_file.stem
            drawer.save_svg(output_path / f"{base}.svg")
            drawer.save_png(output_path / f"{base}.png", dpi=300)

            print(f"✓ {tree_file.name}")
        except Exception as e:
            print(f"✗ {tree_file.name}: {e}")

# Usage
batch_visualize_trees("trees/", "output/")
```
