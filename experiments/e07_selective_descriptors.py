"""Frozen paired selective-feature benchmark; historical experiments untouched."""
import json
import os
import platform
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.descriptor_cache import initialize, update
from src.normalization import initial_scale
from src.update_protocols import paired_updates, observation_mask
from src.candidates import refresh_costs
from src.dynamic_assignment import solve, repair, certificate
from src.metrics import quality
from src.repair_metrics import fidelity
from experiments.e06_dynamic_assignment import digest


def dynamic_pipeline(initial_state, caches, old_graphs, new_graphs, batches, old_features, scale, selective):
    start = perf_counter()
    clone_start = perf_counter()
    state = initial_state.copy()
    local_caches = [cache.copy() for cache in caches] if selective else None
    clone_time = perf_counter()-clone_start
    feature_start = perf_counter()
    if selective:
        updates = [update(cache, old, new, batch) for cache, old, new, batch
                   in zip(local_caches, old_graphs, new_graphs, batches)]
        changed = [pair[0] for pair in updates]
        maintenance = [pair[1] for pair in updates]
        features = [cache.features for cache in local_caches]
    else:
        features = [descriptors(g, 'two_hop_hist') for g in new_graphs]
        changed = [set(np.flatnonzero(np.any(a != b, axis=1))) for a, b in zip(features, old_features)]
        maintenance = []
    feature_time = perf_counter()-feature_start
    cost_start = perf_counter()
    costs, rescored = refresh_costs(initial_state.costs, *features, *changed, scale)
    cost_time = perf_counter()-cost_start
    solver_start = perf_counter()
    state, stats = repair(state, costs, *changed)
    solver_time = perf_counter()-solver_start
    pipeline_time = perf_counter()-start
    return state, features, changed, dict(clone_time=clone_time, feature_time=feature_time,
        cost_time=cost_time, solver_time=solver_time, pipeline_time=pipeline_time,
        maintenance=maintenance, search_stats=stats, rescored_cost_entries=rescored)


