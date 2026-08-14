"""Layers — the composable decorations added to a genome figure with ``+``."""

from .genes import gene_labels, genes
from .guides import position_axis
from .highlight import highlight
from .synteny import synteny

__all__ = ["genes", "gene_labels", "position_axis", "synteny", "highlight"]
