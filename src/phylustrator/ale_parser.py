import pandas as pd
import ete3
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ALEData:
    """
    Stores parsed information from an ALE output file (.uml_rec).
    """
    species_tree_newick: str
    species_tree: ete3.Tree
    log_likelihood: float
    rates: Dict[str, float]  # {Duplications, Transfers, Losses}
    gene_trees: List[str]  # List of Newick strings
    totals: Dict[str, float]  # {Duplications, Transfers, Losses, Speciations}
    branch_stats: pd.DataFrame  # Columns: [S_node, Duplications, Transfers, Losses, Originations, copies]


def parse_ale_file(filepath: str) -> ALEData:
    """
    Parses an ALE .uml_rec file and returns an ALEData object.
    """
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    # 1. Parse Reference Species Tree (First Line)
    # We load it with format=1 to ensure we keep internal node names/IDs.
    tree_line = lines[1].split("\t")[-1]
    species_tree = ete3.Tree(tree_line, format=1)

    # 2. Parse Rates & Likelihood
    # Look for ">logl:"
    logl = 0.0
    rates = {}

    # We iterate through lines to find markers
    i = 1
    while i < len(lines):
        line = lines[i]

        if line.startswith(">logl"):
            # Example: >logl: -1136.19
            logl = float(line.split(":")[1].strip())

        elif line.startswith("rate of"):
            # Skip header, next line is "ML ..."
            pass

        elif line.startswith("ML"):
            # Example: ML      0.154163        0.0712109       0.643975
            parts = line.split()
            # parts[0] is 'ML'
            rates = {
                "Duplications": float(parts[1]),
                "Transfers": float(parts[2]),
                "Losses": float(parts[3])
            }

        elif "reconciled G-s:" in line:
            # Example: 100 reconciled G-s:
            # The next N lines are gene trees until we hit "# of"
            break

        i += 1

    # 3. Parse Reconciled Gene Trees
    # -------------------------------------------------------
    # We are currently at the "100 reconciled G-s:" line.
    i += 1  # Move to first gene tree
    gene_trees = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("# of"):
            # We hit the Totals section header
            break
        gene_trees.append(line)
        i += 1

    # 4. Parse Totals
    i += 1  # Move to 'Total' line
    totals_line = lines[i]
    t_parts = totals_line.split()
    totals = {
        "Duplications": float(t_parts[1]),
        "Transfers": float(t_parts[2]),
        "Losses": float(t_parts[3]),
        "Speciations": float(t_parts[4])
    }

    # 5. Parse Branch Stats Table
    table_start_index = -1
    for idx in range(i, len(lines)):
        if "S_node" in lines[idx] or ("Duplications" in lines[idx] and "copies" in lines[idx]):
            table_start_index = idx + 1
            break

    # Parse the table data
    data_rows = []
    if table_start_index != -1:
        for idx in range(table_start_index, len(lines)):
            line = lines[idx]
            # ALE table rows are tab or space separated
            cols = line.split()
            if not cols: continue

            # S_node usually is an integer, but keep as str to match tree node names safely
            row = {
                "S_node": cols[0],
                "name": cols[1],
                "Duplications": float(cols[2]),
                "Transfers": float(cols[3]),
                "Losses": float(cols[4]),
                "Originations": float(cols[5]),
                "copies": float(cols[6])
            }
            data_rows.append(row)

    df = pd.DataFrame(data_rows)

    return ALEData(
        species_tree_newick=tree_line,
        species_tree=species_tree,
        log_likelihood=logl,
        rates=rates,
        gene_trees=gene_trees,
        totals=totals,
        branch_stats=df
    )
