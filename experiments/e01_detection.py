import json
import platform
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.full_align import full_align
from src.updates import apply_batch
from src.metrics import region, detection
from src.candidates import candidate_lists, refresh_costs, update_candidates, dependency_seeds
from src.conflict_closure import conflict_closure


def run(config, output):
    n, mode = config['nodes'], config['descriptor_mode']
    with Path(output).open('w') as stream:
        for seed in config['seeds']:
            g, h, truth, seeds = graph_pair(n, config['attachment'], seed, config['noise'])
            old, scale, initial = full_align(g, h, descriptor_mode=mode)
            fg, fh = descriptors(g, mode), descriptors(h, mode)
            old_costs = cdist(fg / scale, fh / scale, 'sqeuclidean')
            old_lists = {k: candidate_lists(old_costs, old, k) for k in config['candidate_sizes']}
            for fraction in config['update_fractions']:
                budget = max(1, int(fraction * (g.number_of_edges() + h.number_of_edges()) + .5))
                for side in config['update_sides']:
                    source_count = budget if side == 'source' else (0 if side == 'target' else (budget + 1) // 2)
                    target_count = budget - source_count
                    new_g, gb = apply_batch(g, source_count, seeds[3])
                    new_h, hb = apply_batch(h, target_count, int(np.random.SeedSequence(seeds[3]).generate_state(1)[0]))
                    new, _, full = full_align(new_g, new_h, scale, descriptor_mode=mode)
                    changed = set(np.flatnonzero(old != new).tolist())
                    # Full descriptor recomputation is an explicit oracle here.
                    new_fg, new_fh = descriptors(new_g, mode), descriptors(new_h, mode)
                    changed_g = set(np.flatnonzero(np.any(fg != new_fg, axis=1)).tolist())
                    changed_h = set(np.flatnonzero(np.any(fh != new_fh, axis=1)).tolist())
                    support_g, support_h = region(g, new_g, gb, 2), region(h, new_h, hb, 2)
                    assert changed_g <= support_g and changed_h <= support_h
                    start = perf_counter()
                    costs, rescored = refresh_costs(old_costs, new_fg, new_fh, changed_g, changed_h, scale)
                    cost_time = perf_counter() - start
                    reference = cdist(new_fg / scale, new_fh / scale, 'sqeuclidean')
                    np.testing.assert_allclose(costs, reference, rtol=0, atol=0)
                    for k in config['candidate_sizes']:
                        start = perf_counter()
                        candidates, dirty = update_candidates(old_lists[k], costs, changed_g, changed_h, old, k)
                        candidate_time = perf_counter() - start
                        assert candidates == candidate_lists(reference, old, k)
                        for detector, sg, sh in [('support', support_g, support_h), ('exact_feature', changed_g, changed_h)]:
                            detected = dependency_seeds(sg, sh, old, old_lists[k], candidates)
                            start = perf_counter()
                            affected, stats = conflict_closure(detected, candidates, old)
                            closure_time = perf_counter() - start
                            # Closure must admit all candidate targets, using only old targets of A.
                            targets = {int(old[u]) for u in affected}
                            assert all(candidates[u] <= targets for u in affected)
                            row = {'seed': seed, 'split': 'development' if seed in config['development_seeds'] else 'holdout',
                                'n': n, 'update_side': side, 'requested_fraction': fraction,
                                'realized_fraction': budget / (g.number_of_edges() + h.number_of_edges()),
                                'edits': budget, 'source_edits': source_count, 'target_edits': target_count,
                                'k': k, 'detector': detector, 'initial_nc': float(np.mean(old == truth)),
                                'full_nc': float(np.mean(new == truth)), 'changed_mappings': len(changed),
                                'seed_region_size': len(detected), 'closure_expansion': len(affected) / len(detected) if detected else None,
                                'cost_entries_rescored': rescored, 'candidate_rows_refreshed': len(dirty),
                                'cost_time': cost_time, 'candidate_time': candidate_time,
                                'closure_time': closure_time, 'full_runtime': full['runtime'],
                                'candidate_refresh_matches_full': True, 'cost_refresh_matches_full': True,
                                'missed_changed_vertices': sorted(changed - affected), **stats,
                                **detection(affected, changed, n)}
                            stream.write(json.dumps(row)+'\n')
                    stream.flush()
            print(f'Finished seed {seed}', flush=True)
    Path(output).with_suffix('.metadata.json').write_text(json.dumps({'config': config,
        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
        'platform': platform.platform(), 'scope': 'dense cached costs and full descriptor oracle; detection only'}, indent=2))


if __name__ == '__main__':
    run(json.loads(Path('configs/e01_detection.json').read_text()), 'results/raw/e01_detection.jsonl')
