import os
import glob
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AleRaxData:
    transfers: List[Dict]

def parse_alerax_transfers(summaries_folder: str, min_freq=0.0) -> AleRaxData:
    """
    Parses AleRax transfer summary files.
    Location example: .../reconciliations/summaries/
    """
    if not os.path.exists(summaries_folder):
        raise FileNotFoundError(f"Folder not found: {summaries_folder}")

    transfers = []
    # Pattern: *_transfers.txt
    files = glob.glob(os.path.join(summaries_folder, "*_transfers.txt"))

    for filepath in files:
        filename = os.path.basename(filepath)
        # Family Name: scaffold983gene4_transfers.txt -> scaffold983gene4_transfers
        family_id = filename.split(".")[0]

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
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
                            "time": None # AleRax is usually undated topology
                        })

    return AleRaxData(transfers)
