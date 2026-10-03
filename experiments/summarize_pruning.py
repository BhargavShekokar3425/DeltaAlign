"""Summarize the frozen-policy development and fresh validation experiment."""
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def grouped(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r['policy']['id'], r['update_side'], r['requested_fraction'])].append(r)
    output = []
    for (policy, side, fraction), sub in sorted(groups.items()):
        recalls = [r['region_recall'] for r in sub if r['region_recall'] is not None]
        coverage = [r['changed_candidate_coverage'] for r in sub if r.get('changed_candidate_coverage') is not None]
        upper_bounds = [1-len(set(r['missed_changed_vertices']) | set(r.get('excluded_full_changed_vertices', [])))/1000 for r in sub]
        output.append({'policy': policy, 'side': side, 'fraction': fraction, 'trials': len(sub),
            'nonempty': len(recalls), 'mean_recall': mean(recalls) if recalls else None,
            'min_recall': min(recalls) if recalls else None,
            'mean_rf': mean(r['repair_fraction'] for r in sub),
            'mean_seed_rf': mean(r['seed_size']/1000 for r in sub),
            'mean_candidate_coverage': mean(coverage) if coverage else None,
            'candidate_exclusions': sum(len(r.get('excluded_full_changed_vertices', [])) for r in sub),
            'mean_fra_upper_bound': mean(upper_bounds)})
    return output


