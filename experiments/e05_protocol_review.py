"""Shared-latent/independent observation update review with fixed controls."""
import hashlib
import json
import platform
from pathlib import Path
import networkx as nx
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.normalized_align import full_align
from src.update_protocols import paired_updates, observation_mask
from src.updates import apply_batch
from src.metrics import region, detection, quality
from src.candidates import candidate_lists, refresh_costs, dependency_seeds
from src.candidate_pruning import (ranked_targets, refresh_rankings, pruned_candidates,
                                  refresh_pruned_candidates, confidence_seeds)
from src.conflict_closure import conflict_closure
from src.local_assignment import restricted_assignment
from src.repair_metrics import objective, fidelity


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_selection(selection):
    if digest('configs/e02_pruning.json') != selection['config_hash']:
        raise RuntimeError('Original E02 configuration changed')
    if digest('results/raw/e02_development.jsonl') != selection['development_result_hash']:
        raise RuntimeError('Original development evidence changed')
    # New diagnostic modules are allowed; original detector modules must match.
    for path, expected in selection['source_hashes'].items():
        if digest(path) != expected:
            raise RuntimeError(f'Original frozen source changed: {path}')


def run():
    config_path = 'configs/e05_protocol_review.json'
    output_stem = 'e05_protocol_review'
    normalization = 'unit_constant'
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    selection = json.loads(Path(config['selection_path']).read_text())
    check_selection(selection)
    p = selection['selected']
    n, mode = config['nodes'], config['descriptor_mode']
    rows_written = 0
    with Path(f'results/raw/{output_stem}.jsonl').open('w') as stream:
        for noise in config['noise_levels']:
            split = 'fresh'
            for seed in config['seeds']:
                g, h, truth, seeds = graph_pair(n, config['attachment'], seed, noise)
                old, scale, _ = full_align(g, h, descriptor_mode=mode)
                initial_mask = observation_mask(g, h, truth)
                fg, fh = descriptors(g, mode), descriptors(h, mode)
                constant_dims = np.flatnonzero(np.vstack([fg, fh]).std(axis=0) <= 1e-12)
                dimensions = fg.shape[1]
                old_costs = cdist(fg / scale, fh / scale, 'sqeuclidean')
                old_rank = ranked_targets(old_costs, p['k'])
                old_pruned = pruned_candidates(old_costs, old, p['k'], p['margin'], dimensions, old_rank)
                old_k5 = candidate_lists(old_costs, old, 5)
                inverse = np.empty(n, dtype=int)
                inverse[old] = np.arange(n)
                for fraction in config['update_fractions']:
                    source_count = max(1, int(fraction * (g.number_of_edges()+h.number_of_edges())/2 + .5))
                    budget = 2*source_count
                    for side in config['protocols']:
                        target_seed = int(np.random.SeedSequence(seeds[3]).generate_state(1)[0])
                        new_g, new_h, gb, hb = paired_updates(g, h, truth, source_count, seeds[3], target_seed, side)
                        updated_mask = observation_mask(new_g, new_h, truth)
                        if side == 'shared_latent':
                            assert updated_mask == initial_mask
                        assert sum(map(len, gb.values())) == sum(map(len, hb.values())) == source_count
                        full, _, full_stats = full_align(new_g, new_h, scale, descriptor_mode=mode)
                        new_fg, new_fh = descriptors(new_g, mode), descriptors(new_h, mode)
                        cg = set(np.flatnonzero(np.any(fg != new_fg, axis=1)).tolist())
                        ch = set(np.flatnonzero(np.any(fh != new_fh, axis=1)).tolist())
                        sg, sh = region(g, new_g, gb, 2), region(h, new_h, hb, 2)
                        assert cg <= sg and ch <= sh
                        costs, _ = refresh_costs(old_costs, new_fg, new_fh, cg, ch, scale)
                        np.testing.assert_array_equal(costs, cdist(new_fg / scale, new_fh / scale, 'sqeuclidean'))
                        ranks, dirty = refresh_rankings(old_rank, costs, cg, ch)
                        candidates = refresh_pruned_candidates(old_pruned, costs, old, p['k'], p['margin'], dimensions, ranks, dirty)
                        assert candidates == pruned_candidates(costs, old, p['k'], p['margin'], dimensions)
                        pool = dependency_seeds(cg, ch, old, old_pruned, candidates)
                        if p['detector'] == 'support':
                            pool = dependency_seeds(sg, sh, old, old_pruned, candidates)
                        seed_region = pool
                        if p['detector'] == 'confidence':
                            seed_region, _ = confidence_seeds(pool, old_costs, costs, old, dimensions, p['threshold'])
                        selected_a, _ = conflict_closure(seed_region, candidates, old)
                        k5 = candidate_lists(costs, old, 5)
                        k5_pool = dependency_seeds(sg, sh, old, old_k5, k5)
                        k5_a, _ = conflict_closure(k5_pool, k5, old)
                        local_a = sg | {int(inverse[v]) for v in sh}
                        changed = set(np.flatnonzero(old != full).tolist())
                        methods = [('selected_pruned', selected_a, candidates),
                                   ('selected_dense', selected_a, None),
                                   ('unpruned_k5', k5_a, k5),
                                   ('unpruned_region_dense', k5_a, None),
                                   ('local2', local_a, None)]
                        solutions = {}
                        for name, affected, allowed in methods:
                            mapping, timing = restricted_assignment(costs, old, affected, allowed)
                            solutions[name] = (mapping, timing, affected)
                        solutions['keep_old'] = (old, {'restricted_solve_time': None}, set())
                        solutions['full'] = (full, {'restricted_solve_time': None}, set(range(n)))
                        jp = objective(costs, solutions['selected_pruned'][0])
                        jd = objective(costs, solutions['selected_dense'][0])
                        jf = objective(costs, full)
                        tolerance = 1e-10 * max(1, jp, jd, jf)
                        assert jp >= jd-tolerance
                        assert objective(costs, solutions['unpruned_k5'][0]) >= objective(costs, solutions['unpruned_region_dense'][0])-tolerance
                        np.testing.assert_allclose(jf, full_stats['objective'], rtol=1e-12, atol=1e-12)
                        full_quality = quality(new_g, new_h, full, truth)
                        old_quality = quality(new_g, new_h, old, truth)
                        base = {'seed': seed, 'split': split, 'n': n, 'update_side': side,
                            'normalization': normalization, 'constant_dimensions': constant_dims.tolist(),
                            'newly_active_constant_dimensions': [int(d) for d in constant_dims if np.vstack([new_fg, new_fh])[:, d].std() > 1e-12],
                            'requested_fraction': fraction, 'realized_fraction': budget/(g.number_of_edges()+h.number_of_edges()),
                            'edits': budget, 'source_edits': source_count, 'target_edits': budget-source_count,
                            'frozen_policy': p, 'changed_mappings': len(changed),
                            'initial_noise': noise, 'initial_mask_size': len(initial_mask),
                            'updated_mask_size': len(updated_mask), 'mask_changed_edges': len(initial_mask ^ updated_mask),
                            'latent_edits': source_count if side == 'shared_latent' else None,
                            'source_insertions': len(gb['inserted']), 'source_deletions': len(gb['deleted']),
                            'target_insertions': len(hb['inserted']), 'target_deletions': len(hb['deleted']),
                            'full_quality': full_quality,
                            'keep_old_quality': old_quality, 'full_pipeline_time': full_stats['runtime'],
                            'selected_candidate_loss': max(0., jp-jd),
                            'selected_region_loss': max(0., jd-jf)}
                        for name, (mapping, timing, affected) in solutions.items():
                            q = quality(new_g, new_h, mapping, truth)
                            row = {**base, 'method': name, 'quality': q, **timing,
                                'nc_difference_vs_full': q['nc']-full_quality['nc'],
                                's3_difference_vs_full': q['s3']-full_quality['s3'],
                                'nc_difference_vs_keep_old': q['nc']-old_quality['nc'],
                                's3_difference_vs_keep_old': q['s3']-old_quality['s3'],
                                'old_errors_corrected': int(np.sum((old != truth) & (mapping == truth))),
                                'old_correct_matches_broken': int(np.sum((old == truth) & (mapping != truth))),
                                'bijection_verified': True, 'frozen_mapping_verified': True,
                                **detection(affected, changed, n), **fidelity(costs, mapping, full, old)}
                            stream.write(json.dumps(row)+'\n')
                            rows_written += 1
                        stream.flush()
                print(f'noise={noise}: finished seed {seed}', flush=True)
    paths = sorted(Path('src').glob('*.py')) + [Path(__file__)]
    Path(f'results/raw/{output_stem}.metadata.json').write_text(json.dumps({
        'config': config, 'config_hash': digest(config_path), 'selection_hash': digest(config['selection_path']),
        'source_hashes': {str(path): digest(path) for path in paths}, 'rows': rows_written,
        'python': platform.python_version(), 'platform': platform.platform(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'networkx': nx.__version__,
        'normalization': normalization,
        'scope': 'restricted objective-quality diagnostic; full feature and dense-cost oracles; no end-to-end speedup'}, indent=2))


if __name__ == '__main__':
    run()
