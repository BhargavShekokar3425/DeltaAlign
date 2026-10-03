"""Measure descriptor ambiguity on noiseless copies."""
import json
from pathlib import Path
import numpy as np
from src.graph import graph_pair
from src.descriptors import descriptors
from src.full_align import full_align

rows = []
for seed in range(5):
    g, h, truth, _ = graph_pair(1000, 3, seed, 0)
    mapping, _, stats = full_align(g, h)
    rows.append({'seed': seed, 'n': 1000, 'noise': 0,
                 'nc': float(np.mean(mapping == truth)),
                 'unique_descriptors': len(np.unique(descriptors(g), axis=0)),
                 'objective': stats['objective']})
Path('results/raw/e00_noiseless_controls.json').write_text(json.dumps(rows, indent=2))
print(json.dumps(rows, indent=2))
