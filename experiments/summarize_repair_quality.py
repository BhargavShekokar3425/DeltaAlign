"""Summarize measured repair quality and maintain paper-readiness notes."""
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

METHODS = ['selected_pruned', 'selected_dense', 'unpruned_k5', 'unpruned_region_dense', 'local2', 'keep_old', 'full']


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r['split'], r['update_side'], r['requested_fraction'], r['method']].append(r)
    results = []
    for (split, side, fraction, method), sub in sorted(groups.items()):
        gaps = [r['relative_objective_gap'] for r in sub if r['relative_objective_gap'] is not None]
        gain = [r['objective_gain_recovered'] for r in sub if r['objective_gain_recovered'] is not None]
        timings = [r['restricted_solve_time'] for r in sub if r['restricted_solve_time'] is not None]
        results.append({'split': split, 'side': side, 'fraction': fraction, 'method': method,
            'trials': len(sub), 'mean_rf': mean(r['repair_fraction'] for r in sub),
            'mean_fra': mean(r['full_recompute_agreement'] for r in sub),
            'min_fra': min(r['full_recompute_agreement'] for r in sub),
            'mean_nc': mean(r['quality']['nc'] for r in sub),
            'mean_s3': mean(r['quality']['s3'] for r in sub),
            'mean_nc_vs_full': mean(r['nc_difference_vs_full'] for r in sub),
            'mean_s3_vs_full': mean(r['s3_difference_vs_full'] for r in sub),
            'mean_nc_loss': mean(max(0., -r['nc_difference_vs_full']) for r in sub),
            'mean_s3_loss': mean(max(0., -r['s3_difference_vs_full']) for r in sub),
            'mean_absolute_gap': mean(r['absolute_objective_gap'] for r in sub),
            'mean_relative_gap': mean(gaps) if gaps else None,
            'max_relative_gap': max(gaps) if gaps else None,
            'mean_gain_recovered': mean(gain) if gain else None, 'gain_defined_trials': len(gain),
            'mean_candidate_loss': mean(r['selected_candidate_loss'] for r in sub),
            'mean_region_loss': mean(r['selected_region_loss'] for r in sub),
            'median_solve_only_time': median(timings) if timings else None})
    return results


