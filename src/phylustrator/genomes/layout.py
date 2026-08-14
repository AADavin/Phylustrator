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
    ring_centres: list = field(default_factory=list)   # circular: (cx, cy) per ring; empty = origin
    ring_hh: float = 0.0                               # circular: gene half-height, radius units
    ring_hh_rel: float | None = None                   # circular: if set, half-height is this × R
    centres: dict = field(default_factory=dict)        # circular: id(gene) -> (cx, cy); absent = origin
    equal_aspect: bool = False                         # circular keeps the rings round
    angle_start: float = 0.0                           # circular: angle (rad) of position 0
    angle_sweep: float = 0.0                           # circular: angular span (rad) of a chromosome
    totals: list = field(default_factory=list)         # circular: coordinate span per ring (bp or genes)

    def box(self, gene):
        return self.boxes[id(gene)]

    def centre(self, gene) -> tuple[float, float]:
        """The circle a gene is drawn on. Concentric rings all sit on the origin; a row of circles
        gives each chromosome its own centre."""
        cx, cy = self.centres.get(id(gene), (0.0, 0.0))
        return float(cx), float(cy)

    def half_height(self, R: float) -> float:
        """Gene half-thickness at radius ``R``. Concentric rings share one thickness, since they are
        all much the same size. A row scales it with the circle, so a three-gene chromosome beside a
        hundred-gene one is drawn as a small circle rather than as a blob."""
        return self.ring_hh if self.ring_hh_rel is None else self.ring_hh_rel * R

    def ring_centre(self, k: int) -> tuple[float, float]:
        return self.ring_centres[k] if self.ring_centres else (0.0, 0.0)


def linear(genome, *, coordinates: str = "ordered", gap: float = 0.16, style=None) -> Layout:
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
            chrom_gap: float = 1.0, style=None) -> Layout:
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
             start_deg: float = 90.0, break_deg: float = 0.0, scale: str | float = "each",
             arrange: str = "concentric", band: float = 0.34, ring_gap: float = 0.10,
             row_gap: float = 0.22, min_deg: float = 2.2, style=None) -> Layout:
    """Genes wrapped onto a ring, one ring per chromosome (chromosome 0 outermost / leftmost).

    Angles sweep **clockwise** from the top. By default the ring is closed (``break_deg=0``) so genes
    are evenly spaced all the way round; set ``break_deg`` to leave a wedge marking a linear
    chromosome's ends. ``coordinates`` chooses equal angular slots by **rank** (``"ordered"``) or
    base-proportional arcs (``"nucleotide"``).

    ``arrange`` places the chromosomes of a multi-chromosome genome:

    ``"concentric"`` (default) nests them as rings about one centre — the classic single-genome map.
    ``"row"`` gives each chromosome its own circle, left to right: a **karyotype**, where the
    chromosomes are separate objects rather than tracks of one map.

    ``scale`` decides what a chromosome's size means. ``"each"`` (default) draws every chromosome the
    same: a whole circle concentric, or an equal-sized circle in a row — gene *order* is then
    comparable chromosome to chromosome and size is not. ``"shared"`` draws them to one scale, taken
    from the largest: in a row the radius follows the gene count, so a gene takes the same arc
    *length* in every circle; concentric, a short chromosome draws a short arc rather than a full
    circle of enormous wedges. Pass a **number** instead to fix that reference explicitly — the same
    value across several figures puts them all on one scale, which is what comparing the karyotypes
    of different genomes needs."""
    start = math.radians(start_deg)
    sweep = 2.0 * math.pi - math.radians(break_deg)
    boxes, owner, placed, rings, totals, centres, ring_centres = {}, {}, [], [], [], {}, []
    if arrange not in ("concentric", "row"):
        raise ValueError(f"unknown arrange {arrange!r}; choose 'concentric' or 'row'")
    sizes = [len(c.genes) for c in genome.chromosomes]
    if isinstance(scale, str):
        if scale not in ("each", "shared"):
            raise ValueError(f"unknown scale {scale!r}; choose 'each', 'shared', or a number")
        reference = float(max(sizes, default=1) or 1) if scale == "shared" else 0.0
    else:
        reference = float(scale)
        if reference <= 0:
            raise ValueError(f"scale must be a positive number of genes, not {scale!r}")
    gstyle = getattr(style, "gene_style", "arrow") if style is not None else "arrow"
    frac = getattr(style, "ring_gene_frac", None) if style is not None else None
    if frac is None:                            # chunky "arrow" vs the classic thin "wedge"
        frac = 0.11 if gstyle == "wedge" else 0.30
    hh = band * frac                            # gene half-thickness
    # A row sizes each circle by its own gene count, so the thickness has to follow the circle:
    # one absolute thickness would swallow the small chromosomes whole.
    rel = hh / max(1.0 - band / 2.0, 1e-9)      # thickness as a fraction of the circle
    hh_rel = rel if arrange == "row" else None
    cursor = 0.0
    for k, chrom in enumerate(genome.chromosomes):
        n = len(chrom.genes)
        if arrange == "row":
            R = (n / reference) if reference else 1.0
            R = max(R, 1e-3)
            rings.append(R)
            cx = cursor + R * (1.0 + rel)
            cursor = cx + R * (1.0 + rel) + row_gap
            ring_centres.append((cx, 0.0))
        else:
            R = 1.0 - band / 2.0 - k * (band + ring_gap)
            rings.append(R)
            cx = 0.0
            ring_centres.append((0.0, 0.0))
        nuc = coordinates == "nucleotide" and n and chrom.genes[0].start is not None
        # concentric + a reference: the chromosome takes the fraction of the circle it is worth.
        # A row already says that with the radius, so its angles always run all the way round.
        total = float(chrom.length or (chrom.genes[-1].end - chrom.genes[0].start) or 1.0) if nuc \
            else float(reference if (reference and arrange == "concentric") else (n or 1))
        totals.append(total)
        # cap the minimum arc so a gene-dense genome (a real GFF) never forces genes to overlap.
        # The cap counts the ring's own slots: under "shared" that is the widest chromosome, so a
        # short ring is never inflated back to the width it would have had on its own.
        min_arc = min(math.radians(min_deg), 0.9 * sweep / max(n if nuc else total, 1.0))
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
            centres[id(gene)] = (cx, 0.0)
            placed.append(gene)
    if arrange == "row":
        tall = max(((R * (1.0 + rel)) for R in rings), default=1.0)
        xlim, ylim = (0.0, max(cursor - row_gap, 1e-6)), (-tall, tall)
    else:
        outer = (rings[0] if rings else 1.0) + hh
        xlim = ylim = (-outer, outer)
    return Layout("circular", boxes, xlim, ylim, rows=len(genome.chromosomes),
                  genes=placed, owner=owner, rings=rings, ring_centres=ring_centres,
                  ring_hh=hh, ring_hh_rel=hh_rel, centres=centres, equal_aspect=True,
                  track_order=[genome], angle_start=start, angle_sweep=sweep, totals=totals)
