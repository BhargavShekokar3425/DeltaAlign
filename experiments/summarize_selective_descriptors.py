"""Paired E07 summaries, plots and findings."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from experiments.summarize_dynamic_assignment import distribution


def summarize():
    config = json.loads(Path('configs/e07_selective_descriptors.json').read_text())
    rows = [json.loads(line) for line in Path('results/raw/e07_selective_descriptors.jsonl').read_text().splitlines()]
    expected = len(config['seeds'])*len(config['noise_levels'])*len(config['protocols'])*len(config['update_fractions'])*4
    assert len(rows) == expected
    assert len({(r['seed'],r['noise'],r['protocol'],r['requested_fraction'],r['method']) for r in rows}) == expected
    groups = defaultdict(list)
    for r in rows:
        groups[(r['noise'],r['protocol'],r['requested_fraction'],r['method'])].append(r)
    summaries = []
    for (noise,protocol,fraction,method), subset in sorted(groups.items()):
        assert len(subset) == len(config['seeds'])
        record = dict(noise=noise,protocol=protocol,requested_fraction=fraction,method=method,trials=len(subset))
        for key in ['feature_speedup','dynamic_pipeline_speedup','scipy_pipeline_speedup',
                    'absolute_objective_gap','relative_objective_gap','full_recompute_agreement','mapping_churn','validation_time']:
            record[key] = distribution([r[key] for r in subset if r[key] is not None])
        record['nc'] = distribution([r['quality']['nc'] for r in subset])
        record['s3'] = distribution([r['quality']['s3'] for r in subset])
        for key in ['clone_time','feature_time','cost_time','solver_time','pipeline_time']:
            if key in subset[0]['timings']:
                record[key] = distribution([r['timings'][key] for r in subset])
        if method=='selective_dynamic':
            for key in ['total_support','first_layer_support','changed_histograms','second_layer_support','changed_features']:
                record[key+'_fraction'] = distribution([sum(s[key] for s in r['timings']['maintenance'])/(2*config['nodes']) for r in subset])
            for key in ['support_time','first_layer_time','second_layer_time','equality_time']:
                record[key] = distribution([sum(s[key] for s in r['timings']['maintenance']) for r in subset])
            record['search_fraction'] = distribution([r['timings']['search_stats']['visited_rows']/config['nodes'] for r in subset])
        summaries.append(record)
    certified = [r for r in rows if r['method'] in ['selective_dynamic','full_feature_dynamic']]
    assert all(r['optimality_certificate']['certificate_passed'] for r in certified)
    initialization = json.loads(Path('results/raw/e07_initialization.json').read_text())
    result = dict(trials=expected//4,observations=expected,certified_results=len(certified),
                  max_absolute_objective_gap=max(r['absolute_objective_gap'] for r in certified),
                  max_dual_violation=max(r['optimality_certificate']['dual_feasibility_violation'] for r in certified),
                  initialization={k:distribution([r[k] for r in initialization]) for k in
                      ['cache_time','cache_bytes','dense_cost_bytes','initial_cost_time','initial_solver_time']}, groups=summaries)
    Path('results/aggregate/e07_selective_descriptors.json').write_text(json.dumps(result,indent=2))
    selected = [r for r in summaries if r['method']=='selective_dynamic']
    fig, axes = plt.subplots(1,3,figsize=(14,4))
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            group = [r for r in selected if r['noise']==noise and r['protocol']==protocol]
            x = [r['requested_fraction']*100 for r in group]
            for ax,key in zip(axes,['feature_speedup','dynamic_pipeline_speedup','scipy_pipeline_speedup']):
                ax.plot(x,[r[key]['median'] for r in group],marker='o',label=f'{noise:.0%}, {protocol}')
                ax.fill_between(x,[r[key]['q25'] for r in group],[r[key]['q75'] for r in group],alpha=.12)
                ax.axhline(1,color='gray',linestyle='--'); ax.set_xscale('log'); ax.set_yscale('log')
                ax.set_xlabel('Requested combined-edge update (%)')
    for ax,label in zip(axes,['Full / selective feature time','Full-feature / selective dynamic pipeline','SciPy full / selective dynamic pipeline']):
        ax.set_ylabel(label)
    axes[0].legend(fontsize=7)
    fig.suptitle('E07: exact selective features; median and IQR across five fresh seeds')
    fig.tight_layout(); fig.savefig('results/figures/e07_selective_descriptors.png',dpi=180)
    table = []
    for r in selected:
        table.append(f"| {r['noise']:.0%} | {r['protocol']} | {r['requested_fraction']:.2%} | {r['total_support_fraction']['mean']:.1%} | {r['feature_speedup']['median']:.2f}× | {r['dynamic_pipeline_speedup']['median']:.2f}× | {r['scipy_pipeline_speedup']['median']:.2f}× | {r['pipeline_time']['median']*1000:.1f} |")
    quality_table = []
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            group = {r['method']:r for r in summaries if r['noise']==noise and r['protocol']==protocol and r['requested_fraction']==.001}
            quality_table.append(f"| {noise:.0%} | {protocol} | {group['keep_old']['nc']['mean']:.2%} | {group['selective_dynamic']['nc']['mean']:.2%} | {group['keep_old']['relative_objective_gap']['mean']:.2%} |")
    text = f'''# E07 findings: exact selective descriptor maintenance

Completed {expected//4} reset trials and {expected} method observations on fresh seeds 35–39, 1K BA attachment 3, shared-latent/independent protocols and 1%/5% observation noise. The protocol was written before execution. All feature arrays, actual dirty sets and refreshed cost matrices matched full recomputation exactly. Both dynamic pipelines returned identical permutations in every paired trial. All {len(certified)} dynamic results passed global primal-dual certificates and matched SciPy objectives; maximum absolute objective discrepancy was {result['max_absolute_objective_gap']:.3g}.

The new component caches degrees, raw histograms and final features. Endpoint and neighbor dependencies determine first-layer support; only actually changed histograms propagate to the next layer. Complete statistics are recomputed for supported rows to preserve numerical equality. Historical descriptor, normalization and assignment implementations remain unchanged. This demonstrates exact graph-specific maintenance, not a novel assignment algorithm or verified literature novelty.

| Initial noise | Protocol | Requested update | Feature support, mean | Feature speedup, median | Full-feature dynamic / selective pipeline, median | SciPy full / selective pipeline, median | Selective pipeline ms, median |
|---|---|---|---|---|---|---|---|
'''+'\n'.join(table)+f'''

Ratios above one favor selective maintenance. The feature ratio includes support discovery, layer maintenance and dirty detection; pipeline totals also count descriptor-cache and assignment-state clones, cost refresh and solver work. The additional descriptor caches occupy {initialization[0]['cache_bytes']:,} bytes for two graphs; the dense cost cache alone occupies {initialization[0]['dense_cost_bytes']:,} bytes. Median extra cache initialization was {result['initialization']['cache_time']['median']*1000:.1f} ms. These are array bytes, not peak RSS or all temporary storage.

The smallest requested fraction gives one edit per graph (about 0.033% realized). Both dynamic timings were measured on identical fresh conditions, with their order alternating; full SciPy ran first. Five-seed distributions describe this run, not general speed guarantees. Raw paired rows and aggregate IQR/ranges are saved. Updated-graphs-to-assignment timing excludes graph generation, applying edits and validation. Global certificate scans are validation-only; no operational certificate cost or stream performance claim is made. Cost-rescore counts are unique covered cells; the inherited row/column refresh can compute intersections twice.

At requested 0.1%, quality controls remain essential:

| Initial noise | Protocol | Keep-old NC | Exact selective repair NC | Keep-old relative objective gap |
|---|---|---|---|---|
'''+'\n'.join(quality_table)+'''

Exact feature maintenance introduces no additional descriptor or assignment approximation. It also cannot fix the underlying objective's disagreement with hidden correspondence. Keep-old retains its role as a control. Equal-cost SciPy permutations can differ from the two identical dynamic results.

Paper progress: this adds an implemented, validated graph-maintenance component beyond assignment reuse, with measured efficiency and crossover evidence. It does not establish literature novelty, compact assignment search, large-scale memory efficiency, temporal robustness or parallel CPU scaling. Interpret the timing table before choosing the next stage; retain failures and quality controls.

The next missing control is selective features and selective cost refresh followed by compiled SciPy assignment. E07's paired dynamic comparison isolates feature maintenance, but does not show that warm assignment reuse is necessary to obtain its gains. Test that control on fresh seeds 40–44 against selective dynamic repair, full compiled recomputation and keep-old before designing fallback thresholds or moving to streams. A future compiled fallback must account for how reusable dual state is restored; SciPy does not supply this reference's dual potentials.
'''
    Path('docs/e07_findings.md').write_text(text)
    print(json.dumps({k:v for k,v in result.items() if k!='groups'},indent=2))


if __name__=='__main__':
    summarize()
