"""Summarize E06 without treating paired conditions as independent seeds."""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt


def distribution(values):
    a = np.asarray(values, dtype=float)
    return dict(mean=float(a.mean()), median=float(np.median(a)),
                q25=float(np.quantile(a, .25)), q75=float(np.quantile(a, .75)),
                minimum=float(a.min()), maximum=float(a.max()))


def summarize():
    rows = [json.loads(line) for line in Path('results/raw/e06_dynamic_assignment.jsonl').read_text().splitlines()]
    config = json.loads(Path('configs/e06_dynamic_assignment.json').read_text())
    expected = len(config['seeds'])*len(config['noise_levels'])*len(config['update_fractions'])*len(config['protocols'])*4
    assert len(rows) == expected
    groups = defaultdict(list)
    for row in rows:
        groups[(row['noise'], row['protocol'], row['requested_fraction'], row['method'])].append(row)
    metrics = ['same_kernel_solver_speedup', 'scipy_pipeline_speedup', 'dynamic_pipeline_time',
               'full_pipeline_time', 'dynamic_solver_time', 'cold_solver_time', 'scipy_solver_time',
               'dynamic_feature_time', 'dynamic_cost_time', 'dynamic_clone_time', 'validation_time',
               'rescored_cost_fraction', 'absolute_objective_gap', 'relative_objective_gap',
               'full_recompute_agreement', 'mapping_churn', 'nc_difference_vs_keep_old']
    summaries = []
    for (noise, protocol, fraction, method), subset in sorted(groups.items()):
        assert len(subset) == len(config['seeds'])
        record = dict(noise=noise, protocol=protocol, requested_fraction=fraction, method=method, trials=len(subset))
        for metric in metrics:
            record[metric] = distribution([r[metric] for r in subset if r[metric] is not None])
        record['nc'] = distribution([r['quality']['nc'] for r in subset])
        if method == 'dynamic':
            for key in ['initially_exposed_rows', 'visited_rows', 'augmentations', 'cost_cells_examined']:
                record[key] = distribution([r['search_stats'][key] for r in subset])
        summaries.append(record)
    certified = [r for r in rows if r['method'] in ['dynamic', 'cold_hungarian']]
    assert all(r['optimality_certificate']['certificate_passed'] for r in certified)
    initial = json.loads(Path('results/raw/e06_initialization.json').read_text())
    result = {'trials': expected//4, 'observations': expected, 'certified_observations': len(certified),
              'max_absolute_objective_gap': max(r['absolute_objective_gap'] for r in certified),
              'max_dual_violation': max(r['optimality_certificate']['dual_feasibility_violation'] for r in certified),
              'initialization': {k: distribution([r[k] for r in initial]) for k in
                  ['initial_cost_time', 'initial_solver_time', 'initial_mapping_agreement_with_scipy']},
              'groups': summaries}
    Path('results/aggregate/e06_dynamic_assignment.json').write_text(json.dumps(result, indent=2))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            selected = [s for s in summaries if s['method']=='dynamic' and s['noise']==noise and s['protocol']==protocol]
            x = [s['requested_fraction']*100 for s in selected]
            for ax, metric in zip(axes, ['same_kernel_solver_speedup', 'scipy_pipeline_speedup']):
                y = [s[metric]['median'] for s in selected]
                ax.plot(x, y, marker='o', label=f'{noise:.0%} noise, {protocol}')
                ax.fill_between(x, [s[metric]['q25'] for s in selected], [s[metric]['q75'] for s in selected], alpha=.12)
                ax.set_xscale('log'); ax.set_yscale('log'); ax.axhline(1, color='gray', linestyle='--')
                ax.set_xlabel('Requested combined-edge update (%)')
    axes[0].set_ylabel('Cold / dynamic custom solver time')
    axes[1].set_ylabel('SciPy full / dynamic pipeline time')
    axes[0].legend(fontsize=7)
    fig.suptitle('E06: median and IQR across five seeds; reset trials, 1K BA graphs')
    fig.tight_layout()
    Path('results/figures').mkdir(exist_ok=True)
    fig.savefig('results/figures/e06_dynamic_assignment.png', dpi=180)
    table = []
    for s in summaries:
        if s['method']=='dynamic':
            table.append(f"| {s['noise']:.0%} | {s['protocol']} | {s['requested_fraction']:.2%} | {s['initially_exposed_rows']['mean']/10:.1f}% | {s['visited_rows']['mean']/10:.1f}% | {s['same_kernel_solver_speedup']['median']:.2f}× | {s['scipy_pipeline_speedup']['median']:.2f}× | {s['dynamic_pipeline_time']['median']*1000:.1f} |")
    quality_table = []
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            selected = {s['method']: s for s in summaries if s['noise']==noise and s['protocol']==protocol and s['requested_fraction']==.001}
            quality_table.append(f"| {noise:.0%} | {protocol} | {selected['keep_old']['nc']['mean']:.2%} | {selected['dynamic']['nc']['mean']:.2%} | {selected['scipy_full']['nc']['mean']:.2%} | {selected['keep_old']['relative_objective_gap']['mean']:.2%} |")
    findings = f'''# E06 findings: exact assignment reuse

Completed {expected//4} reset trials and {expected} method observations on fresh seeds 30–34, 1K BA graphs, two update protocols and two initial noise levels. Configuration, raw rows, initialization, source hashes and the aggregate are saved. All {len(certified)} warm/cold reference results passed primal-dual certificates and agreed with SciPy's objective; maximum absolute objective discrepancy was {result['max_absolute_objective_gap']:.3g}. Initial reference solves also matched SciPy objectives. Equal-cost ties can give different permutations; objective agreement is the correctness criterion.

The original reference follows the primal-dual repair idea in [CMU-RI-TR-07-27](https://www.cs.cmu.edu/~gertrude/dyn_assign_techreport.pdf). See [the protocol](e06_protocol.md) for implementation differences and provenance. This establishes an existing exact baseline, not algorithmic novelty for DeltaAlign.

| Initial noise | Protocol | Requested update | Exposed rows, mean | Search rows visited, mean | Same-kernel solver speedup, median | SciPy full / dynamic pipeline, median | Dynamic pipeline ms, median |
|---|---|---|---|---|---|---|---|
''' + '\n'.join(table) + '''

Ratios above one favor dynamic repair. Same-kernel speedup compares two implementations using the same Python/NumPy Hungarian kernel. The full pipeline comparison uses compiled SciPy and includes full feature recomputation, dirty detection, dense cache refresh, state cloning and repair; it excludes graph generation, applying edge batches and correctness certificates. It is a graph-to-assignment measurement, not complete streaming latency. Timing order is fixed, and five-seed distributions describe this machine/run rather than universal speedups. IQR and ranges are in the aggregate. No speedup against E05's restricted methods is asserted because E06 initializes its mapping with the custom optimum, which can differ on ties.

At the smallest requested fraction, each graph receives one edit: the realized combined fraction is about 0.033%, not 0.01%. At requested 0.1%, median pipeline ratios range from 0.63× to 1.12×; only the 5%-noise shared-latent condition is faster. Mean search coverage is 77.8–97.6%. At requested 1% and 5%, all condition medians favor compiled full recomputation. Full descriptor recomputation still takes roughly 74 ms at requested 0.1%; selective dense cost refresh takes about 5 ms. Work reduction in the solver therefore does not remove the graph-feature bottleneck.

Dirty cost rows/columns and searched assignment rows are different quantities. Repair can visit rows outside the initially exposed set through competing assignments. Keep-old is still a quality control: minimizing the descriptor objective does not guarantee improved hidden correspondence. The aggregate retains NC, churn and mapping agreement for every method. At requested 0.1%, five-seed mean NC and keep-old objective gaps are:

| Initial noise | Protocol | Keep-old NC | Dynamic NC | SciPy full NC | Keep-old relative objective gap |
|---|---|---|---|---|---|
''' + '\n'.join(quality_table) + '''

Initial custom and SciPy mappings agreed on all ten graph pairs in this run. Updated exact optima differed on a few equal-cost ties; the tiny NC differences between exact solvers do not indicate an objective error. The quality comparison confirms E05's concern: exact descriptor minimization can lose true matches relative to keep-old, even while eliminating its objective gap.

The next mechanism must preserve assignment competition and dual feasibility, rather than pre-expanding every candidate owner or relying on row-best margins. See [assignment-aware localization design](assignment_aware_localization.md). First implement exact selective descriptor maintenance against the full descriptor oracle; retain exact cost refresh and dynamic assignment so errors can be isolated. Larger graphs, repeated streams, memory profiling and parallel components remain pending.

Paper progress: closer through a verified, correctness-checked baseline and measured work boundaries. A new compact, efficient graph-aware repair method is still unproven. Assignment reuse by itself is established prior work, and timing gains within a custom solver do not establish an advantage over compiled FullAlign.
'''
    Path('docs/e06_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k!='groups'}, indent=2))


if __name__ == '__main__':
    summarize()
