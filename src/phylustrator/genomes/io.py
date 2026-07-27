"""General genome input — reading a **GFF3** into :class:`~phylustrator.genomes.genome.Genome`
objects. Reading a ZOMBI2 *run* (its own file formats) lives in :mod:`phylustrator.zombi`.
"""

from __future__ import annotations

from pathlib import Path

from .genome import Chromosome, Gene, Genome

__all__ = ["read_gff"]


def read_gff(source: str | Path, *, feature: str = "gene", name_attr: str = "locus_tag") -> dict:
    """Read a **GFF3** into ``{seqid: Genome}`` — real genes at their real base coordinates.

    Genes are the rows whose type is ``feature`` (default ``"gene"``); each gets its ``start`` / ``end``
    (bp), ``strand``, and a family/name from ``name_attr`` in column 9 (falling back to ``Name`` / ``ID``).
    A ``##sequence-region`` line or a ``region`` feature sets the replicon length and circularity."""
    path = Path(source)
    per: dict[str, dict] = {}
    for raw in path.read_text().splitlines():
        if raw.startswith("##sequence-region"):
            p = raw.split()
            if len(p) >= 4:
                per.setdefault(p[1], _blank())["length"] = float(p[3])
            continue
        if raw.startswith("#") or not raw.strip():
            continue
        c = raw.split("\t")
        if len(c) < 9:
            continue
        seqid, _src, ftype, start, end, _score, strand, _phase, attrs = c[:9]
        info = per.setdefault(seqid, _blank())
        if ftype == "region" and "Is_circular=true" in attrs:
            info["circular"] = True
        if ftype != feature:
            continue
        a = dict(kv.split("=", 1) for kv in attrs.split(";") if "=" in kv)
        fam = a.get(name_attr) or a.get("Name") or a.get("ID") or ""
        info["genes"].append(Gene(family=fam, strand=(-1 if strand == "-" else 1),
                                  start=float(start), end=float(end)))
        info["length"] = max(info["length"], float(end))
    genomes = {}
    for seqid, info in per.items():
        genes = sorted(info["genes"], key=lambda g: g.start)
        for rank, g in enumerate(genes):
            g.position = rank
        topo = "circular" if info["circular"] else "linear"
        genomes[seqid] = Genome(name=seqid, chromosomes=[
            Chromosome(id=seqid, genes=genes, topology=topo, length=info["length"])])
    return genomes


def _blank() -> dict:
    return {"genes": [], "length": 0.0, "circular": False}
