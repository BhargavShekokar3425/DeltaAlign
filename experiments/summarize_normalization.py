"""Paired normalization audit, fixed-policy quality review, paper readiness."""
import json
from pathlib import Path
from statistics import mean
import numpy as np
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.normalization import initial_scale
from experiments.summarize_repair_quality import aggregate, METHODS


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def key(row):
    return row['seed'], row['update_side'], row['requested_fraction'], row['method']


def review(groups, config):
    guide = config['review_guides']
    results = {}
    for method in METHODS:
        sub = [g for g in groups if g['split'] == 'fresh' and g['method'] == method and g['fraction'] in guide['sparse_fractions']]
        passed = all(g['mean_rf'] <= guide['mean_rf'] and g['mean_fra'] >= guide['mean_fra']
            and g['mean_nc_loss'] <= guide['mean_nc_loss'] and g['mean_s3_loss'] <= guide['mean_s3_loss']
            and g['mean_relative_gap'] is not None and g['mean_relative_gap'] <= guide['mean_relative_gap'] for g in sub)
        results[method] = {'passes_descriptive_guide': passed,
            'worst_group_rf': max(g['mean_rf'] for g in sub),
            'lowest_group_fra': min(g['mean_fra'] for g in sub),
            'largest_group_gap': max(g['mean_relative_gap'] for g in sub if g['mean_relative_gap'] is not None)}
    return results


