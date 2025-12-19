import os
import glob
import pandas as pd
import ete3
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ALEData:
    species_tree: ete3.Tree
    transfers: List[Dict]

def parse_ale_folder(folder_path: str, min_freq=0.0) -> ALEData:
    """
    Parses a folder of ALE results (.uTs files and one .uml_rec for the tree).
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # 1. Get Species Tree (from any .uml_rec file)
    rec_files = glob.glob(os.path.join(folder_path, "*.uml_rec"))
    if not rec_files:
        raise FileNotFoundError("No .uml_rec file found to extract Species Tree.")
    
    # Just parse the first one to get the species tree
    with open(rec_files[0], 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
        # Line 0 usually comment, Line 1 usually species tree
        tree_line = lines[1].split("\t")[-1]
        species_tree = ete3.Tree(tree_line, format=1)

    # 2. Parse Transfers (.uTs)
    transfers = []
    uts_files = glob.glob(os.path.join(folder_path, "*.uTs"))
    # Also check case sensitivity if needed
    if not uts_files:
         uts_files = glob.glob(os.path.join(folder_path, "*.uts"))

    for filepath in uts_files:
        filename = os.path.basename(filepath)
        # family name: 43_prunedtree.nwk.ale.uTs -> 43_prunedtree
        family_id = filename.split(".")[0]

        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith("#") or not line.strip(): continue
                if "from" in line: continue # Header

                parts = line.split()
                if len(parts) >= 3:
                    # from  to  freq
                    src = parts[0]
                    dst = parts[1]
                    freq = float(parts[2])

                    if freq >= min_freq:
                        transfers.append({
                            "family": family_id,
                            "from": src,
                            "to": dst,
                            "freq": freq,
                            "time": None # Undated
                        })

    return ALEData(species_tree, transfers)

# Keep the single file parser if you need it for specific logic
def parse_ale_file(filepath):
    # (Simplified version of previous one, returning tree and stats if needed)
    pass
