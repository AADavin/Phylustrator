"""The **trees** domain — plot phylogenies. ``phylustrator.trees.plot(tree) + layer + …``

    import phylustrator as ph
    tree = ph.trees.loads("((A:1,B:1):2,C:3);")
    (ph.trees.plot(tree) + ph.trees.color_branches(values) + ph.trees.time_axis()).save("tree.pdf")
"""

from __future__ import annotations

from .figure import CladeBox, Figure, Geometry, NodePos, TipPos, plot
from .io import dumps, loads, read, write
from .layers import (
                     branch_events,
                     branch_spindles,
                     color_branches,
                     color_history,
                     color_lanes,
                     colorbar,
                     highlight_clade,
                     highlight_lineage,
                     legend,
                     node_halves,
                     node_labels,
                     note,
                     ring,
                     rubberband,
                     scale_bar,
                     time_axis,
                     time_marker,
                     tip_labels,
                     tip_track,
                     title,
)
from .panels import NodePoints, node_points
from .tree import Node, Tree, lineage

__all__ = [
    "Node", "Tree", "read", "loads", "write", "dumps",
    "plot", "Figure", "Geometry", "NodePos", "TipPos", "CladeBox",
    "color_branches", "color_history", "color_lanes", "tip_labels", "node_labels", "tip_track", "ring",
    "rubberband",
    "branch_events", "branch_spindles", "node_halves", "colorbar", "legend", "note", "time_axis", "time_marker", "scale_bar", "title",
    "highlight_clade", "highlight_lineage", "lineage",
    "node_points", "NodePoints",
]