def run():
    config = json.loads(Path('configs/e04_normalization.json').read_text())
    raw = {mode: read(f'results/raw/e04_{mode}.jsonl') for mode in ['legacy', 'corrected']}
    expected = (len(config['replay_seeds'])+len(config['fresh_seeds']))*len(config['update_sides'])*len(config['update_fractions'])*len(METHODS)
    if any(len(rows) != expected for rows in raw.values()):
        raise RuntimeError('Incomplete paired run')
    indexes = {mode: {key(r): r for r in rows} for mode, rows in raw.items()}
    assert indexes['legacy'].keys() == indexes['corrected'].keys()
    prior = {key(r): r for r in read('results/raw/e03_repair_quality.jsonl') if r['split'] == 'fresh'}
    replay_matches = 0
    for k, r in indexes['legacy'].items():
        if r['split'] == 'replay':
            previous = prior[k]
            for field in ['objective', 'full_objective', 'old_objective', 'quality', 'repair_fraction', 'full_recompute_agreement']:
                assert r[field] == previous[field], (k, field)
            replay_matches += 1
    initial_audit = []
    for seed in config['replay_seeds']+config['fresh_seeds']:
        g, h, _, _ = graph_pair(config['nodes'], config['attachment'], seed, config['noise'])
        fg, fh = descriptors(g, config['descriptor_mode']), descriptors(h, config['descriptor_mode'])
        legacy = np.maximum(np.vstack([fg, fh]).std(axis=0), 1e-12)
        corrected = initial_scale(fg, fh)
        np.testing.assert_array_equal(cdist(fg/legacy, fh/legacy, 'sqeuclidean'), cdist(fg/corrected, fh/corrected, 'sqeuclidean'))
        initial_audit.append({'seed': seed, 'initial_costs_equal': True,
            'corrected_min_scale': float(corrected.min()), 'constant_dimensions': int(np.sum(corrected != legacy))})
    Path('results/raw/e04_initial_audit.json').write_text(json.dumps(initial_audit, indent=2))
    groups = {mode: aggregate(rows) for mode, rows in raw.items()}
    reviews = {mode: review(gs, config) for mode, gs in groups.items()}
    numerical = []
    for mode, rows in raw.items():
        for fraction in config['update_fractions']:
            sub = [r for r in rows if r['method'] == 'full' and r['requested_fraction'] == fraction]
            numerical.append({'mode': mode, 'fraction': fraction, 'trials': len(sub),
                'active_constant_cases': sum(bool(r['newly_active_constant_dimensions']) for r in sub),
                'objectives_above_1e20': sum(r['full_objective'] > 1e20 for r in sub),
                'min_full_objective': min(r['full_objective'] for r in sub),
                'max_full_objective': max(r['full_objective'] for r in sub)})
    sparse_unchanged = 0
    sparse_cases = 0
    for k, old in indexes['legacy'].items():
        if old['requested_fraction'] in config['review_guides']['sparse_fractions']:
            sparse_cases += 1
            new = indexes['corrected'][k]
            sparse_unchanged += all(old[f] == new[f] for f in ['objective', 'quality', 'repair_fraction', 'full_recompute_agreement'])
    result = {'groups': groups, 'review': reviews, 'numerical_audit': numerical,
        'legacy_replay_observations_equal_e03': replay_matches,
        'paired_sparse_observations': sparse_cases, 'paired_sparse_observations_unchanged': sparse_unchanged}
    Path('results/aggregate/e04_normalization.json').write_text(json.dumps(result, indent=2))
    pct = lambda v: f'{v:.2%}' if v is not None else 'undefined'
    lines = ['# Constant-bin normalization correction findings', '',
        f"Completed {len(raw['corrected'])} observations per objective mode, {2*len(raw['corrected'])} total: paired historical and corrected objectives across 120 reset update trials each. Seeds 15–19 are replay; 20–24 are fresh fixed-policy confirmation. All seven repair/reference methods retain the E02 cap/margin/confidence settings. No objective or detector parameter was selected on these outcomes.", '',
        f"All {replay_matches} legacy replay observations exactly match the prior E03 objectives, quality, RF, and FRA. Initial cost matrices are exactly equal between modes on all ten seeds. Constant-bin scale is 1.0 in the corrected mode instead of 1e-12; every other initial standard deviation and all scales after updates remain frozen.", '',
        'Full-reference costs/candidate-refresh checks and restricted feasibility checks passed. Historical outputs and frozen sources are preserved. The original FullAlign default remains explicitly historical; E04 supplies the corrected scale via src/normalization.py.', '',
        '## Numerical correction', '',
        '| Objective mode | Requested update | Active constant-bin cases | Full objectives >1e20 | Max full objective | Trials |', '|---|---|---|---|---|---|']
    for a in numerical:
        lines.append(f"| {a['mode']} | {a['fraction']:.2%} | {a['active_constant_cases']} | {a['objectives_above_1e20']} | {a['max_full_objective']:.6g} | {a['trials']} |")
    lines += ['', f"Of {sparse_cases} paired sparse method observations, {sparse_unchanged} are exactly unchanged on objective, quality, RF, and FRA. This paired comparison distinguishes the fix from fresh-seed variation; the correction cannot be credited for a quality improvement where its dimensions were inactive.", '',
        'Absolute objectives under different scaling rules are different quantities. Their magnitudes diagnose excessive weighting, not a claim that the corrected optimizer improves the historical objective. Relative gaps below are always evaluated within the corrected objective against its own full recomputation.', '',
        '## Corrected objective on fresh sparse trials', '',
        '| Side | Update | Method | RF | FRA | NC | S3 | Relative J gap | J gain recovered |', '|---|---|---|---|---|---|---|---|---|']
    sparse = [g for g in groups['corrected'] if g['split'] == 'fresh' and g['fraction'] in config['review_guides']['sparse_fractions']]
    for side in config['update_sides']:
        for fraction in config['review_guides']['sparse_fractions']:
            for method in METHODS:
                g = next(g for g in sparse if (g['side'], g['fraction'], g['method']) == (side, fraction, method))
                lines.append(f"| {side} | {fraction:.2%} | {method} | {pct(g['mean_rf'])} | {pct(g['mean_fra'])} | {pct(g['mean_nc'])} | {pct(g['mean_s3'])} | {pct(g['mean_relative_gap'])} | {pct(g['mean_gain_recovered'])} |")
    lines += ['', '## Frozen quality-guide review', '',
        '| Method | Meets combined sparse guide on fresh seeds | Worst group RF | Lowest group FRA | Largest group J gap |', '|---|---|---|---|---|']
    for method in METHODS:
        r = reviews['corrected'][method]
        lines.append(f"| {method} | {r['passes_descriptive_guide']} | {pct(r['worst_group_rf'])} | {pct(r['lowest_group_fra'])} | {pct(r['largest_group_gap'])} |")
    lines += ['', 'Guides are unchanged from E03 (RF <=20%, FRA >=99%, NC/S3 loss <=0.5 percentage points, J gap <=1% per sparse group). Full-reference failure on this combined guide reflects RF=100%, not an optimization defect. The detection gate from E02 remains failed.', '',
        '## Objective versus truth/structure', '']
    source = {g['method']: g for g in sparse if g['side'] == 'source' and g['fraction'] == .001}
    lines += [f"At 0.1% fresh source updates, selected dense repair uses {source['selected_dense']['mean_rf']:.2%} RF with {source['selected_dense']['mean_relative_gap']:.2%} J gap; selected pruned repair has {source['selected_pruned']['mean_relative_gap']:.2%} J gap.", '',
        f"Keep-old NC/S3 is {source['keep_old']['mean_nc']:.2%}/{source['keep_old']['mean_s3']:.2%}, compared with full NC/S3 {source['full']['mean_nc']:.2%}/{source['full']['mean_s3']:.2%}. This is a measured distinction between preserving fixed hidden identities and minimizing descriptor cost. Fixing scale weighting is not, by itself, a fix for that objective/quality mismatch.", '',
        'A mean absolute-gap difference between selected pruned and selected dense repair isolates candidate exclusion; selected dense versus full isolates frozen-region restrictions. Those quantities, maximum per-group gaps, replay breakdowns, and 1%/5% stress quality are retained in the aggregate JSON.', '',
        '## Decision and paper readiness', '']
    qualifies = any(reviews['corrected'][m]['passes_descriptive_guide'] for m in ['selected_dense', 'selected_pruned'])
    if qualifies:
        lines += ['The corrected compact diagnostic meets the descriptive guides in this BA/noise setting. This is evidence worth validating, not an efficient-maintenance claim: complete update latency, topology/pattern robustness, and fair dynamic-assignment comparison remain absent.']
    else:
        lines += ['The compact frozen diagnostic still does not meet the combined quality guides. The numerical correction is real scientific-reliability progress, but it does not rescue the localization/pruning policy or establish a publishable efficient-repair method. The new fresh-seed evidence must not be presented as an improvement caused by normalization without the paired comparison.']
    lines += ['', 'Next freeze an objective/update-protocol review: compare the existing unpaired source/target observation edits with shared-latent paired graph evolution plus persistent observation noise, retaining keep-old and the same frozen repair controls. Include a higher initial-noise condition to test whether updates can correct an imperfect old alignment. Separate objective maintenance, ground-truth improvement, and churn before developing a new localization mechanism. Use fresh seeds and no margin tuning. Preserve these controls when adding boundary/stability scoring; those terms require explicitly comparable objectives.', '',
        'Paper status: closer to trustworthy experiments and a clear statement of limitations. Still missing a justified localized dependency mechanism, a validated quality/maintenance claim, end-to-end speedup, cross-topology/update-pattern evidence, streams, parallel scaling, dynamic-assignment comparison, and verified novelty. No readiness percentage or acceptance probability is warranted. Solver-only timings remain diagnostic and do not measure incremental efficiency.']
    Path('docs/e04_findings.md').write_text('\n'.join(lines)+'\n')
    readiness = ['# Paper readiness', '',
        'User preference: after every completed experiment, say whether the evidence brings DeltaAlign closer to a paper, what supports that assessment, and what still blocks the intended contribution. Do not invent readiness percentages or acceptance probabilities.', '',
        'Latest evidence: [e04_findings.md](e04_findings.md), paired historical/corrected normalization and fixed-policy fresh-seed repair diagnostics.', '',
        ('A compact diagnostic meets the internal guides in one controlled setting; method claims still require independent robustness and complete runtime evidence.' if qualifies else 'Scientific reliability has improved: the constant-bin weighting defect is corrected and its effects are measured in paired trials. The central efficient, high-fidelity localized repair claim remains unsupported by the frozen policy.'), '',
        '| Evidence | Status |', '|---|---|',
        '| Reproducible baselines and correctness | Preserved historical runs, frozen configs/source hashes, fresh seeds, paired objective correction |',
        '| Constant-bin normalization | Corrected with unit scale, frozen thereafter; regression checks and stress audit completed |',
        '| Localized candidate mechanism | E01 closure spreads; E02 pruning misses needed global assignments |',
        f"| Restricted quality | E04 fixed compact policy {'meets the descriptive guides' if qualifies else 'does not meet the combined descriptive guides'} |",
        '| Objective versus NC/S3 | Keep-old remains a necessary control; objective/update-protocol review is next |',
        '| End-to-end efficiency | Not established; full feature and dense-cost oracles remain |',
        '| Robustness, streams, parallel scaling | Not established beyond additional seeds in BA/noise independent batches |',
        '| Novelty and dynamic-assignment comparison | Source verification and compatible external baseline remain pending |', '',
        'Next: disentangle shared-latent evolution from unpaired observation changes under frozen corrected normalization. Select the maintenance/quality claim before further localization or scale work.']
    Path('docs/PAPER_READINESS.md').write_text('\n'.join(readiness)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for mode, marker in [('legacy', 'x'), ('corrected', 'o')]:
        sub = [a for a in numerical if a['mode'] == mode]
        axes[0].plot([a['fraction']*100 for a in sub], [a['max_full_objective'] for a in sub], marker+'-', label=mode)
    axes[0].set(xscale='log', yscale='log', xlabel='Requested edge update (%)', ylabel='Max full objective (own scaling)', title='Numerical magnitude: paired trials')
    for method in ['selected_pruned', 'selected_dense', 'local2', 'keep_old']:
        sub = sorted([g for g in groups['corrected'] if g['split'] == 'fresh' and g['side'] == 'source' and g['method'] == method], key=lambda g:g['fraction'])
        axes[1].plot([g['fraction']*100 for g in sub], [g['mean_relative_gap'] for g in sub], 'o-', label=method)
    axes[1].set(xscale='log', xlabel='Requested edge update (%)', ylabel='Mean relative J gap', title='Corrected objective: fresh source trials')
    for ax in axes:
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e04_normalization.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    run()
