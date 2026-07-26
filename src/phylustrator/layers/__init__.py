"""Layers — the composable decorations added to a figure with ``+``.

Each layer is a callable ``(canvas, tree, layout, style) -> None``. Import them from here:

    from phylustrator.layers import color_branches, tip_labels, colorbar, time_axis
"""

from .clades import highlight_clade
from .coloring import color_branches
from .guides import colorbar, legend, scale_bar, time_axis
from .labels import node_labels, tip_labels
from .tracks import tip_track

__all__ = [
    "color_branches",
    "tip_labels",
    "node_labels",
    "tip_track",
    "colorbar",
    "legend",
    "time_axis",
    "scale_bar",
    "highlight_clade",
]
