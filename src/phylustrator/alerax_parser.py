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
    """
    Parses AleRax output to find transfers.
    Checks: root_folder/reconciliations/summaries/
    """
    # 1. Locate Summaries
    if os.path.basename(root_folder) == "summaries":
        summaries_path = root_folder
    else:
        summaries_path = os.path.join(root_folder, "reconciliations", "summaries")
        if not os.path.exists(summaries_path):
             summaries_path = os.path.join(root_folder, "summaries")
    
    if not os.path.exists(summaries_path):
        raise FileNotFoundError(f"AleRax summaries not found in {root_folder}")

    # 2. Parse Transfers
    transfers = []
    files = glob.glob(os.path.join(summaries_path, "*_transfers.txt"))
    
    for filepath in files:
        # Family ID: "scaffold983gene4_transfers.txt" -> "scaffold983gene4"
        filename = os.path.basename(filepath)
        family_id = filename.replace("_transfers.txt", "")

        with open(filepath, 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3:
                    # from  to  freq
                    src, dst, freq = parts[0], parts[1], float(parts[2])
                    if freq >= min_freq:
                        transfers.append({
                            "family": family_id,
                            "from": src,
                            "to": dst,
                            "freq": freq,
                            "time": None # AleRax is undated
                        })

    # 3. Parse Species Tree (Optional)
    sp_tree = None
    possible_trees = [
        os.path.join(root_folder, "species_tree.newick"),
        os.path.join(root_folder, "species_trees", "species_tree.newick")
    ]
    for p in possible_trees:
        if os.path.exists(p):
            try:
                sp_tree = ete3.Tree(p, format=1)
                break
            except:
                pass

    return AleRaxData(species_tree=sp_tree, transfers=transfers)
