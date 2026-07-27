"""The genome data model — :class:`Gene`, :class:`Chromosome`, :class:`Genome`.

Structure only: a genome is chromosomes of ordered genes, and knows nothing about how it is drawn. The
dataclasses use ``eq=False`` so instances hash by identity (a layout keys its boxes by gene).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(eq=False)
class Gene:
    """One gene on a chromosome: its ``family`` (shared across genomes — the unit of colour and
    homology), its ``copy`` name, its ``strand`` (+1 / −1), and its ``position`` (rank order). Optional
    ``start`` / ``end`` carry nucleotide coordinates for the nucleotide resolution."""

    family: str
    copy: str = ""
    strand: int = 1
    position: int = 0
    start: float | None = None
    end: float | None = None


@dataclass(eq=False)
class Chromosome:
    id: str
    genes: list = field(default_factory=list)
    topology: str = "linear"        # "linear" | "circular"
    length: float | None = None     # nucleotide length, if known


@dataclass(eq=False)
class Genome:
    name: str
    chromosomes: list = field(default_factory=list)

    @property
    def genes(self) -> list:
        return [g for chrom in self.chromosomes for g in chrom.genes]