def run():
    config = json.loads(Path('configs/e03_repair_quality.json').read_text())
    rows = [json.loads(line) for line in Path('results/raw/e03_repair_quality.jsonl').read_text().splitlines()]
    expected = (len(config['replay_seeds'])+len(config['fresh_seeds']))*len(config['update_sides'])*len(config['update_fractions'])*len(METHODS)
    if len(rows) != expected:
        raise RuntimeError(f'Incomplete diagnostic: {len(rows)} vs {expected}')
    groups = aggregate(rows)
    guide = config['review_guides']
    sparse_fresh = [g for g in groups if g['split'] == 'fresh' and g['fraction'] in guide['sparse_fractions']]
    review = {}
    for method in METHODS:
        sub = [g for g in sparse_fresh if g['method'] == method]
        promising = (all(g['mean_rf'] <= guide['mean_rf'] and g['mean_fra'] >= guide['mean_fra']
                     and g['mean_nc_loss'] <= guide['mean_nc_loss'] and g['mean_s3_loss'] <= guide['mean_s3_loss']
                     and g['mean_relative_gap'] is not None and g['mean_relative_gap'] <= guide['mean_relative_gap'] for g in sub))
        review[method] = {'passes_descriptive_quality_guide': promising,
            'worst_group_rf': max(g['mean_rf'] for g in sub),
            'worst_group_mean_fra': min(g['mean_fra'] for g in sub),
            'worst_group_mean_gap': max(g['mean_relative_gap'] for g in sub if g['mean_relative_gap'] is not None)}
    Path('results/aggregate/e03_repair_quality.json').write_text(json.dumps({'groups': groups, 'review': review}, indent=2))
    pct = lambda v: f'{v:.2%}' if v is not None else 'undefined'
    lines = ['# Restricted-repair objective and quality findings', '',
        f"Completed {len(rows)} method observations on 120 reset update trials: five observed replay seeds (10–14) and five fresh fixed-policy seeds (15–19). The original frozen E02 detector/config/development hashes were verified. Every replay region/miss/candidate-exclusion matched E02. All restricted solves preserve bijection, old-match feasibility, and frozen mappings. Dense updated costs matched the reference.", '',
        'Seven methods share the same updated objective, descriptors, graph pairs, and batches. Full objective includes frozen rows. Old-match feasibility makes keeping the old mapping an available solution; checks establish J_full <= J_repair <= J_old. Selected dense repair cannot be worse in objective than selected pruned repair. This isolates candidate pruning from region restriction.', '',
        'Timings are matrix/mask construction and assignment only, using full descriptors and dense cost oracles. They are not end-to-end update latency or incremental speedup. Both-graph one-edit cases duplicate source-only conditions and are not independent repetitions.', '',
        '## Fresh sparse-update quality', '',
        '| Side | Requested update | Method | RF | FRA | NC | S3 | Relative J gap | Available J gain recovered |',
        '|---|---|---|---|---|---|---|---|---|']
    for side in config['update_sides']:
        for fraction in guide['sparse_fractions']:
            for method in METHODS:
                g = next(g for g in sparse_fresh if (g['side'], g['fraction'], g['method']) == (side, fraction, method))
                lines.append(f"| {side} | {fraction:.2%} | {method} | {pct(g['mean_rf'])} | {pct(g['mean_fra'])} | {pct(g['mean_nc'])} | {pct(g['mean_s3'])} | {pct(g['mean_relative_gap'])} | {pct(g['mean_gain_recovered'])} |")
    lines += ['', '## Candidate loss versus region loss', '',
        'Same selected region, identical dense objective. Absolute losses are sums of squared normalized descriptor distances:', '',
        '| Side | Requested update | Candidate restriction loss | Region restriction loss |', '|---|---|---|---|']
    for g in sparse_fresh:
        if g['method'] == 'selected_pruned':
            lines.append(f"| {g['side']} | {g['fraction']:.2%} | {g['mean_candidate_loss']:.6f} | {g['mean_region_loss']:.6f} |")
    lines += ['', 'Losses decompose as J_selected_pruned-J_full = (J_selected_pruned-J_selected_dense) + (J_selected_dense-J_full). Exact full-mapping agreement and hidden-truth correctness remain separate: the best descriptor assignment can lose NC after unpaired noisy graph updates even when its objective improves. Keep-old is essential for exposing that distinction.', '',
        '## Predeclared descriptive quality review', '',
        'The protocol recorded mean RF <=20%, FRA >=99%, mean NC/S3 loss <=0.5 percentage points, and relative gap <=1% per sparse side/fraction group before E03 outcomes. These are internal guides for more validation, not a revised detection gate or scientific success claim.', '',
        '| Method | Passes combined guide | Worst group RF | Lowest group mean FRA | Largest group mean J gap |', '|---|---|---|---|---|']
    for method in METHODS:
        r = review[method]
        lines.append(f"| {method} | {r['passes_descriptive_quality_guide']} | {pct(r['worst_group_rf'])} | {pct(r['worst_group_mean_fra'])} | {pct(r['worst_group_mean_gap'])} |")
    promising = review['selected_dense']['passes_descriptive_quality_guide'] or review['selected_pruned']['passes_descriptive_quality_guide']
    source_case = {g['method']: g for g in sparse_fresh if g['side'] == 'source' and g['fraction'] == .001}
    lines += ['', 'At 0.1% source updates on fresh seeds:', '',
        f"- Selected region RF: {source_case['selected_dense']['mean_rf']:.2%}; dense-within-region objective gap: {source_case['selected_dense']['mean_relative_gap']:.2%}; pruned objective gap: {source_case['selected_pruned']['mean_relative_gap']:.2%}.",
        f"- Keep-old NC/S3: {source_case['keep_old']['mean_nc']:.2%}/{source_case['keep_old']['mean_s3']:.2%}; full recomputation NC/S3: {source_case['full']['mean_nc']:.2%}/{source_case['full']['mean_s3']:.2%}.",
        '',
        'The discrepancy is important: reproducing this descriptor optimum and preserving hidden truth/edges are different goals. High NC alone can be achieved by doing no repair in this fixed-identity noisy-copy protocol. The combined guide includes RF, so failure of the full reference on that guide reflects global work, not inaccurate optimization.']
    audit_path = Path('results/raw/e03_normalization_audit.json')
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        lines += ['', '## Normalization audit', '',
            'The inherited scale rule sets initially constant dimensions to 1e-12. A previously empty degree bin becoming variable can therefore dominate squared distances. This audit preserves the original objective/detector and marks affected cases rather than silently fixing them inside the frozen comparison.', '',
            '| Update | Cases with newly variable floor dimensions | Cases with full J > 1e20 | Trials |', '|---|---|---|---|']
        for fraction in config['update_fractions']:
            subset = [r for r in audit if r['fraction'] == fraction]
            lines.append(f"| {fraction:.2%} | {sum(bool(r['newly_variable_floor_dimensions']) for r in subset)} | {sum(r['large_full_objective'] for r in subset)} | {len(subset)} |")
        lines += ['', 'Affected stress objectives must not support quality/crossover claims until normalization is corrected. Next fix the treatment of constant dimensions with a documented finite scale, run regression checks, and repeat fixed-policy baseline/repair comparisons under the revised objective on fresh seeds. Also review why descriptor-objective improvements reduce NC/S3 relative to keep-old. Freeze these choices before further localization work; do not tune pruning margins to hide the failure.']
    lines += ['', '## Decision and paper readiness', '']
    if promising:
        lines += ['The frozen compact-region diagnostic meets the descriptive quality guides on these fresh BA seeds. This moves DeltaAlign closer to a method paper by providing actual objective-fidelity evidence, but it does not erase the failed E02 detection gate. Next independently test other graph topologies/noise/update patterns without tuning, implement local feature maintenance, and measure complete update latency against the same full pipeline before claiming efficient maintenance.']
    else:
        lines += ['The compact frozen-policy diagnostic does not meet the combined quality guide. This moves the project closer to a defensible research conclusion by measuring the failure, but does not advance the central claim of compact, efficient, high-fidelity repair. Broad repair can improve objective fidelity at the cost of near-global regions; keeping old matches must be considered when interpreting high NC.', '',
            'After correcting the normalization issue and reviewing the objective against keep-old, revisit the localization/assignment interface rather than sweeping more row-best margins: determine whether permutation-cycle competition can be represented by objective-aware candidate dependencies with a correctness or approximation argument. Compare any revised mechanism with a compatible dynamic assignment baseline. Before a new method implementation, inspect individual worst cases and define a fixed validation protocol. If no credible mechanism emerges, test the limitations across topologies and position the work as an empirical characterization rather than claiming an efficient repair algorithm.']
    lines += ['', 'Only one graph family, one observation-noise setting, and small independent batches have been tested. End-to-end speedup, scaling, repeated-stream stability, boundary/stability ablations, dynamic-assignment comparison, and verified novelty positioning remain absent. No acceptance probability, readiness percentage, or publication guarantee is justified. Replay results, stress fractions, per-seed failures, and maximum relative gaps are retained in raw/aggregate artifacts.']
    Path('docs/e03_findings.md').write_text('\n'.join(lines)+'\n')
    readiness = ['# Paper readiness', '',
        'User preference: after each completed experiment, explicitly say whether the evidence brings DeltaAlign closer to a paper, why, and what still blocks the intended contribution. Do not substitute a guessed completion percentage or acceptance probability.', '',
        'Latest evidence: E03 restricted-repair quality diagnostic. See [e03_findings.md](e03_findings.md).', '',
        ('The compact diagnostic is promising in one controlled setting; a method-paper claim remains unproven.' if promising else 'The diagnostic foundation is stronger, but compact high-fidelity repair is still unproven. Current evidence is more useful for revising the method or characterizing limitations than for claiming its success.'), '',
        '| Required evidence | Current status |', '|---|---|',
        '| Reproducible experiments and feasibility checks | Implemented and tested; config/source hashes, controls, raw observations retained |',
        '| Meaningful initial alignment | Two-hop descriptor reaches about 99% NC on original BA/noise development cases |',
        '| Localized candidate/region mechanism | E01 closure spreads; E02 compact pruning fails detection/candidate-coverage gate |',
        f"| Actual restricted objective and mapping quality | E03 measured; compact quality guide {'met in this setting' if promising else 'not met'} |",
        '| Objective/normalization validity | Constant-bin scaling can dominate stress costs; keep-old outperforms the full descriptor optimum on NC/S3 in the fresh sparse-source example |',
        '| End-to-end update advantage | Not measured; full descriptors/dense costs remain oracles |',
        '| Robustness and independent validation | Fresh seeds used; graph-family/noise/pattern robustness still absent |',
        '| Shared-memory scalability and streams | Not implemented or evaluated |',
        '| Novelty and fair external baselines | Literature/source verification and dynamic-assignment comparison pending |', '',
        'Next priority: fix constant-dimension normalization and repeat fixed-policy comparisons; review the keep-old control before further localization or scaling.', '',
        'A paper arguing efficient maintenance needs a supported localization mechanism, comparable quality, and complete runtime evidence. An empirical limitations paper would require broader controlled coverage and a verified contribution beyond the current single-family results.']
    Path('docs/PAPER_READINESS.md').write_text('\n'.join(readiness)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for method in ['selected_pruned', 'selected_dense', 'unpruned_k5', 'local2', 'keep_old']:
        sub = sorted([g for g in groups if g['split'] == 'fresh' and g['side'] == 'source' and g['method'] == method and g['fraction'] in guide['sparse_fractions']], key=lambda g:g['fraction'])
        axes[0].plot([g['fraction']*100 for g in sub], [g['mean_relative_gap'] for g in sub], 'o-', label=method)
        axes[1].plot([g['fraction']*100 for g in sub], [g['mean_nc'] for g in sub], 'o-', label=method)
    full = sorted([g for g in groups if g['split'] == 'fresh' and g['side'] == 'source' and g['method'] == 'full' and g['fraction'] in guide['sparse_fractions']], key=lambda g:g['fraction'])
    axes[1].plot([g['fraction']*100 for g in full], [g['mean_nc'] for g in full], 'o--', color='black', label='full')
    axes[0].set(xscale='log', xlabel='Requested edge update (%)', ylabel='Mean relative objective gap', title='Fresh source updates: objective fidelity')
    axes[1].set(xscale='log', xlabel='Requested edge update (%)', ylabel='Mean NC', title='Fresh source updates: hidden-truth quality')
    for ax in axes:
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e03_repair_quality.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run()