def run():
    selection = json.loads(Path('results/aggregate/e02_selection.json').read_text())
    policy = selection['selected']
    validation_rows = [json.loads(line) for line in Path('results/raw/e02_validation.jsonl').read_text().splitlines()]
    development_rows = [json.loads(line) for line in Path('results/raw/e02_development.jsonl').read_text().splitlines()]
    aggregates = {}
    for stage, rows in [('development', development_rows), ('validation', validation_rows)]:
        aggregates[stage] = grouped(rows)
    config = json.loads(Path('configs/e02_pruning.json').read_text())
    sparse = [r for r in validation_rows if r['policy']['id'] == policy['id'] and r['requested_fraction'] in config['selection']['sparse_fractions']]
    val_groups = [g for g in aggregates['validation'] if g['policy'] == policy['id'] and g['fraction'] in config['selection']['sparse_fractions']]
    gate = config['selection']
    recalls = [r['region_recall'] for r in sparse if r['region_recall'] is not None]
    passed = (max(g['mean_rf'] for g in val_groups) <= gate['max_group_mean_rf']
        and all(g['mean_recall'] is None or g['mean_recall'] >= gate['min_group_mean_recall'] for g in val_groups)
        and min(recalls) >= gate['min_trial_recall']
        and sum(len(r['excluded_full_changed_vertices']) for r in sparse) == 0)
    aggregates['validation_gate_passed'] = passed
    Path('results/aggregate/e02_pruning.json').write_text(json.dumps(aggregates, indent=2))
    lines = ['# Margin pruning and confidence-seed findings', '',
        '## Prior evidence and controlled experiment', '',
        'E01 K=5 closure needed about 95% of the graph for approximately 97% recall at 0.1% source updates. E02 changes candidate and seed admission while preserving descriptors, frozen normalization, graph generation, and edit rules. It remains a detection-only study with dense cached costs and a full descriptor oracle.', '',
        f"Development: {len(development_rows)} observations, 60 policy settings plus two controls on 60 reset trials (seeds 0–4). Validation: {len(validation_rows)} observations, one frozen setting plus two controls on 60 fresh reset trials (seeds 10–14). Both-graph one-edit trials duplicate source-only trials and are reported separately, not pooled as independent evidence.", '',
        'All cached cost, ranking, and candidate comparisons matched full refresh. Every retained list includes its old match; closure target-separation assertions passed. No mapping or optimum truth was used to construct the detector.', '',
        '## Frozen selection', '',
        f"Selected cap K={policy['k']}, mean-per-feature cost margin={policy['margin']}, seed policy={policy['detector']}, pressure threshold={policy['threshold']}.", '',
        f"Selection status: `{selection['status']}`. Qualifying development settings: {selection['qualifying_settings']} of {selection['settings_tested']}. Configuration, detector-source, and development-result hashes were saved before validation; validation checked the config and source hashes. Validation gate passed: **{passed}**.", '',
        'The development rule sought <=20% worst-group mean RF, >=95% group mean recall, >=90% minimum nonempty-trial recall, and no changed full-match target excluded from candidates. These are internal guides. If none qualified, the frozen choice maximized recall under the RF budget; if no setting fit that budget, it minimized worst-group RF. Either fallback is explicitly exploratory.', '',
        '| Stage | Side | Requested update | Method | Seed RF | Final RF | Recall | Changed-target coverage | Nonempty |',
        '|---|---|---|---|---|---|---|---|---|']
    def pct(x):
        return f'{x:.2%}' if x is not None else 'undefined'
    for stage in ['development', 'validation']:
        for g in aggregates[stage]:
            if g['fraction'] <= .001 and g['policy'] in [policy['id'], 'control:unpruned_k5', 'control:radius2']:
                label = 'selected' if g['policy'] == policy['id'] else g['policy'].replace('control:', '')
                lines.append(f"| {stage} | {g['side']} | {g['fraction']:.2%} | {label} | {g['mean_seed_rf']:.2%} | {g['mean_rf']:.2%} | {pct(g['mean_recall'])} | {pct(g['mean_candidate_coverage'])} | {g['nonempty']}/{g['trials']} |")
    lines += ['', '## Meaning and limits', '',
        'Region recall and candidate coverage are separate necessary conditions for matching the dense reference: a changed vertex may be detected while its full target has been pruned. Mean changed-target coverage reports that distinction. The grouped JSON also reports an analytical upper bound on FRA from the union of missed vertices and excluded targets; this is not observed repair accuracy. A high bound does not establish that a restricted solver attains it.', '',
        'Row-best margins are sensitive to global assignment competition: a globally optimal match need not be the row-wise nearest target. Confidence filtering reduces seeds but can drop low-pressure vertices required in a permutation cycle. Large-update (1% and 5%) results are retained in raw/grouped files; they were not used to select the sparse-update policy. No speedup, objective-gap, or local-repair quality was measured.', '',
        '## Decision and next step', '']
    if not passed or not selection['qualifying_settings']:
        lines += ['The predeclared dense-recovery gate is not satisfied. Do not scale this pruning policy or claim exact-maintenance fidelity. Preserve the negative result: unconditional closure grows too widely, while row-wise pruning and pressure seeds trade recovery for compactness.', '',
            'Next run a small objective-fidelity diagnostic on the frozen selected region/candidates, the unpruned closure control, and fixed-radius repair. Solve each restricted assignment while retaining old-match edges, then compare NC, S3, FRA, and the same full objective including absolute/relative gaps. Also include repair on the selected region with all old-image targets to separate detection losses from candidate-pruning losses. This tests whether missed dense mappings materially harm quality rather than changing the detection gate after seeing results. It is a diagnostic review of the formulation, not approval to proceed to production/parallel repair. If quality losses remain material, revisit the objective or candidate localization approach. Use fresh evaluation seeds for any new parameter selection; 10–14 are now observed.']
    else:
        lines += ['The frozen policy passed the internal validation gate in this BA/noise setting. Next build a small restricted-repair pilot and measure objective quality before expanding scale or topology. This is not universal validation.']
    Path('docs/e02_findings.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    scored = json.loads(Path('results/aggregate/e02_development_settings.json').read_text())
    for detector in ['support', 'exact_feature', 'confidence']:
        sub = [s for s in scored if s['policy']['detector'] == detector]
        axes[0].scatter([s['worst_group_rf'] for s in sub], [s['worst_group_recall'] for s in sub], label=detector, s=20)
    axes[0].axvline(.2, color='gray', linestyle='--')
    axes[0].axhline(.95, color='gray', linestyle='--')
    axes[0].set(title='Development settings', xlabel='Worst group mean RF', ylabel='Worst group mean recall', xlim=(0,1), ylim=(0,1))
    for side in config['update_sides']:
        sub = [g for g in aggregates['validation'] if g['side'] == side and g['policy'] == policy['id'] and g['fraction'] <= .001]
        axes[1].plot([g['mean_rf'] for g in sub], [g['mean_recall'] for g in sub], 'o-', label=side)
    axes[1].set(title='Frozen policy: fresh validation', xlabel='Mean RF', ylabel='Mean recall (nonempty)', xlim=(0,1), ylim=(0,1))
    for ax in axes:
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e02_pruning.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run()
