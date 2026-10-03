"""Audit frozen normalization without changing any E03 detector or objective."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.updates import apply_batch


def run():
    config = json.loads(Path('configs/e03_repair_quality.json').read_text())
    rows = [json.loads(line) for line in Path('results/raw/e03_repair_quality.jsonl').read_text().splitlines()]
    records = {(r['seed'], r['update_side'], r['requested_fraction']): r for r in rows if r['method'] == 'full'}
    audit = []
    for split, seeds in [('replay', config['replay_seeds']), ('fresh', config['fresh_seeds'])]:
        for seed in seeds:
            g, h, _, bundle = graph_pair(config['nodes'], config['attachment'], seed, config['noise'])
            fg, fh = descriptors(g, config['descriptor_mode']), descriptors(h, config['descriptor_mode'])
            raw_scale = np.vstack([fg, fh]).std(axis=0)
            floor = np.flatnonzero(raw_scale < 1e-12)
            for fraction in config['update_fractions']:
                budget = max(1, int(fraction*(g.number_of_edges()+h.number_of_edges())+.5))
                for side in config['update_sides']:
                    source = budget if side == 'source' else (0 if side == 'target' else (budget+1)//2)
                    ng, _ = apply_batch(g, source, bundle[3])
                    target_seed = int(np.random.SeedSequence(bundle[3]).generate_state(1)[0])
                    nh, _ = apply_batch(h, budget-source, target_seed)
                    new_fg, new_fh = descriptors(ng, config['descriptor_mode']), descriptors(nh, config['descriptor_mode'])
                    pooled = np.vstack([new_fg, new_fh])
                    active = [int(d) for d in floor if pooled[:, d].std() > 1e-12]
                    record = records[seed, side, fraction]
                    audit.append({'split': split, 'seed': seed, 'update_side': side,
                        'fraction': fraction, 'initial_floor_dimensions': floor.tolist(),
                        'newly_variable_floor_dimensions': active,
                        'full_objective': record['full_objective'], 'keep_old_objective': record['old_objective'],
                        'large_full_objective': record['full_objective'] > 1e20})
    Path('results/raw/e03_normalization_audit.json').write_text(json.dumps(audit, indent=2))
    for fraction in config['update_fractions']:
        subset = [r for r in audit if r['fraction'] == fraction]
        print(fraction, 'newly active floor dimensions:',sum(bool(r['newly_variable_floor_dimensions']) for r in subset),'/',len(subset),
              'full objective > 1e20:',sum(r['large_full_objective'] for r in subset))


if __name__ == '__main__':
    run()
