import os
import glob
import pandas as pd
import ete3
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ALEData:
    species_tree: ete3.Tree
    transfers: List[Dict]
    branch_stats: Optional[pd.DataFrame] = None

def parse_uts_file(filepath: str) -> List[Dict]:
    """
    Parses a single ALE .uTs file (Transfers).
    """
    transfers = []
    filename = os.path.basename(filepath)
    # Extract family: "43_prunedtree.nwk.ale.uTs" -> "43_prunedtree"
    family_id = filename.split(".")[0]
    
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith("#") or not line.strip(): continue
            if "from" in line: continue 

            parts = line.split()
            if len(parts) >= 3:
                src, dst, freq = parts[0], parts[1], float(parts[2])
                transfers.append({
                    "family": family_id,
                    "from": src,
                    "to": dst,
                    "freq": freq,
                    "time": None 
                })
    return transfers

def parse_ale_file(filepath: str) -> ALEData:
    """
    Parses a single .uml_rec file to get the tree and stats.
    """
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    # 1. Parse Species Tree
    # Often line 1, column -1 is the tree. 
    # Logic: Look for the line starting with '(' or find the column.
    tree_line = lines[1].split("\t")[-1]
    species_tree = ete3.Tree(tree_line, format=1)

    # 2. Parse Branch Stats
    data_rows = []
    start_parsing = False
    for line in lines:
        if line.startswith("#S_node"):
            start_parsing = True
            continue
        
        if start_parsing and not line.startswith("#"):
            cols = line.split("\t")
            if len(cols) < 5: continue
            
            data_rows.append({
                "name": cols[1],
                "Duplications": float(cols[2]),
                "Transfers": float(cols[3]),
                "Losses": float(cols[4]),
                "Originations": float(cols[5])
            })
            
    df = pd.DataFrame(data_rows)

    return ALEData(
        species_tree=species_tree, 
        transfers=[], 
        branch_stats=df
    )

def parse_ale_folder(folder_path: str, min_freq=0.0) -> ALEData:
    """
    Parses a folder containing .uTs and .uml_rec files.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # 1. Get Tree from first .uml_rec
    rec_files = glob.glob(os.path.join(folder_path, "*.uml_rec"))
    if not rec_files:
        raise FileNotFoundError("No .uml_rec file found.")
    
    base_data = parse_ale_file(rec_files[0])
    species_tree = base_data.species_tree

    # 2. Get Transfers from all .uTs
    all_transfers = []
    uts_files = glob.glob(os.path.join(folder_path, "*.uTs"))
    # Case insensitive check
    if not uts_files:
        uts_files = glob.glob(os.path.join(folder_path, "*.uts"))

    for f in uts_files:
        tr_list = parse_uts_file(f)
        for tr in tr_list:
            if tr['freq'] >= min_freq:
                all_transfers.append(tr)

    return ALEData(species_tree=species_tree, transfers=all_transfers)
