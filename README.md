# **Phylustrator**

**Phylustrator** is a Python library for rendering highly customizable phylogenetic trees. It is built on top of ete3 and drawsvg.

## **Installation**

Phylustrator is pure Python, but it relies on **Cairo** for high-resolution image export (PNG/PDF).

### **Step 1: Install System Libraries (Only for PNG/PDF)**

*If you only need SVG output, you can skip this\!*

* **Conda (Recommended):**  
  conda install \-c conda-forge cairo pango

* **Ubuntu/Debian:** sudo apt-get install libcairo2-dev  
* **macOS (Homebrew):** brew install cairo

### **Step 2: Install Phylustrator**

You can install the latest version directly from GitHub using pip:

pip install git+\[https://github.com/aadria/Phylustrator.git\](https://github.com/aadria/Phylustrator.git)

## **Quick Start Example**

This example demonstrates how to create a complex vertical tree with trait mapping, markers, heatmaps, and legends.

import ete3  
import phylustrator as ph  
import random

\# 1\. Load your tree  
\# Ensure your Newick file is formatted correctly (format=1 is standard for trees with names and lengths)  
with open("../examples/data/basic/tree.nwk") as f:  
    t \= ete3.Tree(f.readline(), format=1)

\# 2\. Define your style  
\# Control dimensions, stroke widths, and default sizes here  
my\_style \= ph.TreeStyle(  
    width=600,  
    height=600,  
    leaf\_r=0,               \# Radius of leaf tips (0 to hide)  
    node\_r=0,               \# Radius of internal nodes (0 to hide)  
    branch\_stroke\_width=2,  \# Thickness of branches  
    branch\_color="black",  
    font\_size=12,  
    font\_family="Arial",  
)

\# 3\. Initialize the Drawer  
v \= ph.VerticalTreeDrawer(t, style=my\_style)

\# \--- BASE TREE COLORING \---  
\# Find a target clade (common ancestor of A and D)  
target \= t.get\_common\_ancestor("A", "D") 

\# Create a color mapping: default blue, target clade green  
node\_colors \= {n: "blue" for n in t.traverse()}  
for n in target.traverse():  
    node\_colors\[n\] \= "green"

\# Draw the base tree structure  
v.draw(branch2color=node\_colors)  
v.add\_leaf\_names()

\# \--- ADDING MARKERS \---  
\# Add triangle shapes next to leaves A, B, C, D  
v.add\_leaf\_shapes(  
    leaves=\["A", "B", "C", "D"\],  
    shape="triangle",  
    fill="blue",  
    r=5,                    \# Radius of the shape  
    stroke="black",  
    stroke\_width=1,  
    offset=35,              \# Distance from the leaf tip  
)

\# Add rotated square shapes for J and M  
v.add\_leaf\_shapes(  
    leaves=\["J", "M"\],  
    shape="square",  
    fill="orange",  
    r=4,                      
    stroke="black",  
    stroke\_width=1,  
    offset=35,  
    rotation=45,  
)

\# Add events along branch 'K' at specific positions (0.0=start, 1.0=end)  
events \= \[  
    {"branch": "K", "where": 0.2, "shape": "circle", "fill": "red", "r": 7},          
    {"branch": "K", "where": 0.5, "shape": "circle", "fill": "orange", "r": 7},       
    {"branch": "K", "where": 0.8, "shape": "circle", "fill": "darkgreen", "r": 7},    
\]  
v.add\_branch\_shapes(events)

\# \--- HIGHLIGHTING \---  
\# Highlight a clade with a shaded background box  
target\_clade \= t.get\_common\_ancestor("E", "G")   
v.highlight\_clade(target\_clade, color="orange", opacity=0.4)

\# Highlight specific branches  
target\_branch \= t.get\_common\_ancestor("P", "Q")   
v.highlight\_branch(target\_branch, color="blue", stroke\_width=5)

\# Apply a gradient to a branch  
target\_grad \= t.get\_common\_ancestor("H", "J")   
v.gradient\_branch(target\_grad, colors=("purple", "red"), stroke\_width=6)

\# \--- TRANSFERS \---  
\# Plot curved links between lineages  
transfer\_data \= \[  
    {"from": "E", "to": "A", "freq": 1.0},  
\]

v.plot\_transfers(  
    transfer\_data,  
    curve\_type="C",         \# Cubic curve  
    stroke\_width=3,           
    opacity=0.6,  
    gradient\_colors=("purple", "orange")   
)

\# \--- AXES & HEATMAPS \---  
\# Add a time axis at the bottom  
v.add\_time\_axis(  
    ticks=\[0, 0.5, 1.0, 1.5, 2.0, 2.5\],   
    label="Time",   
    y\_offset=20    
)

\# Add heatmaps (metadata columns) next to the tree  
\# Column 1: Expression (Blue)  
data\_col1 \= {leaf.name: random.uniform(0, 1\) for leaf in t.get\_leaves()}  
v.add\_heatmap(  
    data\_col1,  
    width=15,  
    offset=50,  
    low\_color="white",  
    high\_color="blue",  
    border\_color="black",  
    border\_width=0.5  
)

\# Column 2: Enrichment (Red)  
data\_col2 \= {leaf.name: random.uniform(0, 100\) for leaf in t.get\_leaves()}  
v.add\_heatmap(  
    data\_col2,  
    width=15,  
    offset=70,  
    low\_color="\#fff5f0",  
    high\_color="\#67000d",  
    border\_color="black",  
    border\_width=0.5  
)

\# \--- LEGENDS \---  
v.add\_categorical\_legend(  
    palette={"Blue": "blue", "Green": "green"},   
    title="Lineage type",  
    x=-280, y=-280  \# Top-left area  
)

v.add\_transfer\_legend(  
    colors=("purple", "orange"),  
    x=-150, y=-280    
)

v.add\_color\_bar(  
    low\_color="white",   
    high\_color="blue",   
    vmin=0, vmax=1,   
    title="Expression",  
    x=160, y=-250  
)

\# Display or Save  
\# v.d  \# Display in Jupyter  
v.save\_png("my\_phylogeny.png", dpi=300)

\!

$$Phylustrator Example$$  
(https://github.com/AADavin/Phylustrator/blob/main/examples/figures/vertical\_tree.png)

## ** API Overview**

### **TreeStyle**

Controls the global appearance of the plot.

* width, height: Canvas dimensions.  
* leaf\_r, node\_r: Radius of leaf/node markers (0 to hide).  
* branch\_stroke\_width: Thickness of tree branches.  
* mode: "r" (radial) or "c" (circular) \- *RadialDrawer only*.

### **Drawers (VerticalTreeDrawer, RadialTreeDrawer)**

The main classes for generating plots.

* **draw()**: Renders the tree structure.  
* **add\_leaf\_shapes()**: Adds markers (circle, square, triangle) to tips.  
* **add\_heatmap()**: Adds data columns/rings.  
* **plot\_transfers()**: Draws HGT links.  
* **highlight\_clade()**: Adds background shading.  
* **save\_png(path, dpi=300)**: Exports high-quality images.

## **License**

This project is licensed under the MIT License \- see the LICENSE file for details.