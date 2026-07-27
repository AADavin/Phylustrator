"""Tabular data to show beside a tree — labelled grids.

A :class:`Matrix` is rows × columns of numbers with labels on both (e.g. a gene-family profile:
genomes × families). An :class:`Alignment` is rows × sites of residues. Both are consumed by the
``heatmap`` / ``alignment`` panels and placed by :func:`~phylustrator.compose.beside`. Readers that
build these from a ZOMBI2 run live in :mod:`phylustrator.zombi`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Matrix:
    rows: list          # row labels (e.g. genomes / tree tips)
    cols: list          # column labels (e.g. families)
    values: list        # values[i][j] aligned to rows[i], cols[j]

    def row(self, label):
        return self.values[self.rows.index(label)]


@dataclass
class Alignment:
    rows: list          # row labels (e.g. genomes / tree tips)
    seqs: dict          # label -> sequence string
    kind: str = "nt"    # "nt" | "aa"

    @property
    def length(self) -> int:
        return max((len(s) for s in self.seqs.values()), default=0)
