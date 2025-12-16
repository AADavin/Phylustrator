import os
import glob
import pandas as pd
import ete3
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ZombiData:
    """
    Stores data parsed from Zombi simulation output.
    """
    species_tree: ete3.Tree

    # Raw events with EXACT timestamps for precise plotting
    # Format: [{'time': 1.2, 'type': 'D', 'node': 'n10'}, ...]
    raw_events: List[Dict]

    # Specific list for Transfer Links (with From/To/Time)
    transfers: List[Dict]

    # Aggregated stats for Heatmaps (Counts per branch)
    aggregated_stats: pd.DataFrame


class ZombiParser:
    def __init__(self, root_folder):
        self.root = root_folder
        self.t_folder = os.path.join(self.root, "T")
        self.g_folder = os.path.join(self.root, "G")

        if not os.path.exists(self.t_folder) or not os.path.exists(self.g_folder):
            raise FileNotFoundError(f"Zombi output structure not found in {self.root}")

    def parse(self) -> ZombiData:

        events_tsv_path = os.path.join(self.t_folder, "Events.tsv")

        if os.path.exists(events_tsv_path):
            with open(events_tsv_path, 'r') as f:
                # Skip header
                f.readline()
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3:
                        # Format: TIME EVENT NODES
                        # We look for the first 'S' (Speciation)
                        if parts[1] == 'S':
                            root_offset = float(parts[0])
                            break
        
        # 1. Load Species Tree
        # --------------------
        tree_path = os.path.join(self.t_folder, "CompleteTree.nwk")
        if not os.path.exists(tree_path):
            tree_path = os.path.join(self.t_folder, "ExtantTree.nwk")

        species_tree = ete3.Tree(tree_path, format=1)
        species_tree.dist = root_offset

        # 2. Parse Events per Branch
        # --------------------
        events_path = os.path.join(self.g_folder, "Events_per_branch")
        event_files = glob.glob(os.path.join(events_path, "*_branchevents.tsv"))

        raw_events = []
        transfer_list = []
        stats = {}  # { 'node_name': {'D': 0, 'T': 0, 'L': 0} }

        for filepath in event_files:
            filename = os.path.basename(filepath)
            branch_name = filename.replace("_branchevents.tsv", "")

            # Initialize stats
            if branch_name not in stats:
                stats[branch_name] = {'duplications': 0, 'transfers': 0, 'losses': 0}

            with open(filepath, 'r') as f:
                header = f.readline()
                for line in f:
                    line = line.strip()
                    if not line: continue

                    parts = line.split("\t")
                    if len(parts) < 3: continue

                    # 1. Parse Exact Time
                    try:
                        event_time = float(parts[0])
                    except ValueError:
                        continue

                    event_type = parts[1]
                    nodes_str = parts[2]

                    # 2. Store Event
                    if event_type == "D":
                        # Duplication on this branch
                        stats[branch_name]['duplications'] += 1
                        raw_events.append({
                            "time": event_time,
                            "type": "D",
                            "node": branch_name
                        })

                    elif event_type == "L":
                        # Loss on this branch
                        stats[branch_name]['losses'] += 1
                        raw_events.append({
                            "time": event_time,
                            "type": "L",
                            "node": branch_name
                        })

                    elif event_type == "LT":
                        # Leaving Transfer (Source -> Dest)
                        node_parts = nodes_str.split(";")

                        if len(node_parts) >= 6:
                            source_sp = node_parts[0]
                            dest_sp = node_parts[4]

                            # Add to Stats
                            stats[branch_name]['transfers'] += 1

                            # Add to Raw Events (Generic)
                            raw_events.append({
                                "time": event_time,
                                "type": "T",
                                "node": source_sp,
                                "to_node": dest_sp
                            })

                            # Add to Transfer List (Specific for Drawing Links)
                            transfer_list.append({
                                "from": source_sp,
                                "to": dest_sp,
                                "time": event_time,
                                "freq": 1.0
                            })

                    # Ignore 'AT' (Arriving Transfer) to avoid duplicates

        # 3. Finalize Data Structures
        # --------------------

        # A. Aggregated Stats (DataFrame)
        stat_rows = []
        for node, counts in stats.items():
            row = {"species": node}
            row.update(counts)
            stat_rows.append(row)
        stats_df = pd.DataFrame(stat_rows)

        # B. Transfers (Keep exact times for drawing!)
        # We do NOT group by mean time anymore, because you want to draw them exactly.
        # If you want to group them later, you can do it in the plotting script.
        # We pass the raw transfer_list directly.

        return ZombiData(
            species_tree=species_tree,
            raw_events=raw_events,
            transfers=transfer_list,
            aggregated_stats=stats_df
        )


def parse_zombi(folder_path: str) -> ZombiData:
    parser = ZombiParser(folder_path)
    return parser.parse()