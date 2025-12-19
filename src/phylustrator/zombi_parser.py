import os
import glob
import ete3
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ZombiData:
    species_tree: ete3.Tree
    raw_events: List[Dict]
    transfers: List[Dict]

class ZombiParser:
    def __init__(self, root_folder):
        self.root = root_folder
        self.t_folder = os.path.join(self.root, "T")
        self.g_folder = os.path.join(self.root, "G", "Gene_families")

        # Fallback if user pointed strictly to T or similar structures
        if not os.path.exists(self.t_folder) and os.path.basename(root_folder) == "T":
            self.t_folder = root_folder
            # Try to infer G folder
            self.g_folder = os.path.join(os.path.dirname(root_folder), "G", "Gene_families")

    def parse(self) -> ZombiData:
        # 1. Load Species Tree
        tree_files = ["SpeciesTree.nwk", "CompleteTree.nwk", "ExtantTree.nwk"]
        species_tree = None
        for name in tree_files:
            path = os.path.join(self.t_folder, name)
            if os.path.exists(path):
                species_tree = ete3.Tree(path, format=1)
                break
        
        if not species_tree:
            raise FileNotFoundError(f"No species tree found in {self.t_folder}")

        raw_events = []
        transfers = []

        # 2. Parse Species Tree Events (T/Events.tsv) - THE STEM
        # These are crucial for the timeline (Root Origin, Speciations, Extinctions)
        t_events = os.path.join(self.t_folder, "Events.tsv")
        if os.path.exists(t_events):
            self._parse_events_file(t_events, "SpeciesTree", raw_events, transfers)

        # 3. Parse Gene Families (G/Gene_families/*.tsv)
        if os.path.exists(self.g_folder):
            gene_files = glob.glob(os.path.join(self.g_folder, "*_events.tsv"))
            for filepath in gene_files:
                fname = os.path.basename(filepath)
                family_id = fname.split("_")[0]
                self._parse_events_file(filepath, family_id, raw_events, transfers)

        return ZombiData(species_tree, raw_events, transfers)

    def _parse_events_file(self, filepath, family_id, raw_events, transfers):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip headers or empty lines
                if not line or line.startswith("TIME") or line.startswith("time"):
                    continue

                parts = line.split()
                if len(parts) < 3: continue

                # Parse Time
                try:
                    time = float(parts[0])
                except ValueError:
                    continue

                etype = parts[1]
                nodes_str = parts[2]
                
                # Parse Node IDs
                tokens = nodes_str.split(";")
                
                if etype == "T":
                    # Format: Src;Gene;Retained;Gene;Dst;Gene
                    if len(tokens) >= 5:
                        transfers.append({
                            "family": family_id,
                            "from": tokens[0], # Source Species Node Name
                            "to": tokens[4],   # Dest Species Node Name
                            "time": time,
                            "freq": 1.0
                        })
                else:
                    # D, L, O, S, E (Extinction)
                    # Format: NodeName;GeneID...
                    node_name = tokens[0]
                    raw_events.append({
                        "family": family_id,
                        "type": etype,
                        "node": node_name,
                        "time": time
                    })

def parse_zombi(folder_path: str) -> ZombiData:
    return ZombiParser(folder_path).parse()
