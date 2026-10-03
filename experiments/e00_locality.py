"""Run from repository root: python3 -m experiments.e00_locality."""
import argparse
import json
import platform
from pathlib import Path
import networkx as nx
import numpy as np
import scipy
from src.graph import graph_pair
from src.updates import apply_batch
from src.full_align import full_align
from src.metrics import quality, region, detection


def run(config, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w') as stream:
        for n in config['nodes']:
            for seed in config['seeds']:
                g, h, truth, seeds = graph_pair(n, config['attachment'], seed, config['noise'])
                mode = config.get('descriptor_mode', 'basic')
                old, scale, initial = full_align(g, h, descriptor_mode=mode)
                repeat, _, _ = full_align(g, h, scale, descriptor_mode=mode)
                if not np.array_equal(old, repeat):
                    raise RuntimeError('No-update determinism check failed')
                random = np.random.default_rng(seeds[1] + 1).permutation(n)
                control = {'n': n, 'seed': seed, 'seeds': seeds, 'descriptor_mode': mode, 'initial': initial,
                           'initial_quality': quality(g, h, old, truth),
                           'random_quality': quality(g, h, random, truth)}
                for fraction in config['update_fractions']:
                    budget = max(1, int(fraction * (g.number_of_edges() + h.number_of_edges()) + 0.5))
                    updated, batch = apply_batch(g, budget, seeds[3])
                    new, _, full = full_align(updated, h, scale, descriptor_mode=mode)
                    changed = set(np.flatnonzero(old != new).tolist())
                    base = {**control, 'requested_fraction': fraction,
                            'realized_fraction': budget / (g.number_of_edges() + h.number_of_edges()),
                            'update_edges': budget, 'insertions': len(batch['inserted']),
                            'deletions': len(batch['deleted']), 'changed_mappings': len(changed),
                            'changed_fraction': len(changed) / n, 'zero_change': not changed,
                            'full': full, 'full_quality': quality(updated, h, new, truth)}
                    for radius in config['radii']:
                        row = {**base, 'radius': radius,
                               **detection(region(g, updated, batch, radius), changed, n)}
                        stream.write(json.dumps(row) + '\n')
                    stream.flush()
                    print(f'n={n} seed={seed} edits={budget} changed={len(changed)} NC={base["full_quality"]["nc"]:.3f}', flush=True)
    output.with_suffix('.metadata.json').write_text(json.dumps({
        'config': config, 'python': platform.python_version(), 'platform': platform.platform(),
        'numpy': np.__version__, 'scipy': scipy.__version__, 'networkx': nx.__version__}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/e00_locality.json')
    parser.add_argument('--output', default='results/raw/e00_locality.jsonl')
    parser.add_argument('--nodes', type=int, nargs='+')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.nodes:
        config['nodes'] = args.nodes
    run(config, args.output)
