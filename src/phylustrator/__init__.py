"""Phylustrator — a lean, composable plotter for phylogenetic trees.

Read a tree, then compose a figure from layers:

    >>> import phylustrator as ph
    >>> tree = ph.loads("((A:1,B:1)C:2,D:3)R;")
    >>> tree.leaves
    [Node('A', length=1, leaf), Node('B', length=1, leaf), Node('D', length=3, leaf)]

The plotting surface (``plot`` + layers) is being built on top of this foundation.
"""

from __future__ import annotations

from .figure import Figure, plot
from .io import dumps, loads, read, write
from .layers import (branch_events, color_branches, colorbar, highlight_clade, legend,
                     node_labels, scale_bar, time_axis, tip_labels, tip_track)
from .style import Style
from .tree import Node, Tree

__version__ = "0.1.0.dev0"

__all__ = [
    "Node", "Tree", "read", "loads", "write", "dumps",
    "plot", "Figure", "Style",
    "color_branches", "tip_labels", "node_labels", "tip_track", "branch_events",
    "colorbar", "legend", "time_axis", "scale_bar", "highlight_clade",
    "__version__",
]
