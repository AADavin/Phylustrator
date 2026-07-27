"""The **genomes** domain — plot genomes, synteny and alignments. Same grammar as ``trees``:
``phylustrator.genomes.plot(genome) + layer + …``

    import phylustrator as ph
    G = ph.zombi.read_genomes("run")                 # or ph.genomes.read_gff("genome.gff")
    (ph.genomes.plot(G["n12"], layout="circular") + ph.genomes.genes(by="family")).save("ring.png")
"""

from __future__ import annotations

from .figure import Figure, StackFigure, plot, stack
from .genome import Chromosome, Gene, Genome
from .io import read_gff
from .layers import genes, highlight, position_axis, synteny
from .matrix import Alignment, Matrix
from .panels import alignment, heatmap

__all__ = [
    "Gene", "Chromosome", "Genome", "read_gff",
    "plot", "stack", "Figure", "StackFigure",
    "genes", "synteny", "highlight", "position_axis",
    "Matrix", "Alignment", "heatmap", "alignment",
]
