"""Layouts — place genes in an abstract coordinate space, the renderer maps it to the page.

- ``linear`` — one genome, a horizontal track per chromosome. The **ordered** resolution spaces genes
  equally by rank; **nucleotide** uses their base coordinates (cladogram vs. phylogram).
- ``circular`` — the same map wrapped onto a ring, one concentric ring per chromosome (Phylustrator's
  radial). A ``linear`` plot of a circular genome *is* the linearisation.
- ``stacked`` — several genomes, one horizontal track each, for synteny comparison.

A :class:`Layout` is **self-describing**: it carries the genes it placed (draw order), each gene's
owner ``(genome, chromosome)``, the backbones to draw, and the vertical track order — so the drawer and
every layer read the layout, never the genome, and single/stacked/circular all share one path.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Layout:
    kind: str
    boxes: dict                              # linear: id(gene)->(x0,x1,y); circular: id(gene)->(a0,a1,R)
    xlim: tuple
    ylim: tuple
    rows: int = 1
    genes: list = field(default_factory=list)          # gene objects, draw order
    owner: dict = field(default_factory=dict)          # id(gene) -> (genome, chromosome)
    backbones: list = field(default_factory=list)      # [(y, x0, x1)] faint tracks (linear/stacked)
    track_order: list = field(default_factory=list)    # genomes top->bottom (synteny adjacency)
    rings: list | None = None                          # circular: centre radius per chromosome
    ring_hh: float = 0.0                               # circular: gene half-height, radius units
    equal_aspect: bool = False                         # circular keeps the rings round
    angle_start: float = 0.0                           # circular: angle (rad) of position 0
    angle_sweep: float = 0.0                           # circular: angular span (rad) of a chromosome
    totals: list = field(default_factory=list)         # circular: coordinate span per ring (bp or genes)

    def box(self, gene):
        return self.boxes[id(gene)]


def linear(genome, *, coordinates: str = "ordered", gap: float = 0.16) -> Layout:
    """Genes on one horizontal track per chromosome."""
    boxes, owner, backbones, placed = {}, {}, [], []
    for row, chrom in enumerate(genome.chromosomes):
        xs = []
        for gene in chrom.genes:
            if coordinates == "nucleotide" and gene.start is not None:
                x0, x1 = float(gene.start), float(gene.end)
            else:
                x0, x1 = gene.position + gap / 2, gene.position + 1 - gap / 2
            boxes[id(gene)] = (x0, x1, float(row))
            owner[id(gene)] = (genome, chrom)
            placed.append(gene)
            xs += [x0, x1]
        if xs:
            backbones.append((float(row), min(xs), max(xs)))
    allx = [v for b in boxes.values() for v in b[:2]] or [0.0, 1.0]
    rows = len(genome.chromosomes)
    return Layout("linear", boxes, (min(allx), max(allx)), (-0.5, rows - 0.5), rows=rows,
                  genes=placed, owner=owner, backbones=backbones, track_order=[genome])


def stacked(genomes, *, coordinates: str = "ordered", gap: float = 0.16,
            chrom_gap: float = 1.0) -> Layout:
    """Several genomes, one horizontal track each (top genome first). Chromosomes of a genome sit
    left-to-right on its track separated by ``chrom_gap``. Same-family genes line up by colour, and a
    ``synteny`` layer links them between adjacent tracks."""
    boxes, owner, backbones, placed = {}, {}, [], []
    for row, genome in enumerate(genomes):
        offset, xs = 0.0, []
        for chrom in genome.chromosomes:
            for gene in chrom.genes:
                if coordinates == "nucleotide" and gene.start is not None:
                    x0, x1 = offset + float(gene.start), offset + float(gene.end)
                else:
                    x0, x1 = offset + gene.position + gap / 2, offset + gene.position + 1 - gap / 2
                boxes[id(gene)] = (x0, x1, float(row))
                owner[id(gene)] = (genome, chrom)
                placed.append(gene)
                xs += [x0, x1]
            span = (len(chrom.genes)) if coordinates != "nucleotide" else float(chrom.length or 0.0)
            offset += span + chrom_gap
        if xs:
            backbones.append((float(row), min(xs), max(xs)))
    allx = [v for b in boxes.values() for v in b[:2]] or [0.0, 1.0]
    n = len(genomes)
    return Layout("stacked", boxes, (min(allx), max(allx)), (-0.6, n - 0.4), rows=n,
                  genes=placed, owner=owner, backbones=backbones, track_order=list(genomes))


def circular(genome, *, coordinates: str = "ordered", gap: float = 0.16,
             start_deg: float = 90.0, break_deg: float = 0.0,
             band: float = 0.34, ring_gap: float = 0.10, min_deg: float = 2.2) -> Layout:
    """Genes wrapped onto a ring, one concentric ring per chromosome (chromosome 0 outermost).

    Angles sweep **clockwise** from the top. By default the ring is closed (``break_deg=0``) so genes
    are evenly spaced all the way round; set ``break_deg`` to leave a wedge marking a linear
    chromosome's ends. ``coordinates`` chooses equal angular slots by **rank** (``"ordered"``) or
    base-proportional arcs (``"nucleotide"``)."""
    start = math.radians(start_deg)
    sweep = 2.0 * math.pi - math.radians(break_deg)
    boxes, owner, placed, rings, totals = {}, {}, [], [], []
    for k, chrom in enumerate(genome.chromosomes):
        R = 1.0 - band / 2.0 - k * (band + ring_gap)
        rings.append(R)
        n = len(chrom.genes)
        nuc = coordinates == "nucleotide" and n and chrom.genes[0].start is not None
        total = float(chrom.length or (chrom.genes[-1].end - chrom.genes[0].start) or 1.0) if nuc \
            else float(n or 1)
        totals.append(total)
        # cap the minimum arc so a gene-dense genome (a real GFF) never forces genes to overlap
        min_arc = min(math.radians(min_deg), 0.9 * sweep / max(n, 1))
        for rank, gene in enumerate(chrom.genes):        # rank, so "ordered" is even with no holes
            lo_v, hi_v = (float(gene.start), float(gene.end)) if nuc \
                else (rank + gap / 2.0, rank + 1.0 - gap / 2.0)
            a0 = start - (lo_v / total) * sweep          # clockwise: angle decreases with position
            a1 = start - (hi_v / total) * sweep
            if abs(a1 - a0) < min_arc:                   # keep tiny (nucleotide) genes visible
                mid = (a0 + a1) / 2.0
                a0, a1 = mid + min_arc / 2.0, mid - min_arc / 2.0
            boxes[id(gene)] = (a0, a1, R)
            owner[id(gene)] = (genome, chrom)
            placed.append(gene)
    hh = band * 0.11                            # thin arrow band so arrowheads read on the ring
    outer = (rings[0] if rings else 1.0) + hh
    lim = (-outer, outer)
    return Layout("circular", boxes, lim, lim, rows=len(genome.chromosomes),
                  genes=placed, owner=owner, rings=rings, ring_hh=hh, equal_aspect=True,
                  track_order=[genome], angle_start=start, angle_sweep=sweep, totals=totals)
