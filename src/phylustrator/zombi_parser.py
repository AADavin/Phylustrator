"""
Zombi parser for Phylustrator.

This module parses a Zombi simulation folder with (at least) the following structure:

<root>/
  T/
    CompleteTree.nwk (or SpeciesTree.nwk / ExtantTree.nwk)
    Events.tsv
    Lengths.tsv (optional)
  G/
    Gene_families/
      <family>_events.tsv
    Events_per_branch/ (optional, not used here)
    ...

Key points:
- We parse T/Events.tsv to infer the stem above the root (origin -> root speciation).
  Zombi can have a non-zero stem, meaning the "root" is not necessarily at time 0.
- We optionally add an explicit Origin node above the root with dist=stem_length.
- We annotate each node with time_from_origin (cumulative branch length).
- We parse all gene-family event files into a single DataFrame.
- We provide a helper to map gene events to branch-marker specs for plotting.

NOTE:
- Transfers: Zombi emits LT/AT (leaving/arriving) events that are simultaneous. This
  parser collects them in `transfers` but does not yet pair them into arcs.
  We can add pairing once we confirm LT/AT token formats in your data.
"""

from __future__ import annotations

import os
import glob
import csv
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import ete3
import pandas as pd


@dataclass
class ZombiData:
    """
    Parsed Zombi data.

    Attributes
    ----------
    species_tree
        ETE3 Tree representing the species tree (possibly with an added Origin node).
    species_events
        DataFrame of species-tree timeline events from T/Events.tsv.
        Columns: time, event, nodes
    gene_events
        DataFrame of gene-family events from G/Gene_families/*_events.tsv.
        Columns: family, time, event, nodes, node
    transfers
        Subset of gene_events with event in {LT, AT, T} (raw, unpaired).
    origin_time
        Inferred time of "O Root" event in T/Events.tsv (if present), else 0.
    stem_length
        Inferred stem length above Root (first "S Root..." time - origin_time), else 0.
    """

    species_tree: ete3.Tree
    species_events: pd.DataFrame
    gene_events: pd.DataFrame
    transfers: pd.DataFrame
    origin_time: float = 0.0
    stem_length: float = 0.0


