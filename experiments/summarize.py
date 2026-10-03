import argparse
import json
from pathlib import Path
from statistics import mean, median


def summarize(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    trials = [r for r in rows if r['radius'] == 0]
    lines = ['# E00 findings', '', 'This report is generated from the 1K diagnostic baseline. Results are pipeline-specific; no repair speedup has been measured.', '',
             f"Initial NC mean: {mean(r['initial_quality']['nc'] for r in trials):.3f}. Random-mapping NC mean: {mean(r['random_quality']['nc'] for r in trials):.3f}.", '',
             '| Requested update | Actual edits | Mean changed fraction | Mean updated NC | Median full solve (s) |',
             '|---|---|---|---|---|']
    aggregates = []
    for fraction in sorted({r['requested_fraction'] for r in rows}):
        group = [r for r in trials if r['requested_fraction'] == fraction]
        lines.append(f"| {fraction:.2%} | {min(r['update_edges'] for r in group)}–{max(r['update_edges'] for r in group)} | {mean(r['changed_fraction'] for r in group):.3f} | {mean(r['full_quality']['nc'] for r in group):.3f} | {median(r['full']['runtime'] for r in group):.4f} |")
        for radius in sorted({r['radius'] for r in rows}):
            subset = [r for r in rows if r['requested_fraction'] == fraction and r['radius'] == radius]
            recalls = [r['region_recall'] for r in subset if r['region_recall'] is not None]
            aggregates.append({'fraction': fraction, 'radius': radius,
                               'rf': mean(r['repair_fraction'] for r in subset),
                               'recall': mean(recalls) if recalls else None})
    lines += ['', '| Update | Radius | Mean RF | Mean recall (nonempty C*) |', '|---|---|---|---|']
    for item in aggregates:
        lines.append(f"| {item['fraction']:.2%} | {item['radius']} | {item['rf']:.3f} | {item['recall'] if item['recall'] is not None else 'undefined'} |")
    lines += ['', '## Decision', '',
              'Revise the baseline before implementing DeltaAlign. Although the descriptor assignment substantially exceeds random NC, sparse edits expose descriptor ambiguity and assignment cascades; this experiment does not yet establish high-fidelity localized repair. Inspect descriptor ties and missed changed vertices, then evaluate a stronger structural descriptor on the same saved protocol and seeds. Preserve this baseline as a diagnostic comparison. Do not conclude that all alignment methods lack locality from these results.', '',
              'No-update checks passed for each seed. Timing covers descriptors, cost construction, and assignment. Five independent seed bundles were used; raw observations remain in results/raw/e00_1k.jsonl. Larger-scale and candidate-closure experiments remain gated on this baseline review.']
    Path('docs/e00_findings.md').write_text('\n'.join(lines) + '\n')
    Path('results/aggregate/e00_1k.json').write_text(json.dumps(aggregates, indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for seed in sorted({r['seed'] for r in trials}):
        group = [r for r in trials if r['seed'] == seed]
        axes[0].plot([r['realized_fraction'] * 100 for r in group], [r['changed_fraction'] for r in group], 'o-', label=f'seed {seed}')
    axes[0].set(xscale='log', xlabel='Realized edge update (%)', ylabel='Changed mapping fraction')
    axes[0].legend(fontsize=7)
    for radius in sorted({a['radius'] for a in aggregates}):
        group = [a for a in aggregates if a['radius'] == radius and a['recall'] is not None]
        axes[1].plot([a['rf'] for a in group], [a['recall'] for a in group], 'o-', label=f'r={radius}')
    axes[1].set(xlabel='Mean repair fraction', ylabel='Mean region recall', xlim=(0, 1), ylim=(0, 1))
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e00_1k.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default='results/raw/e00_1k.jsonl')
    summarize(parser.parse_args().path)
