"""Layers — the composable decorations added to a genome figure with ``+``."""

from .genes import genes
from .guides import position_axis
from .highlight import highlight
from .synteny import synteny

__all__ = ["genes", "position_axis", "synteny", "highlight"]
