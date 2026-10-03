import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
from experiments.summarize_dynamic_assignment import distribution


def summarize():
    config=json.loads(Path('configs/e08_compiled_control.json').read_text())
    rows=[json.loads(x) for x in Path('results/raw/e08_compiled_control.jsonl').read_text().splitlines()]
    expected=len(config['seeds'])*len(config['noise_levels'])*len(config['protocols'])*len(config['update_fractions'])*4
    assert len(rows)==expected
    assert len({(r['noise'],r['seed'],r['protocol'],r['requested_fraction'],r['method']) for r in rows})==expected
    groups=defaultdict(list)
    for r in rows:
        groups[(r['noise'],r['protocol'],r['requested_fraction'],r['method'])].append(r)
    summaries=[]
    for (noise,protocol,fraction,method),subset in sorted(groups.items()):
        assert len(subset)==len(config['seeds'])
        summary=dict(noise=noise,protocol=protocol,requested_fraction=fraction,method=method,trials=len(subset))
        for key in ['compiled_vs_dynamic_speedup','full_vs_selective_compiled_speedup','full_vs_selective_dynamic_speedup',
                    'absolute_objective_gap','relative_objective_gap','full_recompute_agreement','mapping_churn']:
            summary[key]=distribution([r[key] for r in subset if r[key] is not None])
        for key in ['nc','s3']:
            summary[key]=distribution([r['quality'][key] for r in subset])
        for key in ['clone_time','feature_time','cost_time','solver_time','pipeline_time']:
            if key in subset[0]['timings']:
                summary[key]=distribution([r['timings'][key] for r in subset])
        summaries.append(summary)
    warm=[r for r in rows if r['method']=='selective_dynamic']
    compiled=[r for r in rows if r['method']=='selective_scipy']
    assert all(r['optimality_certificate']['certificate_passed'] for r in warm)
    assert all(r['full_recompute_agreement']==1 for r in compiled)
    initial=json.loads(Path('results/raw/e08_initialization.json').read_text())
    result=dict(trials=expected//4,observations=expected,certified_warm_results=len(warm),
        max_absolute_objective_difference=max(abs(r['objective']-r['full_objective']) for r in warm+compiled),
        initialization={k:distribution([r[k] for r in initial]) for k in
            ['cache_time','cache_bytes','dense_cost_bytes','initial_solver_time','initial_scipy_time']},groups=summaries)
    Path('results/aggregate/e08_compiled_control.json').write_text(json.dumps(result,indent=2))
    selected=[s for s in summaries if s['method']=='selective_scipy']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            group=[s for s in selected if s['noise']==noise and s['protocol']==protocol]
            x=[s['requested_fraction']*100 for s in group]
            for ax,key in zip(axes,['compiled_vs_dynamic_speedup','full_vs_selective_compiled_speedup']):
                ax.plot(x,[s[key]['median'] for s in group],marker='o',label=f'{noise:.0%}, {protocol}')
                ax.fill_between(x,[s[key]['q25'] for s in group],[s[key]['q75'] for s in group],alpha=.12)
                ax.axhline(1,color='gray',linestyle='--');ax.set_xscale('log');ax.set_yscale('log')
                ax.set_xlabel('Requested combined-edge update (%)')
    axes[0].set_ylabel('Selective dynamic / selective compiled time')
    axes[1].set_ylabel('Full compiled / selective compiled time')
    axes[0].legend(fontsize=7)
    fig.suptitle('E08: median and IQR across five fresh seeds; ratios >1 favor compiled selective')
    fig.tight_layout();fig.savefig('results/figures/e08_compiled_control.png',dpi=180)
    table=[]
    for s in selected:
        table.append(f"| {s['noise']:.0%} | {s['protocol']} | {s['requested_fraction']:.2%} | {s['compiled_vs_dynamic_speedup']['median']:.2f}× | {s['full_vs_selective_compiled_speedup']['median']:.2f}× | {s['pipeline_time']['median']*1000:.1f} |")
    quality=[]
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            group={s['method']:s for s in summaries if s['noise']==noise and s['protocol']==protocol and s['requested_fraction']==.001}
            quality.append(f"| {noise:.0%} | {protocol} | {group['keep_old']['nc']['mean']:.2%} | {group['selective_scipy']['nc']['mean']:.2%} | {group['selective_dynamic']['nc']['mean']:.2%} |")
    findings=f'''# E08 findings: compiled assignment control

Completed {expected//4} reset trials and {expected} method observations on fresh seeds 40–44 under frozen E07 conditions. Selective compiled features, dirty sets and costs equal the full oracle exactly; its mapping agrees with full SciPy in every trial. All {len(warm)} warm results pass dual certificates and match the optimal objective. Maximum absolute objective difference across warm/compiled selective results is {result['max_absolute_objective_difference']:.3g}. The protocol was written before execution; historical kernels and results are preserved.

| Initial noise | Protocol | Requested update | Dynamic / compiled selective pipeline, median | Full / compiled selective pipeline, median | Compiled selective ms, median |
|---|---|---|---|---|---|
'''+'\n'.join(table)+f'''

Ratios above one favor compiled selective maintenance. These compare real implementations: a Python/NumPy warm assignment kernel versus compiled SciPy. They do not establish a theoretical superiority of cold assignment. Compiled selective needs descriptor caches and dense costs, but no warm dual state; both selective pipelines count their required clones, support discovery, feature/cost maintenance and solves. The full pipeline runs first and selective order alternates. Five-seed IQR/ranges and raw paired rows are saved. Timing excludes graph generation, edge application and validation; reset trials do not establish production streaming latency.

For two 1K graphs, extra descriptor arrays occupy {initial[0]['cache_bytes']:,} bytes; a dense cost matrix occupies {initial[0]['dense_cost_bytes']:,} bytes. Median cache setup is {result['initialization']['cache_time']['median']*1000:.1f} ms. Median custom warm initialization is {result['initialization']['initial_solver_time']['median']*1000:.1f} ms versus {result['initialization']['initial_scipy_time']['median']*1000:.1f} ms for SciPy on the initial matrix. Compiled selective does not require the custom setup. Array bytes omit graph storage, solver workspace and temporaries; no peak-RSS claim is made.

At requested 0.1%, mean quality controls are:

| Initial noise | Protocol | Keep-old NC | Compiled selective NC | Warm selective NC |
|---|---|---|---|---|
'''+'\n'.join(quality)+'''

Exact descriptor/objective maintenance still does not guarantee better hidden correspondence than keep-old. Warm permutations may differ on equal-cost ties; compiled selective returns the full compiled permutation. The smallest budget is one edit per graph, about 0.033% realized rather than requested 0.01%.

Paper progress: the experiment closes an important attribution gap. Report graph-maintenance gains separately from warm-solver reuse, retain every crossover/regression and avoid a solver-novelty claim. The remaining contribution needs novelty positioning, sustained exact maintenance, broader topology, memory/scaling and eventual CPU decomposition evidence.

Decision: at requested 0.1%, selective compiled beats full recomputation by 1.45–1.86× in every condition; warm selective is faster than compiled selective in three of four conditions. At requested 1%, compiled selective remains 1.11–1.19× faster than full recomputation and is 2.33–6.52× faster than warm selective. At 5%, full recomputation wins in all condition medians. These establish measured regime differences, not a validated adaptive selector.

Next run a short persistent-state stream pilot on fresh seeds 45–49: ten successive batches per stream, requested 0.1% and 1%, both protocols/noise levels. Compare the two selective methods, full compiled recomputation and keep-initial mapping. Count method-specific initialization and cumulative update cost; remove reset-only per-batch clones while retaining real cache/cost work. Validate every step against the full oracle. Record realized budgets, accumulated changes, NC/S3, churn and latency by step. Keep the solver choice fixed per stream; defer adaptive fallback until its dual-state transition cost is addressed. Ten-step evidence is a pilot, not long-stream robustness or an amortization guarantee.
'''
    Path('docs/e08_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k!='groups'},indent=2))


if __name__=='__main__':
    summarize()
