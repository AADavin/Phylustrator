# File Formats Guide

This guide covers the phylogenetic file formats supported by Phylustrator through ete3.

## Supported Formats

Phylustrator uses ete3 for tree parsing, which supports multiple standard phylogenetic file formats:

- **Newick** (NHX): Simple text format with nested parentheses
- **Nexus**: Structured format with metadata
- **PhyloXML**: XML-based format with rich annotations

## Newick Format

Newick is the most common and simplest phylogenetic format.

### Basic Newick Syntax

```
(A:1,B:1)C;                    # Simple tree
((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;  # Nested tree
```

### Newick Components

- `A, B, C`: Leaf names
- `:1`: Branch lengths
- `()`: Grouping (clade)
- `;`: Tree terminator

### Loading Newick Trees

```python
import ete3
import phylustrator as ph

# From string
t = ete3.Tree("(A:1,B:1)C;", format=1)

# From file
with open("tree.nwk") as f:
    t = ete3.Tree(f.readline(), format=1)

# Render
drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.save_svg("tree.svg")
```

### Newick Format Parameter

The `format` parameter controls parsing:

```python
# Format 0: No names or distances
t = ete3.Tree("(,());", format=0)

# Format 1: Names and distances (standard)
t = ete3.Tree("(A:1.0,B:2.0)C;", format=1)

# Format 2: Names and distances, but different structure
t = ete3.Tree("(A:1.0,B:2.0);", format=2)
```

Use `format=1` for most cases (includes node names and branch lengths).

### Example Newick Files

Simple tree:
```
((human:0.1,chimp:0.1):0.2,(dog:0.2,cat:0.2):0.1);
```

Tree with root:
```
(((A:1,B:1)AB:1,(C:1,D:1)CD:1)ABCD:1)root;
```

Large tree:
```
(((((A:0.1,B:0.2)x:0.1,(C:0.15,D:0.25)y:0.05)z:0.2,
E:0.5)w:0.1,(F:0.3,G:0.4)v:0.2)u:0.1);
```

## Nexus Format

Nexus is a more structured format with explicit metadata.

### Nexus Syntax

```
#NEXUS
BEGIN TAXA;
  NTAX=4;
  TAXLABELS A B C D;
END;

BEGIN TREES;
  TREE tree1 = (A:1,B:1,(C:1,D:1):1);
END;
```

### Loading Nexus Trees

```python
import ete3
import phylustrator as ph

# From file
t = ete3.Tree("tree.nex")

# Render
drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.save_svg("tree.svg")
```

### Nexus Advantages

- Multiple trees in single file
- Metadata and comments
- Structured blocks
- Character data included

### Example Nexus File

```
#NEXUS
BEGIN TAXA;
  NTAX=5;
  TAXLABELS human chimp gorilla orangutan macaque;
END;

BEGIN TREES;
  TREE primates = ((human:0.1,chimp:0.1)hominoid:0.2,(gorilla:0.15,orangutan:0.15)pongid:0.15,macaque:0.5);
END;
```

## PhyloXML Format

PhyloXML is an XML-based format that supports rich annotations.

### PhyloXML Syntax

```xml
<?xml version="1.0"?>
<phyloxml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <phylogeny rooted="true">
    <clade>
      <name>root</name>
      <clade>
        <name>A</name>
        <branch_length>1.0</branch_length>
      </clade>
      <clade>
        <name>B</name>
        <branch_length>1.0</branch_length>
      </clade>
    </clade>
  </phylogeny>
</phyloxml>
```

### Loading PhyloXML Trees

```python
import ete3
import phylustrator as ph

# From file
t = ete3.Tree("tree.xml")

# Render
drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.save_svg("tree.svg")
```

### PhyloXML Features

- Node and clade annotations
- Species information
- Sequence data
- Confidence values
- Event information

### Example PhyloXML File

```xml
<?xml version="1.0"?>
<phyloxml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <phylogeny rooted="true" branch_length_unit="substitutions">
    <description>Primate phylogeny</description>
    <clade>
      <name>root</name>
      <clade>
        <name>Hominoidea</name>
        <branch_length>1.0</branch_length>
        <clade>
          <name>human</name>
          <branch_length>0.1</branch_length>
          <taxonomy>
            <scientific_name>Homo sapiens</scientific_name>
          </taxonomy>
        </clade>
        <clade>
          <name>chimp</name>
          <branch_length>0.1</branch_length>
          <taxonomy>
            <scientific_name>Pan troglodytes</scientific_name>
          </taxonomy>
        </clade>
      </clade>
      <clade>
        <name>macaque</name>
        <branch_length>1.0</branch_length>
        <taxonomy>
          <scientific_name>Macaca mulatta</scientific_name>
        </taxonomy>
      </clade>
    </clade>
  </phylogeny>
</phyloxml>
```

