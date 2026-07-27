"""Read a **ZOMBI2 run** into Phylustrator's generic objects — the one ZOMBI-aware module.

Everything here understands ZOMBI2's own file layout and formats and returns plain
:class:`~phylustrator.trees.Tree`, :class:`~phylustrator.genomes.Genome`,
:class:`~phylustrator.genomes.Matrix` and :class:`~phylustrator.genomes.Alignment` objects, so the rest
of the library stays format-agnostic.

    import phylustrator as ph
    G     = ph.zombi.read_genomes("run")          # gene_order.tsv / blocks.tsv -> {lineage: Genome}
    prof  = ph.zombi.read_profiles("run")         # profiles.tsv -> Matrix (genomes x families)
    aln   = ph.zombi.read_alignment("run", 27)    # one family's alignment, keyed by genome
    evs   = ph.zombi.read_events("run")            # genome_events.tsv rows
    tree  = ph.zombi.read_species_tree("run")     # species/species_extant.nwk -> Tree
"""

from __future__ import annotations

import csv
from pathlib import Path

from .genomes.genome import Chromosome, Gene, Genome
from .genomes.matrix import Alignment, Matrix
from .trees.io import read as _read_newick

__all__ = ["read_genomes", "read_profiles", "read_alignment", "read_events", "read_species_tree"]


def _genomes_dir(run) -> Path:
    p = Path(run)
    if p.is_file():
        return p.parent
    return p / "genomes" if (p / "genomes").is_dir() else p


def read_genomes(run) -> dict:
    """A ZOMBI2 genomes run into ``{lineage: Genome}`` — ``gene_order.tsv`` (ordered/family) or
    ``blocks.tsv`` (nucleotide, real bp coordinates), whichever is present."""
    path = Path(run)
    if path.is_dir():
        gdir = _genomes_dir(path)
        if (gdir / "gene_order.tsv").exists():
            path = gdir / "gene_order.tsv"
        elif (gdir / "blocks.tsv").exists():
            path = gdir / "blocks.tsv"
        else:
            raise FileNotFoundError(f"no gene_order.tsv or blocks.tsv under {run}")
    return _read_blocks(path) if path.name == "blocks.tsv" else _read_gene_order(path)


def _read_gene_order(path: Path) -> dict:
    lines = path.read_text().strip().splitlines()
    col = {name: i for i, name in enumerate(lines[0].split("\t"))}
    per: dict[str, dict[str, list]] = {}
    for line in lines[1:]:
        r = line.split("\t")
        gene = Gene(family=r[col["family"]], copy=r[col["copy"]],
                    strand=int(r[col["strand"]]), position=int(r[col["position"]]))
        per.setdefault(r[col["lineage"]], {}).setdefault(r[col["chromosome"]], []).append(gene)
    genomes = {}
    for lineage, chroms in per.items():
        chromosomes = []
        for cid, genes in chroms.items():
            genes.sort(key=lambda g: g.position)
            chromosomes.append(Chromosome(id=cid, genes=genes))
        genomes[lineage] = Genome(name=lineage, chromosomes=chromosomes)
    return genomes


def _read_blocks(path: Path) -> dict:
    per: dict[str, dict[str, dict]] = {}
    with open(path) as handle:
        for r in csv.DictReader(handle, delimiter="\t"):
            lin, cid = r["lineage"], r["chromosome"]
            chrom = per.setdefault(lin, {}).setdefault(cid, {"genes": [], "length": 0.0})
            chrom["length"] = max(chrom["length"], float(r["end"]))
            if r.get("gene") and r["gene"] != "0":
                chrom["genes"].append(Gene(family=r["gene"], copy=r.get("copy", ""),
                                           strand=int(r["strand"]),
                                           start=float(r["start"]), end=float(r["end"])))
    genomes = {}
    for lineage, chroms in per.items():
        chromosomes = []
        for cid, info in chroms.items():
            genes = sorted(info["genes"], key=lambda g: g.start)
            for rank, g in enumerate(genes):
                g.position = rank
            chromosomes.append(Chromosome(id=cid, genes=genes, topology="circular",
                                          length=info["length"]))
        genomes[lineage] = Genome(name=lineage, chromosomes=chromosomes)
    return genomes


def read_profiles(run, *, transpose: bool = True) -> Matrix:
    """``profiles.tsv`` (``family`` column then one column per genome) into a :class:`Matrix`. By
    default **genomes × families** (rows = genomes, aligning to a species tree)."""
    gdir = _genomes_dir(run)
    f = gdir / "profiles.tsv" if gdir.is_dir() else Path(run)
    with open(f) as handle:
        reader = csv.reader(handle, delimiter="\t")
        genomes = next(reader)[1:]
        fams, grid = [], []
        for line in reader:
            fams.append(line[0])
            grid.append([float(v) for v in line[1:]])
    if transpose:
        values = [[grid[j][i] for j in range(len(fams))] for i in range(len(genomes))]
        return Matrix(rows=genomes, cols=fams, values=values)
    return Matrix(rows=fams, cols=genomes, values=grid)


def read_alignment(run, family, *, kind: str = "nt") -> Alignment:
    """One gene ``family``'s alignment, **keyed by genome**: each gene-copy header (``g1200``) is mapped
    back to its genome (``n12``) via ``gene_order.tsv``, so rows line up with a species tree."""
    run = Path(run)
    gdir = _genomes_dir(run)
    adir = run / "sequences" / "alignments"
    if not adir.is_dir():
        adir = run / "alignments"
    with open(gdir / "gene_order.tsv") as handle:
        copy2genome = {r["copy"]: r["lineage"] for r in csv.DictReader(handle, delimiter="\t")}
    seqs, name = {}, None
    raw: dict[str, list] = {}
    for line in open(adir / f"fam{family}.fasta"):
        line = line.rstrip("\n")
        if line.startswith(">"):
            name = line[1:].strip()
            raw[name] = []
        elif name is not None:
            raw[name].append(line.strip())
    seqs = {copy2genome.get(copy, copy): "".join(v) for copy, v in raw.items()}
    return Alignment(rows=list(seqs), seqs=seqs, kind=kind)


def read_events(run) -> list:
    """``genome_events.tsv`` as a list of row dicts (time, kind, lineage, family, donor, recipient, …)."""
    gdir = _genomes_dir(run)
    with open(gdir / "genome_events.tsv") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_species_tree(run, *, which: str = "extant"):
    """The species tree (``species/species_<which>.nwk``) as a :class:`~phylustrator.trees.Tree`."""
    run = Path(run)
    path = run / "species" / f"species_{which}.nwk"
    return _read_newick(path if path.exists() else run)
