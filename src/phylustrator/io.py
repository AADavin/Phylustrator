"""File format loaders for phylogenetic trees.

Supports Newick, Nexus, and PhyloXML formats via ete3.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import ete3

logger = logging.getLogger(__name__)


def read_tree(path: str | Path, format: str = "auto", **kwargs: Any) -> ete3.Tree:
    """Read a phylogenetic tree from a file.

    Args:
        path: Path to the tree file.
        format: File format - "newick", "nexus", "phyloxml", or "auto" (detect from extension).
        **kwargs: Additional arguments passed to format-specific readers.

    Returns:
        An ete3.Tree object.

    Raises:
        ValueError: If the format cannot be determined.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if format == "auto":
        suffix = path.suffix.lower()
        if suffix in {".nwk", ".newick", ".tre"}:
            format = "newick"
        elif suffix in {".nex", ".nexus"}:
            format = "nexus"
        elif suffix in {".xml", ".phyloxml"}:
            format = "phyloxml"
        else:
            raise ValueError(
                f"Could not determine format from file extension: {path.suffix}. "
                f"Specify format explicitly as 'newick', 'nexus', or 'phyloxml'."
            )

    if format == "newick":
        return read_newick(path, **kwargs)
    elif format == "nexus":
        return read_nexus(path, **kwargs)
    elif format == "phyloxml":
        return read_phyloxml(path, **kwargs)
    else:
        raise ValueError(
            f"Unknown format: {format}. Must be 'newick', 'nexus', or 'phyloxml'."
        )


def read_newick(path: str | Path, newick_format: int = 1) -> ete3.Tree:
    """Read a Newick format tree file.

    Args:
        path: Path to the Newick format tree file.
        newick_format: Newick format type (0 or 1). Format 1 includes support for
            node names and branch lengths.

    Returns:
        An ete3.Tree object.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r") as f:
        content = f.read().strip()

    logger.debug(f"Reading Newick tree from {path}")
    return ete3.Tree(content, format=newick_format)


def read_nexus(path: str | Path, tree_index: int = 0) -> ete3.Tree:
    """Read a Nexus format tree file.

    Extracts the tree block and parses as Newick.

    Args:
        path: Path to the Nexus format tree file.
        tree_index: Index of the tree to extract (0-based) if multiple trees present.

    Returns:
        An ete3.Tree object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no valid tree is found in the file.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r") as f:
        content = f.read()

    logger.debug(f"Reading Nexus tree from {path}")

    # Find the trees block (case-insensitive)
    trees_match = re.search(
        r"begin\s+trees\s*;(.*?)end\s*;",
        content,
        re.IGNORECASE | re.DOTALL,
    )

    if not trees_match:
        raise ValueError(f"No 'begin trees;' block found in {path}")

    trees_block = trees_match.group(1)

    # Extract all tree statements (format: "tree name = newick_string;")
    tree_pattern = r"tree\s+\w+\s*=\s*(.+?);"
    tree_matches = re.findall(tree_pattern, trees_block, re.IGNORECASE | re.DOTALL)

    if not tree_matches:
        raise ValueError(f"No valid tree statements found in {path}")

    if tree_index >= len(tree_matches):
        raise ValueError(
            f"Tree index {tree_index} out of range (found {len(tree_matches)} trees)"
        )

    newick_str = tree_matches[tree_index].strip()

    logger.debug(f"Extracted tree {tree_index} from Nexus file: {newick_str[:50]}...")

    # Add semicolon if not present (required by ete3)
    if not newick_str.endswith(";"):
        newick_str += ";"

    return ete3.Tree(newick_str, format=1)


def read_phyloxml(path: str | Path) -> ete3.Tree:
    """Read a PhyloXML format tree file.

    Parses the XML and builds an ete3 tree from the clade structure.

    Args:
        path: Path to the PhyloXML format tree file.

    Returns:
        An ete3.Tree object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the XML is invalid or contains no valid tree.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.debug(f"Reading PhyloXML tree from {path}")

    try:
        tree_xml = ET.parse(path)
        root = tree_xml.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in {path}: {e}")

    # PhyloXML root is typically "phyloxml" and contains "phylogeny" elements
    phylogenies = root.findall("phylogeny")
    if not phylogenies:
        phylogenies = root.findall(".//{http://www.phyloxml.org}phylogeny")

    if not phylogenies:
        raise ValueError(f"No phylogeny elements found in {path}")

    # Use the first phylogeny
    phylogeny = phylogenies[0]
    clade = phylogeny.find("clade")
    if clade is None:
        clade = phylogeny.find(".//{http://www.phyloxml.org}clade")

    if clade is None:
        raise ValueError(f"No clade element found in phylogeny in {path}")

    logger.debug("Building ete3 tree from PhyloXML clade structure")

    # Recursively build the tree from clade elements
    tree = _build_tree_from_clade(clade)

    return tree


def _build_tree_from_clade(clade_elem: ET.Element) -> ete3.Tree:
    """Recursively build an ete3 tree from a PhyloXML clade element.

    Args:
        clade_elem: An XML Element representing a clade.

    Returns:
        An ete3.Tree object.
    """
    node = ete3.Tree()

    # Extract name
    name_elem = clade_elem.find("name")
    if name_elem is None:
        name_elem = clade_elem.find(".//{http://www.phyloxml.org}name")
    if name_elem is not None:
        node.name = name_elem.text

    # Extract branch length
    branch_length_elem = clade_elem.find("branch_length")
    if branch_length_elem is None:
        branch_length_elem = clade_elem.find(
            ".//{http://www.phyloxml.org}branch_length"
        )
    if branch_length_elem is not None and branch_length_elem.text:
        try:
            node.dist = float(branch_length_elem.text)
        except ValueError:
            logger.warning(
                f"Could not parse branch_length: {branch_length_elem.text}"
            )

    # Recursively process direct child clades (immediate children only)
    for child_elem in clade_elem:
        # Check if this is a clade element (handle both with and without namespace)
        tag = child_elem.tag
        if tag.endswith("clade") or tag == "clade":
            child_tree = _build_tree_from_clade(child_elem)
            node.add_child(child_tree)

    return node
