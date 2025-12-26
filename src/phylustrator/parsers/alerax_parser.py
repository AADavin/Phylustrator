import os
import glob
import ete3
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class AleRaxData:
    species_tree: Optional[ete3.Tree] = None
    transfers: List[Dict] = field(default_factory=list)

def parse_alerax(root_folder: str, min_freq=0.0) -> AleRaxData:
    # 1. Parse Transfers
    summaries_path = os.path.join(root_folder, "reconciliations", "summaries")
    transfers = []
    
    for fpath in glob.glob(os.path.join(summaries_path, "*_transfers.txt")):
        family_id = os.path.basename(fpath).replace("_transfers.txt", "")
        with open(fpath, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3:
                    src, dst, freq = parts[0], parts[1], float(parts[2])
                    if freq >= min_freq:
                        transfers.append({"family": family_id, "from": src, "to": dst, "freq": freq, "time": None})

    # 2. Load Species Tree (Direct path)
    tree_path = os.path.join(root_folder, "species_trees", "inferred_species_tree.newick")
    sp_tree = ete3.Tree(tree_path, format=1) if os.path.exists(tree_path) else None

    return AleRaxData(species_tree=sp_tree, transfers=transfers)
