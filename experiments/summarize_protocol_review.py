"""Update-semantics review with keep-old and paper-readiness checks."""
import json
from pathlib import Path
from statistics import mean
from experiments.summarize_repair_quality import aggregate, METHODS


def run():
    config = json.loads(Path('configs/e05_protocol_review.json').read_text())
    rows = [json.loads(line) for line in Path('results/raw/e05_protocol_review.jsonl').read_text().splitlines()]
    expected = len(config['seeds'])*len(config['noise_levels'])*len(config['update_fractions'])*len(config['protocols'])*len(METHODS)
    if len(rows) != expected:
        raise RuntimeError('Incomplete protocol review')
    groups = []
    for noise in config['noise_levels']:
        sub = [r for r in rows if r['initial_noise'] == noise]
        for g in aggregate(sub):
            cases = [r for r in sub if r['update_side']==g['side'] and r['requested_fraction']==g['fraction'] and r['method']==g['method']]
            g.update({'noise': noise, 'mean_realized_fraction': mean(r['realized_fraction'] for r in cases),
                'mean_nc_vs_keep_old': mean(r['nc_difference_vs_keep_old'] for r in cases),
                'mean_s3_vs_keep_old': mean(r['s3_difference_vs_keep_old'] for r in cases),
                'old_errors_corrected_total': sum(r['old_errors_corrected'] for r in cases),
                'old_correct_broken_total': sum(r['old_correct_matches_broken'] for r in cases),
                'mean_full_changed_mappings': mean(r['changed_mappings'] for r in cases),
                'zero_full_change_trials': sum(r['changed_mappings']==0 for r in cases),
                'mean_mask_changes': mean(r['mask_changed_edges'] for r in cases)})
            for r in cases:
                assert abs(r['nc_difference_vs_keep_old']-(r['old_errors_corrected']-r['old_correct_matches_broken'])/r['n']) < 1e-12
                assert r['source_edits'] == r['target_edits']
                if g['side']=='shared_latent':
                    assert r['mask_changed_edges']==0 and r['initial_mask_size']==r['updated_mask_size']
            groups.append(g)
    guide = config['review_guides']
    reviews = []
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            for method in METHODS:
                sub = [g for g in groups if g['noise']==noise and g['side']==protocol and g['method']==method and g['fraction'] in guide['sparse_fractions']]
                passed = all(g['mean_rf']<=guide['mean_rf'] and g['mean_fra']>=guide['mean_fra']
                    and g['mean_nc_loss']<=guide['mean_nc_loss'] and g['mean_s3_loss']<=guide['mean_s3_loss']
                    and g['mean_relative_gap'] is not None and g['mean_relative_gap']<=guide['mean_relative_gap'] for g in sub)
                reviews.append({'noise': noise, 'protocol': protocol, 'method': method, 'passes_guide': passed,
                    'worst_rf': max(g['mean_rf'] for g in sub), 'worst_fra': min(g['mean_fra'] for g in sub),
                    'worst_gap': max(g['mean_relative_gap'] for g in sub if g['mean_relative_gap'] is not None)})
    Path('results/aggregate/e05_protocol_review.json').write_text(json.dumps({'groups': groups, 'review': reviews}, indent=2))
    pct = lambda x: f'{x:.2%}' if x is not None else 'undefined'
    lines = ['# Update-protocol and objective review findings', '',
        f"Completed {len(rows)} method observations on 80 independently reset paired-condition trials: five fresh seeds 25–29, two initial-noise conditions, four requested update fractions, two protocols, and seven methods. Corrected normalization and the frozen E02 policy are unchanged. Noise/protocol conditions share graph/permutation/source-batch seeds; the independent replicates are the five seed bundles, not the 80 condition rows.", '',
        'Shared evolution preserves the exact XOR observation-noise mask. Independent balanced edits use the same source batch and a separate target batch. Both have matched effective source/target counts. All mask, actual-budget, cost/candidate-refresh, bijection, candidate feasibility, frozen-map, and objective-ordering checks pass.', '',
        'The hidden permutation is used only in data generation and evaluation. The detector/assignment inputs contain graphs, descriptors, candidate costs, and the old alignment. No stream, boundary/stability term, policy selection, or end-to-end speedup is introduced.', '',
        '## At requested 0.1% combined-edge updates', '',
        '| Initial noise | Protocol | Method | RF | FRA | NC | S3 | Relative J gap | Old errors corrected / correct matches broken |', '|---|---|---|---|---|---|---|---|---|']
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            for method in METHODS:
                g = next(g for g in groups if (g['noise'],g['side'],g['fraction'],g['method'])==(noise,protocol,.001,method))
                lines.append(f"| {noise:.0%} | {protocol} | {method} | {pct(g['mean_rf'])} | {pct(g['mean_fra'])} | {pct(g['mean_nc'])} | {pct(g['mean_s3'])} | {pct(g['mean_relative_gap'])} | {g['old_errors_corrected_total']} / {g['old_correct_broken_total']} |")
    lines += ['', 'Correction/break counts are totals across five 1K graphs, whereas quality values are per-seed means. Cases with no full mapping changes are counted explicitly in the aggregate JSON. Full-objective improvement is not evidence of improving the hidden identity mapping.', '',
        '## Unchanged sparse guide, including the keep-old control', '',
        '| Noise | Protocol | Method | Guide met | Worst mean RF | Lowest mean FRA | Largest mean J gap |', '|---|---|---|---|---|---|---|']
    for r in reviews:
        if r['method'] in ['selected_dense','selected_pruned','local2','keep_old']:
            lines.append(f"| {r['noise']:.0%} | {r['protocol']} | {r['method']} | {r['passes_guide']} | {pct(r['worst_rf'])} | {pct(r['worst_fra'])} | {pct(r['worst_gap'])} |")
    lines += ['', 'These are internal descriptive guides, not publication thresholds. Meeting them does not establish repair value if keep-old already meets them. Exact mapping differences can still include ties; J gaps and actual error corrections are reported alongside FRA.', '',
        '## Matched budgets and noise behavior', '',
        '| Noise | Protocol | Requested fraction | Mean realized fraction | Mean full mapping changes | Zero-change trials | Mean changed noise-mask edges |', '|---|---|---|---|---|---|---|']
    for g in groups:
        if g['method']=='full':
            lines.append(f"| {g['noise']:.0%} | {g['side']} | {g['fraction']:.2%} | {g['mean_realized_fraction']:.4%} | {g['mean_full_changed_mappings']:.1f} | {g['zero_full_change_trials']}/{g['trials']} | {g['mean_mask_changes']:.1f} |")
    lines += ['', '## Decision, contribution scope, and paper readiness', '',
        'Shared evolution supplies a low-noise regime with small-region, low-objective-gap repair. The no-repair control is already close to the full solution in that regime, so this is not yet a substantial incremental-repair contribution. More initial noise exposes imperfect prior correspondences and larger mapping churn; the frozen compact/pruned policies do not consistently recover the full behavior. Full descriptor optimization can correct some old errors while breaking more previously correct matches. The same descriptor objective should therefore not be presented as a proven ground-truth/edge-quality improvement.', '',
        'Use stated-objective maintenance as the provisional technical claim, with NC/S3 and keep-old as quality controls. Explicitly distinguish shared-latent evolution from unpaired observation changes in all future reporting. Any later boundary/stability objective must have a comparable full reference, and must demonstrate something beyond merely retaining the old alignment. The present row-best candidate policy is not the mechanism to scale.', '',
        'Next establish a compatible dynamic-assignment reference and an assignment-aware localization design. Review the original algorithm/source and its assumptions, implement and verify a small assignment-repair baseline on exactly these changed costs, and compare its full-objective fidelity and complete graph-to-cost/solver work with FullAlign and keep-old. Use fresh seeds for new settings. This directly addresses whether graph-specific localization adds value beyond existing assignment reuse, and avoids another uninformed margin sweep. Do not invent novelty claims before checking that literature.', '',
        'Paper progress: closer to a defensible problem formulation and useful operating-regime evidence. Still lacking a demonstrated nontrivial localized mechanism, end-to-end efficiency, cross-topology/update-pattern robustness, repeated-stream stability, parallel scaling, and verified novelty. A low-noise condition where keep-old nearly solves the problem cannot by itself justify the intended method paper.']
    Path('docs/e05_findings.md').write_text('\n'.join(lines)+'\n')
    readiness = ['# Paper readiness', '',
        'User preference: after each completed experiment, say whether the evidence brings DeltaAlign closer to a paper and identify the next blockers. Do not invent readiness percentages or acceptance probabilities.', '',
        'Latest evidence: [e05_findings.md](e05_findings.md), shared-latent versus independent balanced updates, fresh seeds 25–29, 1%/5% initial observation noise.', '',
        'Closer to a precise, defensible formulation. Shared low-noise evolution can be maintained near the full descriptor objective in a small region, but keep-old is already highly competitive. Higher noise exposes fidelity failures and truth/objective disagreement. A substantive repair-method contribution remains unproven.', '',
        '| Evidence needed | Current status |', '|---|---|',
        '| Reproducibility and feasibility | Historical results preserved, frozen policy, corrected normalization, paired budgets and mask checks |',
        '| Update semantics | Shared persistent-noise evolution distinguished from independent observation changes |',
        '| Useful incremental repair beyond keep-old | Some objective improvement, but no robust nontrivial advantage demonstrated |',
        '| Localized candidate mechanism | Unconditional closure spreads; row-best pruning excludes globally needed assignments |',
        '| Truth/structural quality | Full descriptor optimum often breaks more correct matches than it fixes; NC/S3 require controls |',
        '| Exact assignment reuse baseline/novelty | Next priority: verify and evaluate compatible dynamic-assignment reference |',
        '| End-to-end efficiency | Not established; full features/dense costs remain oracles |',
        '| Robustness, streams, and CPU scaling | BA seed/noise coverage only; broader topology/pattern/stream/parallel evidence pending |', '',
        'Next: dynamic-assignment reference and assignment-aware localization design under the stated objective, before scale or margin tuning.']
    Path('docs/PAPER_READINESS.md').write_text('\n'.join(readiness)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for i,noise in enumerate(config['noise_levels']):
        for j,protocol in enumerate(config['protocols']):
            ax=axes[i,j]
            for method in ['selected_dense','selected_pruned','keep_old','local2']:
                sub=sorted([g for g in groups if g['noise']==noise and g['side']==protocol and g['method']==method],key=lambda g:g['fraction'])
                ax.plot([g['mean_realized_fraction']*100 for g in sub],[g['mean_relative_gap'] for g in sub],'o-',label=method)
            ax.set(xscale='log',xlabel='Realized combined edge update (%)',ylabel='Mean relative objective gap',title=f'{noise:.0%} initial noise: {protocol}')
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig('results/figures/e05_protocol_review.png',dpi=160)
    plt.close(fig)


if __name__=='__main__':
    run()
