"""Read `ZOMBI2 <https://github.com/AADavin/zombi2>`_ output and draw gene-family reconciliations.

ZOMBI2 simulates species trees and gene families and writes a folder with the species tree,
per-family event tables and transfers. This module reads that output (it never imports ZOMBI2)
and overlays a family's history on the **time-calibrated** species tree: originations,
duplications and losses as markers placed at their true time along a branch, and transfers as
arcs drawn *at the transfer time* — so a transfer is horizontal in time by construction.

Expected folder (from ``zombi2`` ``Genomes.write(outdir)``)::

    <outdir>/
      species_tree.nwk                        # named internal nodes, branch lengths = time
      gene_family_events/<family>_events.tsv  # columns: time, event, branch, donor, recipient, nodes
      Transfers.tsv                           # optional; transfers are also derived from the events

Quick start::

    from phylustrator import zombi2
    data = zombi2.load("out/")
    drawer = zombi2.draw_reconciliation(data, family="10")
    drawer.save_svg("family10.svg")   # or .save_png(...) with the [export] extra
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import ete3
import pandas as pd

from .drawing import TreeStyle, VerticalTreeDrawer
from .io import read_newick

__all__ = ["Zombi2Data", "load", "draw_reconciliation", "event_markers", "transfer_records"]

# ZOMBI event code -> (marker shape, fill colour). Colours are the ColorBrewer Set1 palette
# ZOMBI/Phylustrator use elsewhere. Transfers (T) are drawn as arcs, not markers.
EVENT_STYLE: dict[str, tuple[str, str]] = {
    "O": ("star", "#984EA3"),      # origination
    "D": ("square", "#377EB8"),    # duplication
    "T": ("triangle", "#4DAF4A"),  # transfer
    "L": ("circle", "#E41A1C"),    # loss
    "S": ("circle", "#999999"),    # speciation
    "I": ("triangle", "#FF7F00"),  # inversion (ordered genome)
    "P": ("diamond", "#FFFF33"),   # transposition
}

#: Default point-events drawn as branch markers (S is implicit in the tree; T is an arc).
DEFAULT_EVENTS = ("O", "D", "L")


@dataclass
class Zombi2Data:
    """Parsed ZOMBI2 output, ready to draw.

    Attributes
    ----------
    species_tree:
        The species tree as an ``ete3.Tree``; every node is annotated with
        ``time_from_origin`` (root = 0, cumulative branch length), which is what places
        events and transfers at the right time.
    events:
        All gene-family events — columns ``family, time, event, branch, donor, recipient, nodes``.
    transfers:
        Transfers derived from the events — columns ``from, to, time, family, freq``.
    """

    species_tree: ete3.Tree
    events: pd.DataFrame
    transfers: pd.DataFrame = field(repr=False)

    def families(self) -> list[str]:
        """Family ids present in the events, in natural order."""
        if self.events.empty:
            return []
        return sorted(self.events["family"].astype(str).unique(), key=_natkey)


def _natkey(name: str) -> tuple[int, str]:
    digits = re.sub(r"\D", "", name)
    return (int(digits) if digits else 0, name)


def _annotate_times(tree: ete3.Tree) -> ete3.Tree:
    """Annotate every node with ``time_from_origin`` (root = 0, cumulative branch length)."""
    for n in tree.traverse("preorder"):
        n.add_feature("time_from_origin", 0.0 if n.is_root() else n.up.time_from_origin + n.dist)
    return tree


def load(output_dir: str | Path) -> Zombi2Data:
    """Parse a ZOMBI2 ``Genomes.write()`` output folder into a :class:`Zombi2Data`."""
    out = Path(output_dir)
    sp_path = out / "species_tree.nwk"
    if not sp_path.exists():
        raise FileNotFoundError(
            f"No species_tree.nwk in {out}. Point `load` at a folder written by "
            f"zombi2's Genomes.write()."
        )
    tree = _annotate_times(read_newick(sp_path))

    frames = []
    for path in sorted(glob.glob(str(out / "gene_family_events" / "*_events.tsv"))):
        family = os.path.basename(path).replace("_events.tsv", "")
        df = pd.read_csv(path, sep="\t",
                         dtype={"event": str, "branch": str, "donor": str, "recipient": str})
        df.insert(0, "family", family)
        frames.append(df)
    cols = ["family", "time", "event", "branch", "donor", "recipient", "nodes"]
    events = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)

    if not events.empty:
        tr = events[events["event"] == "T"]
        transfers = pd.DataFrame({
            "from": tr["donor"].astype(str), "to": tr["recipient"].astype(str),
            "time": tr["time"].astype(float), "family": tr["family"].astype(str),
            "freq": 1.0,
        }).reset_index(drop=True)
    else:
        transfers = pd.DataFrame(columns=["from", "to", "time", "family", "freq"])

    return Zombi2Data(species_tree=tree, events=events, transfers=transfers)


def _where(node: ete3.TreeNode, t: float) -> float:
    """Fractional position (0-1) of time ``t`` along the branch above ``node``."""
    parent = node.up
    if parent is None:
        return 0.0
    t0 = float(getattr(parent, "time_from_origin", 0.0))
    t1 = float(getattr(node, "time_from_origin", t0))
    if abs(t1 - t0) <= 1e-12:
        return 0.5
    return max(0.0, min(1.0, (t - t0) / (t1 - t0)))


def event_markers(data: Zombi2Data, family, event_types=DEFAULT_EVENTS, r: float = 7.0,
                  stroke: str = "white", stroke_width: float = 1.5) -> list[dict]:
    """Branch-marker specs for one family's point events, for ``add_branch_shapes``.

    Each event is placed at its true time along its species branch. Diamonds/stars are mapped
    to shapes the drawer supports (square rotated 45°, circle). Skips events whose branch is
    not in the species tree.
    """
    name2node = {n.name: n for n in data.species_tree.traverse()}
    df = data.events
    if df.empty:
        return []
    sub = df[(df["family"].astype(str) == str(family)) & (df["event"].isin(event_types))]

    specs: list[dict] = []
    for _, row in sub.iterrows():
        node = name2node.get(str(row["branch"]))
        if node is None or node.up is None:  # events on the root stem have nowhere to sit
            continue
        shape, color = EVENT_STYLE.get(row["event"], ("circle", "black"))
        rotation = 0.0
        if shape == "diamond":
            shape, rotation = "square", 45.0
        elif shape == "star":
            shape = "circle"
        specs.append({
            "branch": node, "where": _where(node, float(row["time"])),
            "shape": shape, "fill": color, "r": r, "stroke": stroke,
            "stroke_width": stroke_width, "rotation": rotation, "event_type": row["event"],
        })
    return specs


def transfer_records(data: Zombi2Data, family) -> list[dict]:
    """Transfer dicts (``from, to, time, freq``) for one family, for ``plot_transfers(mode='time')``."""
    tr = data.transfers
    if tr.empty:
        return []
    return tr[tr["family"].astype(str) == str(family)].to_dict("records")


def draw_reconciliation(data, family, style: TreeStyle | None = None,
                        event_types=DEFAULT_EVENTS, show_transfers: bool = True,
                        leaf_names: bool = True, node_names: bool = True,
                        title: str | None = None,
                        transfer_colors=("#984EA3", "#4DAF4A")) -> VerticalTreeDrawer:
    """Draw one family's reconciliation on the time-calibrated species tree.

    ``data`` may be a :class:`Zombi2Data` or a path to a ZOMBI2 output folder. Point events
    (O/D/L) become branch markers at their true time; transfers become arcs placed by time
    (``mode="time"``), so they are horizontal in time. Returns the
    :class:`~phylustrator.VerticalTreeDrawer` for further customisation / ``save_svg`` /
    ``save_png``.
    """
    if not isinstance(data, Zombi2Data):
        data = load(data)
    if style is None:
        style = TreeStyle(width=760, height=440, leaf_r=0, node_r=4,
                          branch_stroke_width=4, branch_color="#666", font_size=14)

    v = VerticalTreeDrawer(data.species_tree, style=style)
    v.draw()
    if leaf_names:
        v.add_leaf_names()
    if node_names:
        v.add_node_names()

    specs = event_markers(data, family, event_types=event_types)
    if specs:
        v.add_branch_shapes(specs)
    if show_transfers:
        records = transfer_records(data, family)
        if records:
            v.plot_transfers(records, mode="time", use_gradient=True,
                             gradient_colors=transfer_colors, stroke_width=4.0,
                             arc_intensity=26.0, opacity=0.9)

    v.add_title(title if title is not None else f"ZOMBI2 gene family {family}", font_size=16)
    return v
