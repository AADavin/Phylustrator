# Benchmark Trees

This directory contains randomly generated phylogenetic trees for performance testing and benchmarking of tree visualization and analysis tools.

## Files

- **tree_100.nwk** — Randomly generated balanced binary tree with 100 leaf nodes (t001...t100)
- **tree_500.nwk** — Randomly generated balanced binary tree with 500 leaf nodes (t001...t500)

## Properties

- Leaves are named with sequential identifiers (t001, t002, etc.)
- Branch lengths are randomly assigned between 0.01 and 1.0
- Trees are in Newick format with internal node labels and branch lengths (format=1)
- Generated with consistent random seed for reproducibility

## Note

These trees are **not biologically meaningful** and are intended solely for performance testing and benchmarking of phylogenetic visualization and computation tools.
