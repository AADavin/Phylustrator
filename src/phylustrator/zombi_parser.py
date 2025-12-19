import os
import glob
import pandas as pd
import ete3
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ZombiData:
    species_tree: ete3.Tree
    raw_events: List[Dict] # D, L, O
    transfers: List[Dict]  # T

class ZombiParser:
    def __init__(self, root_folder):
        self.root = root_folder
        # Zombi species tree is usually in T/SpeciesTree.nwk or T/ExtantTree.nwk
        self.sp_tree_path = os.path.join(self.root, "T", "SpeciesTree.nwk")
        if not os.path.exists(self.sp_tree_path):
             # Fallback if SpeciesTree.nwk doesn't exist
             self.sp_tree_path = os.path.join(self.root, "T", "CompleteTree.nwk")
             
        self.families_folder = os.path.join(self.root, "G", "Gene_families")

    def parse(self) -> ZombiData:
        # 1. Load Species Tree
        if not os.path.exists(self.sp_tree_path):
            raise FileNotFoundError(f"Could not find species tree in {self.root}/T/")
        
        species_tree = ete3.Tree(self.sp_tree_path, format=1)

        raw_events = []
        transfers = []

        # 2. Iterate over Gene Families
        if not os.path.exists(self.families_folder):
            raise FileNotFoundError(f"Folder not found: {self.families_folder}")

        tsv_files = glob.glob(os.path.join(self.families_folder, "*_events.tsv"))
        
        for filepath in tsv_files:
            # Extract family name: "100_events.tsv" -> "100"
            filename = os.path.basename(filepath)
            family_id = filename.split("_")[0] 

            with open(filepath, 'r') as f:
                header = f.readline() # Skip header: TIME EVENT NODES
                for line in f:
                    parts = line.split() # Splits by tab or space
                    if len(parts) < 3: continue

                    time = float(parts[0])
                    etype = parts[1]
                    nodes_str = parts[2]
                    
                    # Parse NODES string (semicolon separated)
                    # Example T: n1;2;n1;8;n6;9 (SourceSp;Gene;RetainedSp;Gene;DestSp;Gene)
                    node_tokens = nodes_str.split(";")
                    
                    if etype == "T":
                        # We expect 6 tokens for T: u;uid;v;vid;w;wid
                        # Transfer is from u (tokens[0]) to w (tokens[4])
                        if len(node_tokens) >= 5:
                            src_sp = node_tokens[0]
                            dst_sp = node_tokens[4]
                            
                            transfers.append({
                                "family": family_id,
                                "from": src_sp,
                                "to": dst_sp,
                                "time": time,
                                "freq": 1.0 # Zombi events are single events, freq=1
                            })

                    elif etype == "D":
                        # Duplication usually happens at a specific node
                        # Format: Sp;ID;Child1Sp;ID;Child2Sp;ID
                        sp_node = node_tokens[0]
                        raw_events.append({
                            "family": family_id,
                            "type": "D",
                            "node": sp_node,
                            "time": time
                        })

                    elif etype == "L":
                        # Loss: Sp;ID
                        sp_node = node_tokens[0]
                        raw_events.append({
                            "family": family_id,
                            "type": "L",
                            "node": sp_node,
                            "time": time
                        })

        return ZombiData(species_tree, raw_events, transfers)

def parse_zombi(folder_path: str) -> ZombiData:
    return ZombiParser(folder_path).parse()