## Creating Newick Strings Programmatically

Build trees from data:

```python
import ete3

# Simple binary tree
newick = "((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;"
t = ete3.Tree(newick, format=1)

# From nested list (hierarchical data)
def build_newick(name, children, length=1.0):
    if not children:
        return f"{name}:{length}"
    child_str = ",".join(build_newick(c[0], c[1], c[2] if len(c) > 2 else 1.0)
                         for c in children)
    return f"({child_str}){name}:{length}" if name else f"({child_str}):"

# Example: Create star tree with A, B, C, D
star_tree = "(A:1,B:1,C:1,D:1)root;"
t = ete3.Tree(star_tree, format=1)
```

## Working with Tree Files

### Reading from File

```python
# Read single tree
with open("phylogeny.nwk") as f:
    content = f.read().strip()
    t = ete3.Tree(content, format=1)

# Read multiple trees
with open("trees.nwk") as f:
    for line in f:
        if line.strip():
            t = ete3.Tree(line, format=1)
            # Process tree
```

### Writing Trees

```python
import ete3
import phylustrator as ph

t = ete3.Tree("(A:1,B:1)C;", format=1)

# Write to Newick file
with open("output.nwk", "w") as f:
    f.write(t.write(format=1))

# Save phylustrator visualization
drawer = ph.VerticalTreeDrawer(t)
drawer.draw()
drawer.save_svg("tree.svg")
drawer.save_png("tree.png", dpi=300)
```

## Format Conversion

Convert between formats:

```python
import ete3

# Read from one format, write to another
t = ete3.Tree("tree.nex")  # Read Nexus

# Write as Newick
with open("output.nwk", "w") as f:
    f.write(t.write(format=1))

# Write as PhyloXML
with open("output.xml", "w") as f:
    f.write(t.write(format="phyloxml"))
```

## Common Issues and Solutions

### Invalid Newick String

```
Error: Malformed newick tree...
```

Solution: Check for:
- Missing semicolon at end
- Unmatched parentheses
- Invalid characters in names (use only alphanumeric)

### Format Parameter

```python
# Wrong
t = ete3.Tree("(A:1,B:1)C;")  # Missing format parameter

# Correct
t = ete3.Tree("(A:1,B:1)C;", format=1)
```

### Unicode in Names

```python
# Some formats struggle with Unicode
# Use ASCII names when possible
t = ete3.Tree("(species_A:1,species_B:1)root;", format=1)

# Or use format 0 if names aren't needed
t = ete3.Tree("(,:1);", format=0)
```

## Example Workflows

### Load and Visualize

```python
import ete3
import phylustrator as ph

# Load tree from file
t = ete3.Tree("my_tree.nwk", format=1)

# Create visualization
style = ph.TreeStyle(width=800, height=600)
drawer = ph.VerticalTreeDrawer(t, style=style)
drawer.draw()
drawer.add_leaf_names()

# Save in multiple formats
drawer.save_svg("tree.svg")
drawer.save_png("tree.png", dpi=300)
```

### Batch Process Multiple Trees

```python
import ete3
import phylustrator as ph
from pathlib import Path

input_dir = Path("trees/")
output_dir = Path("visualizations/")
output_dir.mkdir(exist_ok=True)

# Process all Newick files
for tree_file in input_dir.glob("*.nwk"):
    t = ete3.Tree(tree_file, format=1)

    drawer = ph.VerticalTreeDrawer(t)
    drawer.draw()
    drawer.add_leaf_names()

    output_file = output_dir / f"{tree_file.stem}.png"
    drawer.save_png(str(output_file), dpi=300)
    print(f"Saved {output_file}")
```

### Extract and Modify Trees

```python
import ete3
import phylustrator as ph

t = ete3.Tree("((A:1,B:1)AB:1,(C:1,D:1)CD:1)root;", format=1)

# Get subtree
subtree = t.get_common_ancestor("A", "B")

# Visualize subtree only
drawer = ph.VerticalTreeDrawer(subtree)
drawer.draw()
drawer.save_svg("subtree.svg")

# Write subtree
with open("subtree.nwk", "w") as f:
    f.write(subtree.write(format=1))
```

## Best Practices

1. **Use format=1 for Newick**: Includes names and distances
2. **Validate formats**: Always test tree loading before processing
3. **Document source**: Keep track of which format you're using
4. **Backup originals**: Keep original files before conversion
5. **Use appropriate format**: Choose based on your data needs
6. **Check Unicode**: Verify non-ASCII characters are handled correctly
