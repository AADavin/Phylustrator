import os
import glob
import pandas as pd
import ete3
from dataclasses import dataclass
from typing import Optional

@dataclass
class AleRaxData:
    """
    Stores aggregated data from an AleRax run.
    """
    species_tree: Optional[ete3.Tree]
    events_df: pd.DataFrame          # The raw, concatenated data from all families
    aggregated_stats: pd.DataFrame   # Summed stats per species (Total D, T, L, etc.)

class AleRaxParser:
    def __init__(self, output_path):
        self.path = output_path
        # Define expected columns based on AleRax documentation/standard output
        self.header = ["species_label", "speciations", "duplications", "losses", 
                       "transfers", "presence", "origination", "copies", 
                       "singletons", "gene_family", "replicate"]

    def parse(self) -> AleRaxData:
        """
        Parses the AleRax output directory.
        """
        # 1. Parse Reconciliations (Event Counts)
        # ------------------------------------------------
        # Look in reconciliations/all/ for *.perspecies_eventcount.txt or *.perspecies_eventcount
        # AleRax directory structure can vary slightly, so we look recursively or in standard spots.
        rec_path = os.path.join(self.path, "reconciliations", "all")
        if not os.path.exists(rec_path):
            # Fallback: maybe they are just in reconciliations/
            rec_path = os.path.join(self.path, "reconciliations")
            
        # Find all event count files
        files = glob.glob(os.path.join(rec_path, "*perspecies_eventcount*"))
        
        data = []
        for mfile in files:
            # Extract Gene Family and Replicate from filename
            # Filename format example: "FAM001_0.perspecies_eventcount.txt"
            filename = os.path.basename(mfile)
            
            # Robust split logic
            parts = filename.split(".")
            base = parts[0] # "FAM001_0"
            
            if "_" in base:
                gf = base.split("_")[0]
                rep = base.split("_")[-1]
            else:
                gf = base
                rep = "0"

            # Read File
            # Skip the first line (header) and parse lines
            with open(mfile, 'r') as f:
                header_line = f.readline() # Skip header "species, speciation, ..."
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    # Split by comma (standard AleRax CSV format)
                    cols = line.split(",")
                    
                    # Parse row: [Label] + [Integers...]
                    row = [cols[0]] + [float(x) for x in cols[1:]]
                    
                    # Append metadata
                    row.append(gf)
                    row.append(rep)
                    
                    data.append(row)

        # Create Raw DataFrame
        df = pd.DataFrame(data, columns=self.header)
        
        # 2. Create Aggregated Stats (Sum per Species)
        # ------------------------------------------------
        # We group by 'species_label' and sum the numeric columns.
        # This gives us the data needed to paint the Species Tree (e.g. Total Transfers at Node X).
        numeric_cols = ["speciations", "duplications", "losses", "transfers", 
                        "presence", "origination", "copies", "singletons"]
        
        agg_df = df.groupby("species_label")[numeric_cols].sum().reset_index()

        # 3. Parse Species Tree (Optional but recommended)
        # ------------------------------------------------
        # Try to find the species tree in species_trees/
        tree_path = os.path.join(self.path, "species_trees")
        s_tree = None
        
        if os.path.exists(tree_path):
            # Usually named "species_tree.newick" or similar
            tree_files = glob.glob(os.path.join(tree_path, "*.newick"))
            if not tree_files:
                tree_files = glob.glob(os.path.join(tree_path, "*.nwk"))
                
            if tree_files:
                try:
                    # Load the first found tree
                    s_tree = ete3.Tree(tree_files[0], format=1)
                except:
                    print(f"Warning: Could not parse species tree at {tree_files[0]}")

        return AleRaxData(
            species_tree=s_tree,
            events_df=df,
            aggregated_stats=agg_df
        )

# Convenience function wrapper
def parse_alerax(path: str) -> AleRaxData:
    parser = AleRaxParser(path)
    return parser.parse()