class ZombiParser:
    """
    Parser for Zombi output folders.

    Parameters
    ----------
    root_folder
        Path to a Zombi run folder containing T/ and G/ subfolders, or a direct path to T/.
    """

    def __init__(self, root_folder: str):
        self.root = root_folder
        self.t_folder = os.path.join(self.root, "T")
        self.g_folder = os.path.join(self.root, "G", "Gene_families")

        # If user points directly to T/
        if not os.path.exists(self.t_folder) and os.path.basename(root_folder) == "T":
            self.t_folder = root_folder
            self.g_folder = os.path.join(os.path.dirname(root_folder), "G", "Gene_families")

    def parse(self) -> ZombiData:
        # 1) Load species tree (prefer CompleteTree)
        species_tree = self._load_species_tree()

        # 2) Parse T/Events.tsv (stem / origin)
        species_events, origin_time, stem_length = self._parse_species_events()

        # 3) Add explicit Origin stem above root (if stem_length > 0)
        if stem_length > 0:
            species_tree = self._add_origin_stem(species_tree, stem_length)

        # 4) Annotate each node with cumulative time_from_origin (by dist)
        self._annotate_time_from_origin(species_tree)

        # 5) Parse gene-family events from G/Gene_families/*_events.tsv
        gene_events = self._parse_gene_family_events()

        # 6) Extract raw transfer records (T)
        transfers = self._extract_species_transfers(gene_events)


        return ZombiData(
            species_tree=species_tree,
            species_events=species_events,
            gene_events=gene_events,
            transfers=transfers,
            origin_time=origin_time,
            stem_length=stem_length,
        )

    # ------------------------
    # Species tree loading
    # ------------------------
    def _load_species_tree(self) -> ete3.Tree:
        tree_files = ["CompleteTree.nwk", "SpeciesTree.nwk", "ExtantTree.nwk"]
        for name in tree_files:
            path = os.path.join(self.t_folder, name)
            if os.path.exists(path):
                return ete3.Tree(path, format=1)
        raise FileNotFoundError(
            f"No species tree found in {self.t_folder} (expected one of {tree_files})"
        )

    # ------------------------
    # Species events (T/Events.tsv)
    # ------------------------
    def _parse_species_events(self) -> Tuple[pd.DataFrame, float, float]:
        """
        Parse T/Events.tsv and infer origin_time + stem_length.

        We infer:
          - origin_time: time of event 'O' for Root (if present)
          - stem_length: first speciation event involving Root minus origin_time

        Returns
        -------
        df, origin_time, stem_length
        """
        t_events = os.path.join(self.t_folder, "Events.tsv")
        if not os.path.exists(t_events):
            return pd.DataFrame(columns=["time", "event", "nodes"]), 0.0, 0.0

        rows: List[Dict[str, Any]] = []
        with open(t_events, "r", newline="") as f:
            sample = f.read(4096)
            f.seek(0)

            is_tab = "\t" in sample
            if is_tab:
                reader = csv.DictReader(f, delimiter="\t")
                for r in reader:
                    if not r:
                        continue
                    # Try several header casings
                    time_val = r.get("TIME", r.get("Time", r.get("time")))
                    event_val = r.get("EVENT", r.get("Event", r.get("event")))
                    nodes_val = r.get("NODES", r.get("Nodes", r.get("nodes")))
                    try:
                        rows.append(
                            {
                                "time": float(time_val),
                                "event": str(event_val).strip(),
                                "nodes": str(nodes_val).strip(),
                            }
                        )
                    except Exception:
                        continue
            else:
                for line in f:
                    line = line.strip()
                    if not line or line.lower().startswith("time"):
                        continue
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    try:
                        rows.append({"time": float(parts[0]), "event": parts[1], "nodes": parts[2]})
                    except Exception:
                        continue

        df = pd.DataFrame(rows)
        if len(df) == 0:
            return pd.DataFrame(columns=["time", "event", "nodes"]), 0.0, 0.0

        df = df.sort_values("time").reset_index(drop=True)

        origin_time = 0.0
        stem_length = 0.0

        # "O Root" gives origin time if present
        o_root = df[(df["event"] == "O") & (df["nodes"].astype(str).str.startswith("Root"))]
        if len(o_root) > 0:
            origin_time = float(o_root.iloc[0]["time"])

        # first speciation involving Root gives the root speciation time
        s_root = df[(df["event"] == "S") & (df["nodes"].astype(str).str.startswith("Root"))]
        if len(s_root) > 0:
            root_spec_time = float(s_root.iloc[0]["time"])
            stem_length = max(0.0, root_spec_time - origin_time)

        return df, origin_time, stem_length

    def _add_origin_stem(self, species_tree: ete3.Tree, stem_length: float) -> ete3.Tree:
        """
        Add an explicit 'Origin' node above the current root.
        The old root becomes the single child of Origin with dist=stem_length.
        """
        origin = ete3.Tree()
        origin.name = "Origin"
        origin.dist = 0.0

        # old root becomes a child
        species_tree.dist = float(stem_length)
        origin.add_child(species_tree)
        return origin

    def _annotate_time_from_origin(self, tree: ete3.Tree) -> None:
        """
        Add node.time_from_origin = cumulative dist from the ETE root.
        """
        tree.add_feature("time_from_origin", 0.0)
        for node in tree.traverse("preorder"):
            if node.up is None:
                node.time_from_origin = 0.0
            else:
                node.time_from_origin = float(node.up.time_from_origin) + float(getattr(node, "dist", 0.0))

    # ------------------------
    # Gene family events
    # ------------------------
    def _parse_gene_family_events(self) -> pd.DataFrame:
        """
        Parse all G/Gene_families/*_events.tsv.

        Format commonly:
          TIME <tab> EVENT <tab> NODES

        Returns a DataFrame with:
          family, time, event, nodes, node
        where node is the first token of nodes (split by ';').
        """
        if not os.path.exists(self.g_folder):
            return pd.DataFrame(columns=["family", "time", "event", "nodes", "node"])

        rows: List[Dict[str, Any]] = []
        gene_files = glob.glob(os.path.join(self.g_folder, "*_events.tsv"))
        for filepath in gene_files:
            family_id = os.path.basename(filepath).split("_")[0]
            rows.extend(self._parse_single_events_tsv(filepath, family_id))

        df = pd.DataFrame(rows)
        if len(df) == 0:
            return pd.DataFrame(columns=["family", "time", "event", "nodes", "node"])

        df["node"] = df["nodes"].apply(
            lambda s: str(s).split(";")[0] if isinstance(s, str) and len(s) > 0 else ""
        )
        return df.sort_values(["family", "time"]).reset_index(drop=True)

    def _parse_single_events_tsv(self, filepath: str, family_id: str) -> List[Dict[str, Any]]:
        """
        Parse one <family>_events.tsv into row dicts with keys: family,time,event,nodes.
        """
        rows: List[Dict[str, Any]] = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.lower().startswith("time"):
                    continue
                parts = line.split()
                if len(parts) < 3:
                    continue
                try:
                    time = float(parts[0])
                except ValueError:
                    continue
                event = str(parts[1]).strip()
                nodes = str(parts[2]).strip()
                rows.append({"family": family_id, "time": time, "event": event, "nodes": nodes})
        return rows

    def _extract_species_transfers(self, gene_events: pd.DataFrame) -> pd.DataFrame:
        """
        Extract species-level transfers from gene-family events.

        Zombi gene-family transfer payload format (as you reported):
            TIME   T   n2;3;n2;4;n1;5

        Meaning:
        donor gene node     = n2_3
        retained gene node  = n2_4
        receiver gene node  = n1_5

        Species node names are the prefix before '_' (n2, n1, ...).
        """
        if gene_events is None or len(gene_events) == 0:
            return pd.DataFrame(columns=[
                "family", "time", "from", "to", "freq",
                "donor_gene", "retained_gene", "recv_gene"
            ])

        df = gene_events[gene_events["event"] == "T"].copy()
        rows = []

        for _, r in df.iterrows():
            nodes = str(r.get("nodes", ""))
            toks = nodes.split(";")
            if len(toks) < 6:
                continue

            donor_gene = f"{toks[0]}_{toks[1]}"
            retained_gene = f"{toks[2]}_{toks[3]}"
            recv_gene = f"{toks[4]}_{toks[5]}"

            from_species = donor_gene.split("_", 1)[0]
            to_species = recv_gene.split("_", 1)[0]

            rows.append({
                "family": r.get("family", ""),
                "time": float(r["time"]),
                "from": from_species,
                "to": to_species,
                "freq": 1.0,  # default weight; you can change later if you compute frequencies
                "donor_gene": donor_gene,
                "retained_gene": retained_gene,
                "recv_gene": recv_gene,
            })

        return pd.DataFrame(rows)



    # ------------------------
    # Plotting helper
    # ------------------------
    def to_branch_shapes(
        self,
        data: ZombiData,
        shape_map: Optional[Dict[str, str]] = None,
        color_map: Optional[Dict[str, str]] = None,
        size: float = 10.0,
        stroke: str = "black",
        stroke_width: float = 1.0,
        include_events: Optional[List[str]] = None,
        exclude_events: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert gene events into BaseDrawer.add_branch_shapes specs.

        Mapping:
          for an event on species node 'node_name' at time tt,
          parent time t0 = parent.time_from_origin
          child  time t1 = node.time_from_origin
          where = (tt - t0) / (t1 - t0) clipped to [0,1]

        Parameters
        ----------
        data
            Parsed ZombiData.
        shape_map, color_map
            Maps from event letter (e.g., 'D','L','P','I','O','E') to shape/color.
        size
            Default marker size.
        include_events, exclude_events
            Optional filtering by event codes.

        Returns
        -------
        list of dict specs, suitable for drawer.add_branch_shapes(specs, ...)
        """
        shape_map = shape_map or {}
        color_map = color_map or {}

        include_set = set(include_events) if include_events else None
        exclude_set = set(exclude_events) if exclude_events else set()

        t = data.species_tree
        specs: List[Dict[str, Any]] = []

        for _, row in data.gene_events.iterrows():
            et = str(row.get("event", "")).strip()
            if include_set is not None and et not in include_set:
                continue
            if et in exclude_set:
                continue

            # Skip transfers here; handle separately once LT/AT format is confirmed
            if et in ("LT", "AT", "T"):
                continue

            node_name = str(row.get("node", "")).strip()
            if node_name == "":
                continue

            try:
                node = t & node_name
            except Exception:
                continue

            parent = node.up
            if parent is None:
                continue

            t0 = float(getattr(parent, "time_from_origin", 0.0))
            t1 = float(getattr(node, "time_from_origin", t0))
            tt = float(row["time"])

            denom = (t1 - t0) if abs(t1 - t0) > 1e-12 else 1.0
            where = (tt - t0) / denom
            where = 0.0 if where < 0.0 else (1.0 if where > 1.0 else where)

            specs.append(
                {
                    "branch": node_name,  # child node id in the species tree
                    "where": float(where),
                    "shape": shape_map.get(et, "circle"),
                    "fill": color_map.get(et, "black"),
                    "size": float(size),
                    "stroke": stroke,
                    "stroke_width": float(stroke_width),
                    "rotation": 0.0,  # vertical: no rotation by default
                    "event": et,
                    "family": row.get("family", ""),
                    "time": float(tt),
                }
            )

        return specs


def parse_zombi(folder_path: str) -> ZombiData:
    """
    Convenience function.
    """
    return ZombiParser(folder_path).parse()

