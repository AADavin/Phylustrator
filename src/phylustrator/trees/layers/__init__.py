"""Layers — the composable decorations added to a figure with ``+``.

Each layer is a callable ``(canvas, tree, layout, style) -> None``. Import them from here:

    from phylustrator.layers import color_branches, tip_labels, colorbar, time_axis
"""

from .clades import highlight_clade
from .coloring import color_branches, color_history, color_lanes
from .events import branch_events
from .guides import colorbar, legend, note, scale_bar, time_axis, time_marker
from .labels import node_labels, tip_labels
from .tracks import ring, rubberband, tip_track

__all__ = [
    "color_branches",
    "color_history",
    "color_lanes",
    "tip_labels",
    "node_labels",
    "tip_track",
    "ring",
    "rubberband",
    "branch_events",
    "colorbar",
    "legend",
    "note",
    "time_axis",
    "time_marker",
    "scale_bar",
    "highlight_clade",
]