def run():
    path = Path('configs/e07_selective_descriptors.json')
    config = json.loads(path.read_text())
    n = config['nodes']
    initialization = []
    trial = 0
    with Path('results/raw/e07_selective_descriptors.jsonl').open('w') as stream:
        for noise in config['noise_levels']:
            for seed in config['seeds']:
                g, h, truth, bundle = graph_pair(n, config['attachment'], seed, noise)
                start = perf_counter()
                fg, fh = descriptors(g, 'two_hop_hist'), descriptors(h, 'two_hop_hist')
                scale = initial_scale(fg, fh)
                costs = cdist(fg/scale, fh/scale, 'sqeuclidean')
                initial_cost_time = perf_counter()-start
                start = perf_counter()
                caches = [initialize(g), initialize(h)]
                cache_time = perf_counter()-start
                for cache, f in zip(caches, [fg, fh]):
                    np.testing.assert_array_equal(cache.features, f)
                start = perf_counter()
                initial_state, _ = solve(costs)
                initial_solver_time = perf_counter()-start
                certificate(initial_state, config['certificate_tolerance'])
                rr, cc = linear_sum_assignment(costs)
                np.testing.assert_allclose(costs[rr,cc].sum(), costs[np.arange(n),initial_state.mapping].sum(), rtol=1e-10, atol=1e-8)
                old = initial_state.mapping
                initialization.append(dict(seed=seed, noise=noise, initial_cost_time=initial_cost_time,
                    cache_time=cache_time, cache_bytes=sum(c.nbytes for c in caches),
                    dense_cost_bytes=costs.nbytes, initial_solver_time=initial_solver_time))
                for fraction in config['update_fractions']:
                    budget = max(1, int(fraction*(g.number_of_edges()+h.number_of_edges())/2+.5))
                    for protocol in config['protocols']:
                        target_seed = int(np.random.SeedSequence(bundle[3]).generate_state(1)[0])
                        ng, nh, gb, hb = paired_updates(g,h,truth,budget,bundle[3],target_seed,protocol)
                        if protocol == 'shared_latent':
                            assert observation_mask(g,h,truth) == observation_mask(ng,nh,truth)
                        start = perf_counter()
                        full_features = [descriptors(ng, 'two_hop_hist'), descriptors(nh, 'two_hop_hist')]
                        full_feature_time = perf_counter()-start
                        cost_start = perf_counter()
                        full_costs = cdist(full_features[0]/scale, full_features[1]/scale, 'sqeuclidean')
                        full_cost_time = perf_counter()-cost_start
                        solver_start = perf_counter()
                        rr, cc = linear_sum_assignment(full_costs)
                        scipy_solver_time = perf_counter()-solver_start
                        full_pipeline_time = perf_counter()-start
                        full = np.empty(n, dtype=int); full[rr] = cc
                        order = ['selective_dynamic','full_feature_dynamic'] if trial % 2 == 0 else ['full_feature_dynamic','selective_dynamic']
                        outputs = {}
                        for name in order:
                            outputs[name] = dynamic_pipeline(initial_state, caches, [g,h], [ng,nh], [gb,hb],
                                                            [fg,fh], scale, name=='selective_dynamic')
                        validation_start = perf_counter()
                        certs = {}
                        for name, (state, features, changed, timings) in outputs.items():
                            for new, expected in zip(features, full_features):
                                np.testing.assert_array_equal(new, expected)
                            for dirty, new, previous in zip(changed, full_features, [fg,fh]):
                                assert dirty == set(np.flatnonzero(np.any(new != previous, axis=1)))
                            np.testing.assert_array_equal(state.costs, full_costs)
                            certs[name] = certificate(state, config['certificate_tolerance'])
                        np.testing.assert_array_equal(outputs['selective_dynamic'][0].mapping, outputs['full_feature_dynamic'][0].mapping)
                        validation_time = perf_counter()-validation_start
                        select_time = outputs['selective_dynamic'][3]
                        oracle_time = outputs['full_feature_dynamic'][3]
                        common = dict(seed=seed, noise=noise, protocol=protocol, requested_fraction=fraction,
                            realized_fraction=2*budget/(g.number_of_edges()+h.number_of_edges()), edits=2*budget,
                            batch_counts=[{k:len(v) for k,v in b.items()} for b in [gb,hb]],
                            timing_order=order, validation_time=validation_time,
                            feature_speedup=oracle_time['feature_time']/select_time['feature_time'],
                            dynamic_pipeline_speedup=oracle_time['pipeline_time']/select_time['pipeline_time'],
                            scipy_pipeline_speedup=full_pipeline_time/select_time['pipeline_time'])
                        mappings = {name: output[0].mapping for name, output in outputs.items()}
                        mappings.update(scipy_full=full, keep_old=old)
                        for name, mapping in mappings.items():
                            timings = outputs[name][3] if name in outputs else (
                                dict(feature_time=full_feature_time, cost_time=full_cost_time,
                                     solver_time=scipy_solver_time, pipeline_time=full_pipeline_time) if name=='scipy_full' else {})
                            row = {**common, 'method':name, 'timings':timings,
                                   'quality':quality(ng,nh,mapping,truth), 'optimality_certificate':certs.get(name,{}),
                                   **fidelity(full_costs,mapping,full,old)}
                            if name in outputs:
                                assert row['absolute_objective_gap'] <= 1e-8*max(1.,row['full_objective'])
                            stream.write(json.dumps(row)+'\n')
                        stream.flush()
                        trial += 1
                print(f'noise={noise}: finished seed {seed}', flush=True)
    Path('results/raw/e07_initialization.json').write_text(json.dumps(initialization, indent=2))
    sources = sorted(Path('src').glob('*.py'))+[Path(__file__),Path('experiments/e06_dynamic_assignment.py')]
    Path('results/raw/e07_selective_descriptors.metadata.json').write_text(json.dumps(dict(config=config,
        config_hash=digest(path), source_hashes={str(p):digest(p) for p in sources},
        python=platform.python_version(), platform=platform.platform(), cpu_count=os.cpu_count(),
        numpy=np.__version__, scipy=scipy.__version__,
        scope='updated graphs to assignment; includes cloning/cache work; excludes edge application and validation'), indent=2))


if __name__ == '__main__':
    run()
