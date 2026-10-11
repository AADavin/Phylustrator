"""Reading a ZOMBI2 run: one family's alignment, from either layout the run was written in."""

import phylustrator as ph

GENE_ORDER = (
    "lineage\tchromosome\ttopology\tposition\tstrand\tfamily\tcopy\n"
    "n1\t0\tcircular\t0\t+\t0\tg10\n"
    "n2\t0\tcircular\t0\t+\t0\tg11\n"
    "n1\t0\tcircular\t1\t+\t1\tg12\n"
    "n2\t0\tcircular\t1\t+\t1\tg13\n"
)

#: one file per family, as a run writes by default
PER_FAMILY = {"fam0.fasta": ">n1_g10\nACGT\n>n2_g11\nACGA\n",
              "fam1.fasta": ">n1_g12\nTTTT\n>n2_g13\nTTTA\n"}

#: every family in one file, as a run writes with --bundle
BUNDLED = ">n1_g10 fam0\nACGT\n>n2_g11 fam0\nACGA\n>n1_g12 fam1\nTTTT\n>n2_g13 fam1\nTTTA\n"


def _run(root, bundled):
    (root / "genomes").mkdir(parents=True)
    (root / "genomes" / "gene_order.tsv").write_text(GENE_ORDER)
    (root / "sequences" / "alignments").mkdir(parents=True)
    if bundled:
        (root / "sequences" / "alignments.fasta").write_text(BUNDLED)
    else:
        for name, text in PER_FAMILY.items():
            (root / "sequences" / "alignments" / name).write_text(text)
    return root


def test_an_alignment_reads_the_same_from_either_layout(tmp_path):
    per_family = ph.zombi.read_alignment(_run(tmp_path / "a", bundled=False), 1)
    bundled = ph.zombi.read_alignment(_run(tmp_path / "b", bundled=True), 1)
    assert per_family.seqs == bundled.seqs == {"n1": "TTTT", "n2": "TTTA"}
