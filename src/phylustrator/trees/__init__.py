"""The **trees** domain — plot phylogenies. ``phylustrator.trees.plot(tree) + layer + …``

    import phylustrator as ph
    tree = ph.trees.loads("((A:1,B:1):2,C:3);")
    (ph.trees.plot(tree) + ph.trees.color_branches(values) + ph.trees.time_axis()).save("tree.pdf")
"""

from __future__ import annotations

from .figure import Figure, Geometry, TipPos, plot
from .io import dumps, loads, read, write
from .layers import (branch_events, color_branches, color_history, color_lanes, colorbar,
                     highlight_clade, legend, node_labels, note, scale_bar, time_axis, time_marker,
                     tip_labels, tip_track)
from .tree import Node, Tree

__all__ = [
    "Node", "Tree", "read", "loads", "write", "dumps",
    "plot", "Figure", "Geometry", "TipPos",
    "color_branches", "color_history", "color_lanes", "tip_labels", "node_labels", "tip_track",
    "branch_events", "colorbar", "legend", "note", "time_axis", "time_marker", "scale_bar",
    "highlight_clade",
]
