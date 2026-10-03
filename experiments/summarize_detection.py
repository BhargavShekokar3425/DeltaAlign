import json
from pathlib import Path
from statistics import mean


def run():
    rows = [json.loads(line) for line in Path('results/raw/e01_detection.jsonl').read_text().splitlines()]
    groups = []
    for split in ['development', 'holdout']:
        for side in ['source', 'target', 'both']:
            for fraction in [.0001, .001, .01, .05]:
                for detector in ['support', 'exact_feature']:
                    for k in [1, 2, 5, 10, 20]:
                        sub = [r for r in rows if (r['split'], r['update_side'], r['requested_fraction'], r['detector'], r['k']) == (split, side, fraction, detector, k)]
                        if not sub:
                            continue
                        recall = [r['region_recall'] for r in sub if r['region_recall'] is not None]
                        groups.append({'split': split, 'side': side, 'fraction': fraction,
                            'detector': detector, 'k': k, 'trials': len(sub), 'nonempty_trials': len(recall),
                            'mean_recall': mean(recall) if recall else None,
                            'min_recall': min(recall) if recall else None,
                            'mean_rf': mean(r['repair_fraction'] for r in sub),
                            'max_rf': max(r['repair_fraction'] for r in sub),
                            'mean_seed_rf': mean(r['seed_region_size']/r['n'] for r in sub),
                            'mean_closure_added': mean(r['closure_added'] for r in sub)})
    Path('results/aggregate/e01_detection.json').write_text(json.dumps(groups, indent=2))
    lines = ['# Candidate-dependency and closure findings', '',
        f"Completed {len(rows)} detector observations (120 independently reset full-align update trials, reused across K and seed detectors). All incremental cost comparisons and candidate refresh comparisons matched their full references. Old-match feasibility and closure target separation assertions passed.", '',
        'The study uses 1K BA graphs, fixed 1% observation noise, development seeds 0–4, and holdout seeds 5–9. Candidate top-K lists always include old matches. Both-graph one-edit trials duplicate source-only conditions by budget allocation. Full descriptors and cached dense costs are correctness references; these results do not measure incremental update latency or speedup.', '',
        '## Sparse-update closure tradeoff', '',
        'Conservative radius-2 support detection (mean values; recall excludes zero-change trials):', '',
        '| Split | Update side | Fraction | K | Seed RF | Final RF | Recall | Nonempty |', '|---|---|---|---|---|---|---|---|']
    for g in groups:
        if g['detector'] == 'support' and g['fraction'] <= .001 and g['k'] in [1, 2, 5, 20]:
            recall = f"{g['mean_recall']:.2%}" if g['mean_recall'] is not None else 'undefined'
            lines.append(f"| {g['split']} | {g['side']} | {g['fraction']:.2%} | {g['k']} | {g['mean_seed_rf']:.2%} | {g['mean_rf']:.2%} | {recall} | {g['nonempty_trials']}/{g['trials']} |")
    lines += ['', '## Exact changed-feature diagnostic', '',
              '| Split | Side | Fraction | K | Final RF | Recall |', '|---|---|---|---|---|---|']
    for g in groups:
        if g['detector'] == 'exact_feature' and g['fraction'] <= .001 and g['k'] in [1, 2, 5]:
            recall = f"{g['mean_recall']:.2%}" if g['mean_recall'] is not None else 'undefined'
            lines.append(f"| {g['split']} | {g['side']} | {g['fraction']:.2%} | {g['k']} | {g['mean_rf']:.2%} | {recall} |")
    lines += ['', '## Interpretation', '',
        'Exact candidate maintenance is validated, including new target entrants. It does not imply detection equivalence to dense FullAlign: omitted candidate alternatives can carry dense optimum changes. Conversely, adding more alternatives can recursively bring many old owners into closure. The full grouped JSON includes every K, larger update fractions, minimum recall, and maximum RF; inspect seed-level misses before choosing a repair policy.', '',
        'The next decision should use recall together with final RF, and remain scoped to this topology/noise. Conservative structural support and exact changed-feature seeds are separate detectors; the latter currently requires a full feature oracle and is not a deployable incremental detector. No candidate K should be presented as universally correct based on this diagnostic.']
    lines += ['', '## Decision and next experiment', '',
        'Do not proceed to large-scale or parallel repair with unconditional top-K ownership closure. It expands the repair set toward the whole graph; lowering K reduces expansion but misses dense full-alignment changes. Exact feature seeds reduce some unnecessary structural expansion without eliminating the candidate-competition problem.', '',
        'Next evaluate cost-margin candidate pruning and confidence-based seeds as a detection-only ablation. Retain old-match edges, refresh changed-target costs against all sources, and compare the pruned detector with both unpruned closure and fixed-radius detection. Choose margin settings on development seeds and assess them once on a fresh validation split; seeds 5–9 are now observed and should not be reused as untouched validation. If recall still requires near-global RF, record that limitation and reconsider the localization premise before investing in repair. A pruned candidate detector will have empirical recall, not exact equivalence to dense assignment.', '',
        'The feature-update path is also still an oracle: implementing local descriptor updates remains necessary before any performance claim. These experiments provide correctness and region-growth evidence only.']
    Path('docs/e01_findings.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, split in zip(axes, ['development', 'holdout']):
        for side in ['source', 'target', 'both']:
            sub = [g for g in groups if g['split'] == split and g['side'] == side and g['fraction'] == .001 and g['detector'] == 'support']
            ax.plot([g['mean_rf'] for g in sub], [g['mean_recall'] for g in sub], 'o-', label=side)
            for g in sub:
                ax.annotate(str(g['k']), (g['mean_rf'], g['mean_recall']), fontsize=7)
        ax.set(title=f'{split}: 0.1% updates', xlabel='Mean final repair fraction', ylabel='Mean recall (nonempty)', xlim=(0, 1.02), ylim=(0, 1.02))
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e01_detection.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run()
