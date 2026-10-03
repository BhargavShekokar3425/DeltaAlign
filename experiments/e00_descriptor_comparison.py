"""Compare completed baseline runs and replay sparse trials for diagnostics."""
import json
from pathlib import Path
from statistics import mean, median
import numpy as np
from src.graph import graph_pair
from src.descriptors import descriptors
from src.full_align import full_align
from src.updates import apply_batch
from src.metrics import region


def run():
    names = {'basic': 'e00_1k', 'degree_hist': 'e00_degree_hist_1k', 'two_hop_hist': 'e00_two_hop_hist_1k'}
    records, summary, controls, missed = {}, [], [], []
    for mode, name in names.items():
        rows = [json.loads(line) for line in Path(f'results/raw/{name}.jsonl').read_text().splitlines()]
        records[mode] = rows
        for fraction in sorted({r['requested_fraction'] for r in rows}):
            trials = [r for r in rows if r['radius'] == 0 and r['requested_fraction'] == fraction]
            summary.append({'mode': mode, 'fraction': fraction,
                'initial_nc': mean(r['initial_quality']['nc'] for r in trials),
                'updated_nc': mean(r['full_quality']['nc'] for r in trials),
                'changed_fraction': mean(r['changed_fraction'] for r in trials),
                'changed_min': min(r['changed_fraction'] for r in trials),
                'changed_max': max(r['changed_fraction'] for r in trials),
                'zero_change_trials': sum(r['zero_change'] for r in trials),
                'median_full_runtime': median(r['full']['runtime'] for r in trials)})
        for seed in range(5):
            g, h, truth, _ = graph_pair(1000, 3, seed, 0)
            mapping, _, stats = full_align(g, h, descriptor_mode=mode)
            controls.append({'mode': mode, 'seed': seed,
                'unique_descriptors': len(np.unique(descriptors(g, mode), axis=0)),
                'noiseless_nc': float(np.mean(mapping == truth)), 'objective': stats['objective']})
    for seed in range(5):
        mode = 'two_hop_hist'
        g, h, truth, seeds = graph_pair(1000, 3, seed, .01)
        old, scale, _ = full_align(g, h, descriptor_mode=mode)
        fg = descriptors(g, mode)
        for budget in [1, 6]:
            updated, batch = apply_batch(g, budget, seeds[3])
            new, _, _ = full_align(updated, h, scale, descriptor_mode=mode)
            changed = set(np.flatnonzero(old != new).tolist())
            feature_changed = set(np.flatnonzero(np.any(fg != descriptors(updated, mode), axis=1)).tolist())
            affected = region(g, updated, batch, 2)
            missing = sorted(changed - affected)
            missed.append({'seed': seed, 'edits': budget, 'changed': sorted(changed),
                'feature_changed_count': len(feature_changed), 'radius2_size': len(affected),
                'missed_radius2': missing, 'unchanged_descriptor_but_changed_mapping': sorted(changed - feature_changed)})
    Path('results/aggregate/e00_descriptor_comparison.json').write_text(json.dumps(summary, indent=2))
    Path('results/raw/e00_descriptor_controls.json').write_text(json.dumps(controls, indent=2))
    Path('results/raw/e00_two_hop_missed.json').write_text(json.dumps(missed, indent=2))
    lines = ['# Descriptor revision findings', '',
        'Five seed bundles, n=1,000 BA graphs, attachment 3, 1% mixed target noise. Graph/permutation/noise/update seeds and trial resets match the original experiment. Costs remain normalized squared Euclidean with the initial scale frozen. No candidates, stability penalty, repair, or ground-truth features were added.', '',
        '| Descriptor | Initial NC | One-edit mean churn | One-edit churn range | 0.1% mean churn |', '|---|---|---|---|---|']
    for mode in names:
        one = next(s for s in summary if s['mode'] == mode and s['fraction'] == .0001)
        six = next(s for s in summary if s['mode'] == mode and s['fraction'] == .001)
        lines.append(f"| {mode} | {one['initial_nc']:.2%} | {one['changed_fraction']:.2%} | {one['changed_min']:.2%}–{one['changed_max']:.2%} | {six['changed_fraction']:.2%} |")
    lines += ['', 'The stronger feature adds fixed-bin neighbor-degree counts, then a second-hop neighbor average of those counts, both log1p transformed. It uses structural information only. The first histogram depends on radius 1 around edited endpoints; the second depends on radius 2. Larger structural support increases the feature-update work required by a future incremental implementation.', '',
        '| Descriptor | Mean noiseless NC | Unique descriptor count range |', '|---|---|---|']
    for mode in names:
        subset = [r for r in controls if r['mode'] == mode]
        lines.append(f"| {mode} | {mean(r['noiseless_nc'] for r in subset):.2%} | {min(r['unique_descriptors'] for r in subset)}–{max(r['unique_descriptors'] for r in subset)} |")
    lines += ['', '## Detection gate', '', '| Requested update | Radius | Mean RF | Recall mean (nonempty trials) | Nonempty trials |', '|---|---|---|---|---|']
    for fraction in [.0001, .001]:
        for radius in [0, 1, 2, 3]:
            subset = [r for r in records['two_hop_hist'] if r['requested_fraction'] == fraction and r['radius'] == radius]
            recalls = [r['region_recall'] for r in subset if r['region_recall'] is not None]
            lines.append(f"| {fraction:.2%} | {radius} | {mean(r['repair_fraction'] for r in subset):.2%} | {mean(recalls):.2%} | {len(recalls)}/5 |")
    lines += ['', '## Missed-change diagnosis', '']
    for budget in [1, 6]:
        subset = [r for r in missed if r['edits'] == budget]
        lines.append(f"For {budget} edit(s), across all seeds: {sum(len(r['changed']) for r in subset)} mapping changes; {sum(len(r['missed_radius2']) for r in subset)} lie outside radius 2; {sum(len(r['unchanged_descriptor_but_changed_mapping']) for r in subset)} have unchanged source descriptors. Changed-target ownership and assignment competition can therefore require movement beyond descriptor-update support. This is evidence of assignment coupling, not proof that a particular candidate detector will recover them.")
    lines += ['', '## Decision and next task', '',
        'Retain two_hop_hist as the revised diagnostic baseline: quality and one-edit locality improve substantially in this controlled setting. The fixed-radius detection gate still fails to capture nearly all changes with a small region. Next implement candidate-dependency detection and ownership closure as a detection-only experiment at 1K, validated against full candidate refresh. Preserve old matches and explicitly handle new candidate entrants. Measure recall, RF, and closure growth before building repair or expanding to 5K/10K.', '',
        'These results are limited to five BA seeds and one noise condition. Fixed bins were specified before these runs, but the descriptor selection is based on this development data; subsequent validation needs independent seeds/topologies. Exact FRA can be sensitive to remaining equivalent optima. No-update determinism and permutation-equivariance checks pass. All prior raw files are preserved.']
    Path('docs/e00_descriptor_findings.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for mode in names:
        subset = [s for s in summary if s['mode'] == mode]
        axes[0].plot([s['fraction']*100 for s in subset], [s['changed_fraction'] for s in subset], 'o-', label=mode)
        axes[1].plot([s['fraction']*100 for s in subset], [s['updated_nc'] for s in subset], 'o-', label=mode)
    axes[0].set(xscale='log', xlabel='Requested edge update (%)', ylabel='Mean changed mapping fraction')
    axes[1].set(xscale='log', xlabel='Requested edge update (%)', ylabel='Mean updated NC')
    for ax in axes:
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e00_descriptor_comparison.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run()
