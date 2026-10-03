"""Development sweep, frozen selection, and one fresh validation run."""
import argparse
import hashlib
import json
import platform
from collections import defaultdict
from pathlib import Path
from statistics import mean
from time import perf_counter
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.full_align import full_align
from src.updates import apply_batch
from src.metrics import region, detection
from src.candidates import candidate_lists, refresh_costs, dependency_seeds
from src.candidate_pruning import (ranked_targets, refresh_rankings, pruned_candidates,
                                  refresh_pruned_candidates, confidence_seeds)
from src.conflict_closure import conflict_closure

CONFIG = Path('configs/e02_pruning.json')
SELECTION = Path('results/aggregate/e02_selection.json')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    paths = list(Path('src').glob('*.py')) + [Path(__file__)]
    return {str(p): file_hash(p) for p in sorted(paths)}


def settings(config):
    result = []
    for k in config['candidate_caps']:
        for margin in config['cost_margins']:
            for detector, threshold in [('support', None), ('exact_feature', None)] + [('confidence', t) for t in config['confidence_thresholds']]:
                result.append({'id': f'{k}:{margin}:{detector}:{threshold}', 'k': k,
                               'margin': margin, 'detector': detector, 'threshold': threshold})
    return result


def measure(config, stage):
    if stage == 'development':
        policies = settings(config)
        seeds_to_run = config['development_seeds']
    else:
        frozen = json.loads(SELECTION.read_text())
        if frozen['config_hash'] != file_hash(CONFIG) or frozen['source_hashes'] != source_hashes():
            raise RuntimeError('Configuration/source changed after selection; refreeze before validation')
        policies = [frozen['selected']]
        seeds_to_run = config['validation_seeds']
        if set(seeds_to_run) & (set(config['development_seeds']) | set(range(5, 10))):
            raise ValueError('Validation seeds overlap previously inspected seeds')
    output = Path(f'results/raw/e02_{stage}.jsonl')
    output.parent.mkdir(parents=True, exist_ok=True)
    n, mode = config['nodes'], config['descriptor_mode']
    with output.open('w') as stream:
        for seed in seeds_to_run:
            g, h, truth, seeds = graph_pair(n, config['attachment'], seed, config['noise'])
            old, scale, initial = full_align(g, h, descriptor_mode=mode)
            fg, fh = descriptors(g, mode), descriptors(h, mode)
            dimensions = fg.shape[1]
            old_costs = cdist(fg / scale, fh / scale, 'sqeuclidean')
            old_rank = ranked_targets(old_costs, max(config['candidate_caps']))
            old_lists = {(p['k'], p['margin']): pruned_candidates(old_costs, old, p['k'], p['margin'], dimensions, old_rank) for p in policies}
            old_control = candidate_lists(old_costs, old, 5)
            for fraction in config['update_fractions']:
                budget = max(1, int(fraction * (g.number_of_edges() + h.number_of_edges()) + .5))
                for side in config['update_sides']:
                    source_count = budget if side == 'source' else (0 if side == 'target' else (budget + 1) // 2)
                    new_g, gb = apply_batch(g, source_count, seeds[3])
                    target_seed = int(np.random.SeedSequence(seeds[3]).generate_state(1)[0])
                    new_h, hb = apply_batch(h, budget - source_count, target_seed)
                    new, _, full = full_align(new_g, new_h, scale, descriptor_mode=mode)
                    changed = set(np.flatnonzero(old != new).tolist())
                    new_fg, new_fh = descriptors(new_g, mode), descriptors(new_h, mode)
                    cg = set(np.flatnonzero(np.any(fg != new_fg, axis=1)).tolist())
                    ch = set(np.flatnonzero(np.any(fh != new_fh, axis=1)).tolist())
                    sg, sh = region(g, new_g, gb, 2), region(h, new_h, hb, 2)
                    assert cg <= sg and ch <= sh
                    costs, work = refresh_costs(old_costs, new_fg, new_fh, cg, ch, scale)
                    reference = cdist(new_fg / scale, new_fh / scale, 'sqeuclidean')
                    np.testing.assert_array_equal(costs, reference)
                    rankings, dirty = refresh_rankings(old_rank, costs, cg, ch)
                    reference_rank = ranked_targets(reference, max(config['candidate_caps']))
                    np.testing.assert_array_equal(rankings, reference_rank)
                    lists = {}
                    for k, margin in old_lists:
                        candidates = refresh_pruned_candidates(old_lists[k, margin], costs, old, k, margin, dimensions, rankings, dirty)
                        assert candidates == pruned_candidates(reference, old, k, margin, dimensions, reference_rank)
                        assert all(int(old[u]) in candidates[u] for u in range(n))
                        lists[k, margin] = candidates
                    base = {'stage': stage, 'seed': seed, 'update_side': side,
                        'requested_fraction': fraction, 'realized_fraction': budget / (g.number_of_edges() + h.number_of_edges()),
                        'edits': budget, 'source_edits': source_count, 'target_edits': budget-source_count,
                        'initial_nc': float(np.mean(old == truth)), 'full_nc': float(np.mean(new == truth)),
                        'changed_mappings': len(changed), 'cost_entries_rescored': work,
                        'ranking_rows_refreshed': len(dirty), 'full_runtime': full['runtime'],
                        'costs_match_full': True, 'rankings_match_full': True}
                    evaluations = []
                    for p in policies:
                        candidates = lists[p['k'], p['margin']]
                        seed_g, seed_h = (sg, sh) if p['detector'] == 'support' else (cg, ch)
                        pool = dependency_seeds(seed_g, seed_h, old, old_lists[p['k'], p['margin']], candidates)
                        selected_seeds = pool
                        if p['detector'] == 'confidence':
                            selected_seeds, _ = confidence_seeds(pool, old_costs, costs, old, dimensions, p['threshold'])
                        evaluations.append((p, candidates, selected_seeds, len(pool)))
                    control_candidates = candidate_lists(costs, old, 5)
                    control_seeds = dependency_seeds(sg, sh, old, old_control, control_candidates)
                    evaluations.append(({'id': 'control:unpruned_k5', 'detector': 'control', 'k': 5, 'margin': None, 'threshold': None}, control_candidates, control_seeds, len(control_seeds)))
                    inverse = np.empty(n, dtype=int)
                    inverse[old] = np.arange(n)
                    fixed_region = sg | {int(inverse[v]) for v in sh}
                    for p, candidates, initial_seeds, pool_size in evaluations:
                        start = perf_counter()
                        affected, stats = conflict_closure(initial_seeds, candidates, old)
                        closure_time = perf_counter()-start
                        targets = {int(old[u]) for u in affected}
                        assert all(candidates[u] <= targets for u in affected)
                        excluded = sorted(u for u in changed if int(new[u]) not in candidates[u])
                        row = {**base, 'policy': p, 'dependency_pool_size': pool_size,
                            'seed_size': len(initial_seeds), 'closure_time': closure_time,
                            'full_match_candidate_coverage': float(np.mean([int(new[u]) in candidates[u] for u in range(n)])),
                            'changed_candidate_coverage': 1-len(excluded)/len(changed) if changed else None,
                            'excluded_full_changed_vertices': excluded,
                            'mean_candidate_size': mean(len(c) for c in candidates),
                            'candidates_match_full': True, 'missed_changed_vertices': sorted(changed-affected),
                            **stats, **detection(affected, changed, n)}
                        stream.write(json.dumps(row)+'\n')
                    stream.write(json.dumps({**base, 'policy': {'id': 'control:radius2', 'detector': 'control'},
                        'seed_size': len(fixed_region), 'closure_added': 0,
                        'missed_changed_vertices': sorted(changed-fixed_region),
                        **detection(fixed_region, changed, n)})+'\n')
                    stream.flush()
            print(f'{stage}: finished seed {seed}', flush=True)
    output.with_suffix('.metadata.json').write_text(json.dumps({'config': config, 'config_hash': file_hash(CONFIG),
        'source_hashes': source_hashes(), 'selected_policy': policies if stage == 'validation' else None,
        'python': platform.python_version(), 'platform': platform.platform(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'scope': 'detection only; full feature oracle; dense cached costs'}, indent=2))


def select(config):
    rows = [json.loads(line) for line in Path('results/raw/e02_development.jsonl').read_text().splitlines()]
    scored = []
    for policy in settings(config):
        sub = [r for r in rows if r['policy']['id'] == policy['id'] and r['requested_fraction'] in config['selection']['sparse_fractions']]
        by_group = defaultdict(list)
        for r in sub:
            by_group[r['update_side'], r['requested_fraction']].append(r)
        if len(sub) != len(config['development_seeds'])*len(config['selection']['sparse_fractions'])*len(config['update_sides']):
            raise RuntimeError('Incomplete development sweep')
        group_recalls = [mean(r['region_recall'] for r in group if r['region_recall'] is not None)
                         for group in by_group.values() if any(r['region_recall'] is not None for r in group)]
        recalls = [r['region_recall'] for r in sub if r['region_recall'] is not None]
        scored.append({'policy': policy,
            'worst_group_rf': max(mean(r['repair_fraction'] for r in group) for group in by_group.values()),
            'worst_group_recall': min(group_recalls), 'min_trial_recall': min(recalls),
            'candidate_exclusions': sum(len(r['excluded_full_changed_vertices']) for r in sub)})
    gate = config['selection']
    qualifying = [s for s in scored if s['worst_group_rf'] <= gate['max_group_mean_rf'] and s['worst_group_recall'] >= gate['min_group_mean_recall']
                  and s['min_trial_recall'] >= gate['min_trial_recall'] and s['candidate_exclusions'] == 0]
    if qualifying:
        chosen = min(qualifying, key=lambda s: (s['worst_group_rf'], -s['worst_group_recall'], s['policy']['id']))
        status = 'development_gate_passed'
    else:
        compact = [s for s in scored if s['worst_group_rf'] <= gate['max_group_mean_rf']]
        if compact:
            chosen = min(compact, key=lambda s: (-s['worst_group_recall'], -s['min_trial_recall'], s['worst_group_rf'], s['policy']['id']))
        else:
            chosen = min(scored, key=lambda s: (s['worst_group_rf'], -s['worst_group_recall'], s['policy']['id']))
        status = 'exploratory_development_gate_failed'
    frozen = {'selected': chosen['policy'], 'status': status, 'development_metrics': chosen,
        'qualifying_settings': len(qualifying), 'settings_tested': len(scored), 'config_hash': file_hash(CONFIG),
        'source_hashes': source_hashes(), 'development_result_hash': file_hash('results/raw/e02_development.jsonl')}
    SELECTION.write_text(json.dumps(frozen, indent=2))
    Path('results/aggregate/e02_development_settings.json').write_text(json.dumps(scored, indent=2))
    print(json.dumps({k: v for k, v in frozen.items() if k not in ['source_hashes']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['development', 'select', 'validation'], required=True)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    if args.stage == 'select':
        select(config)
    else:
        measure(config, args.stage)
