"""Stream-level E09 evidence; correlated steps are never independent samples."""
import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
from experiments.summarize_dynamic_assignment import distribution


def summarize():
    config=json.loads(Path('configs/e09_streams.json').read_text())
    rows=[json.loads(x) for x in Path('results/raw/e09_streams.jsonl').read_text().splitlines()]
    expected=len(config['seeds'])*len(config['noise_levels'])*len(config['protocols'])*len(config['update_fractions'])*config['steps']*4
    assert len(rows)==expected
    assert len({(r['noise'],r['seed'],r['protocol'],r['requested_fraction'],r['step'],r['method']) for r in rows})==expected
    streams=defaultdict(list)
    for r in rows:streams[(r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method'])].append(r)
    totals=[]
    for (noise,protocol,fraction,seed,method),steps in sorted(streams.items()):
        steps=sorted(steps,key=lambda r:r['step'])
        assert [r['step'] for r in steps]==list(range(1,config['steps']+1))
        final=steps[-1]
        assert abs(sum(r['timings']['pipeline_time'] for r in steps)-final['cumulative_update_time'])<1e-9
        total=dict(noise=noise,protocol=protocol,requested_fraction=fraction,seed=seed,method=method,
            initialization_time=final['initialization_time'],update_time=final['cumulative_update_time'],
            initialization_plus_updates=final['initialization_plus_updates'],final_nc=final['quality']['nc'],
            final_s3=final['quality']['s3'],final_initial_churn=final['initial_mapping_churn'],
            final_objective_gap=final['relative_objective_gap'],max_absolute_objective_difference=max(abs(r['objective']-r['full_objective']) for r in steps))
        for key in ['feature_time','cost_time','solver_time']:
            total[key]=sum(r['timings'][key] for r in steps)
        totals.append(total)
    lookup={(r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method']):r for r in totals}
    paired=[]
    for r in totals:
        if r['method']=='keep_initial':continue
        full=lookup[(r['noise'],r['protocol'],r['requested_fraction'],r['seed'],'full_scipy')]
        paired.append({**r,'feature_speedup':full['feature_time']/r['feature_time'],
            'cost_speedup':full['cost_time']/r['cost_time'],'solver_speedup':full['solver_time']/r['solver_time'],
            'update_speedup':full['update_time']/r['update_time'],
            'initialization_inclusive_speedup':full['initialization_plus_updates']/r['initialization_plus_updates']})
    grouped=defaultdict(list)
    for r in paired:grouped[(r['noise'],r['protocol'],r['requested_fraction'],r['method'])].append(r)
    summaries=[]
    for (noise,protocol,fraction,method),subset in sorted(grouped.items()):
        assert len(subset)==len(config['seeds'])
        record=dict(noise=noise,protocol=protocol,requested_fraction=fraction,method=method,streams=len(subset))
        for key in ['initialization_time','update_time','initialization_plus_updates','feature_time','cost_time','solver_time',
                    'feature_speedup','cost_speedup','solver_speedup','update_speedup','initialization_inclusive_speedup',
                    'final_nc','final_s3','final_initial_churn']:
            record[key]=distribution([r[key] for r in subset])
        summaries.append(record)
    stepgroups=defaultdict(list)
    for r in rows:stepgroups[(r['noise'],r['protocol'],r['requested_fraction'],r['method'],r['step'])].append(r)
    per_step=[]
    for (noise,protocol,fraction,method,step),subset in sorted(stepgroups.items()):
        per_step.append(dict(noise=noise,protocol=protocol,requested_fraction=fraction,method=method,step=step,
            pipeline_time=distribution([r['timings']['pipeline_time'] for r in subset]),
            initialization_plus_updates=distribution([r['initialization_plus_updates'] for r in subset]),
            nc=distribution([r['quality']['nc'] for r in subset]),s3=distribution([r['quality']['s3'] for r in subset])))
    warm=[r for r in rows if r['method']=='selective_dynamic']
    compiled=[r for r in rows if r['method']=='selective_scipy']
    assert all(r['optimality_certificate']['certificate_passed'] for r in warm)
    assert all(r['full_recompute_agreement']==1 for r in compiled)
    result=dict(streams=expected//(config['steps']*4),updates=expected//4,observations=expected,
        certified_warm_updates=len(warm),max_absolute_objective_difference=max(abs(r['objective']-r['full_objective']) for r in warm+compiled),
        stream_totals=totals,paired_stream_metrics=paired,groups=summaries,per_step=per_step)
    Path('results/aggregate/e09_streams.json').write_text(json.dumps(result,indent=2))
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    labels=[]
    for index,r in enumerate(s for s in summaries if s['method']!='full_scipy'):
        labels.append(f"{r['noise']:.0%}/{r['protocol']}/{r['requested_fraction']:.1%}/{r['method'].replace('selective_','')}")
        for ax,key in zip(axes,['feature_speedup','initialization_inclusive_speedup']):
            v=r[key];ax.errorbar(index,v['median'],yerr=[[v['median']-v['q25']],[v['q75']-v['median']]],fmt='o')
    for ax in axes:
        ax.axhline(1,color='gray',linestyle='--');ax.set_yscale('log');ax.set_xticks(range(len(labels)),labels,rotation=90,fontsize=7)
    axes[0].set_ylabel('Full / selective feature time')
    axes[1].set_ylabel('Full / selective total time\n(setup + ten updates)')
    fig.suptitle('E09: feature-stage and setup-inclusive speedups\nMedian/IQR across five streams per condition',fontsize=11)
    fig.tight_layout();fig.savefig('results/figures/e09_streams.png',dpi=180)
    table=[]
    for r in summaries:
        if r['method']=='full_scipy':continue
        table.append(f"| {r['noise']:.0%} | {r['protocol']} | {r['requested_fraction']:.1%} | {r['method'].replace('selective_','')} | {r['feature_speedup']['median']:.2f}× | {r['cost_speedup']['median']:.2f}× | {r['update_speedup']['median']:.2f}× | {r['initialization_inclusive_speedup']['median']:.2f}× |")
    quality=[]
    for noise in config['noise_levels']:
        for protocol in config['protocols']:
            for fraction in config['update_fractions']:
                group=[r for r in totals if r['noise']==noise and r['protocol']==protocol and r['requested_fraction']==fraction]
                values={m:distribution([r['final_nc'] for r in group if r['method']==m])['mean'] for m in ['keep_initial','full_scipy','selective_dynamic']}
                quality.append(f"| {noise:.0%} | {protocol} | {fraction:.1%} | {values['keep_initial']:.2%} | {values['full_scipy']:.2%} | {values['selective_dynamic']:.2%} |")
    findings=f'''# E09 findings: persistent-state stream pilot

Completed {result['streams']} ten-batch streams, {result['updates']} updates and {expected} method observations on fresh seeds 45–49. All selective features, actual dirty sets and costs match full recomputation at every step; selective SciPy returns the full SciPy mapping. All {len(warm)} warm updates pass global primal-dual certificates and match the optimal objective. Maximum absolute objective difference is {result['max_absolute_objective_difference']:.3g}. Shared-latent observation masks are checked against the initial mask at every step. The protocol was saved before execution, and historical kernels/results remain frozen.

Each method initializes its own required state, then maintains it across ten successive updates. No reset-specific state/cache clones occur per batch. Warm repair still copies refreshed costs internally; selective cost refresh still copies dense costs. Timings start from already updated graphs and exclude generation, batch application, validation and quality evaluation. Setup-inclusive totals include real method-specific feature/cost/solver setup. Keep-initial pays initial full alignment and does no update computation.

Five stream/seed bundles per condition provide independent observations; correlated batches are summed within each stream before ratios and distributions are reported. Noise/protocol/budget conditions are paired. Full SciPy runs first and selective order alternates. Ratios above one favor selective maintenance. Stage and total results are deliberately separate: a faster component is positive engineering evidence even when another component or initialization prevents a whole-pipeline gain.

| Initial noise | Protocol | Requested batch fraction | Selective solver | Feature-stage speedup | Cost-stage speedup | Update-only pipeline speedup | Setup + ten updates speedup |
|---|---|---|---|---|---|---|---|
'''+'\n'.join(table)+'''

These are medians of paired stream-total ratios, not ratios of pooled batch means. Aggregate JSON retains IQR/ranges, method-specific initialization, cumulative stage totals and per-step latency/quality. Cost-stage ratios describe the existing dense refresh implementation, including copies and repeated row/column intersections; they are not subquadratic indexing evidence. Feature-stage ratios include support discovery and dirty detection on selective pipelines. All cache arrays/scale persist across steps; normalization remains frozen initially.

Final mean NC after ten steps:

| Initial noise | Protocol | Requested batch fraction | Keep-initial NC | Full / compiled selective NC | Warm selective NC |
|---|---|---|---|---|---|
'''+'\n'.join(quality)+'''

Exact maintenance adds no feature or assignment-objective approximation, but descriptor minimization still need not improve hidden correspondence. Objective correctness, stage efficiency and identity quality are distinct outcomes. Warm ties may select an equally optimal permutation with different NC.

Paper progress: sustained exact maintenance and component-level improvements now have short-stream evidence. Component improvements count positively even if total setup-inclusive latency loses. Literature novelty, long-stream robustness, other topologies, memory/scaling and parallel CPU decomposition remain unproven. Ten steps are a pilot, not an amortization or break-even guarantee. No adaptive fallback is evaluated; switching to compiled assignment does not automatically restore reusable warm duals.

Decision: at requested 0.1%, feature-stage medians improve 9.05–9.46× across selective methods/conditions; compiled selective achieves 1.42–1.85× setup-inclusive speedup. Warm setup-inclusive medians are 0.46–0.77×, despite useful feature gains and some update-only wins. At 1%, feature-stage gains persist at 1.71–1.73× while cost-stage ratios are only 0.52–0.54×; compiled setup-inclusive totals still improve 1.11–1.19×. Warm totals remain slower. This supports positive component progress and a measured compiled pipeline benefit without a universal warm-solver claim.

Independent-edit streams accumulate observation differences: final NC at 1% batches is 20.12% under 1% initial noise and 17.28% under 5% initial noise. Full recomputation has the same decline as exact selective maintenance, so this is not a cache error. Keep-initial retains its fixed true correspondence; it need not maintain the updated descriptor optimum. Shared-latent streams preserve the observation mask and retain much higher NC. Objective/protocol fitness must remain explicit in any paper claim.

Next address the isolated cost-stage regression using [exact persistent cost maintenance](cost_maintenance_design.md): cached normalized features, disjoint changed-row/changed-column blocks and safe in-place dense updates. Compare with the frozen historical refresh on fresh seeds 50–54, count all work/setup/storage, and require full cost and mapping equality. Then apply [topology robustness](topology_robustness_design.md). Do not hide a stage gain if total latency barely changes, and do not claim that cost optimization improves correspondence quality.
'''
    Path('docs/e09_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k not in ['stream_totals','paired_stream_metrics','groups','per_step']},indent=2))


if __name__=='__main__':summarize()
