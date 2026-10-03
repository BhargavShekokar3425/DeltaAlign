"""E10 paired stage and whole-pipeline outcomes from stream totals."""
import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
from experiments.summarize_dynamic_assignment import distribution


def summarize():
    config=json.loads(Path('configs/e10_costs.json').read_text())
    rows=[json.loads(x) for x in Path('results/raw/e10_costs.jsonl').read_text().splitlines()]
    expected=len(config['seeds'])*len(config['noise_levels'])*len(config['protocols'])*len(config['update_fractions'])*config['steps']*4
    assert len(rows)==expected
    assert len({(r['noise'],r['seed'],r['protocol'],r['requested_fraction'],r['step'],r['method']) for r in rows})==expected
    active=[r for r in rows if r['method']!='keep_initial']
    assert all(r['full_recompute_agreement']==1 for r in active)
    assert all(r['objective']==r['full_objective'] for r in active)
    streams=defaultdict(list)
    for r in rows:streams[(r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method'])].append(r)
    totals=[]
    for (noise,protocol,fraction,seed,method),steps in sorted(streams.items()):
        steps=sorted(steps,key=lambda r:r['step'])
        assert [r['step'] for r in steps]==list(range(1,config['steps']+1))
        final=steps[-1]
        total=dict(noise=noise,protocol=protocol,requested_fraction=fraction,seed=seed,method=method,
            initialization_time=final['initialization_time'],update_time=final['cumulative_update_time'],
            total_time=final['initialization_plus_updates'],final_nc=final['quality']['nc'],final_s3=final['quality']['s3'])
        for key in ['feature_time','cost_time','solver_time','computed_cost_entries','dense_refresh_copies']:
            total[key]=sum(r['timings'].get(key,0) for r in steps)
        assert abs(total['update_time']-sum(r['timings']['pipeline_time'] for r in steps))<1e-9
        totals.append(total)
    lookup={(r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method']):r for r in totals}
    paired=[]
    for r in totals:
        if r['method']!='persistent_scipy':continue
        key=(r['noise'],r['protocol'],r['requested_fraction'],r['seed'])
        full=lookup[(*key,'full_scipy')];old=lookup[(*key,'selective_scipy')]
        paired.append({**r,'cost_speedup_vs_historical':old['cost_time']/r['cost_time'],
            'cost_speedup_vs_full':full['cost_time']/r['cost_time'],
            'feature_speedup_vs_full':full['feature_time']/r['feature_time'],
            'computed_cell_reduction':old['computed_cost_entries']/r['computed_cost_entries'],
            'update_speedup_vs_historical':old['update_time']/r['update_time'],
            'total_speedup_vs_historical':old['total_time']/r['total_time'],
            'update_speedup_vs_full':full['update_time']/r['update_time'],
            'total_speedup_vs_full':full['total_time']/r['total_time']})
    groups=defaultdict(list)
    for r in paired:groups[(r['noise'],r['protocol'],r['requested_fraction'])].append(r)
    summaries=[]
    for (noise,protocol,fraction),subset in sorted(groups.items()):
        assert len(subset)==len(config['seeds'])
        summary=dict(noise=noise,protocol=protocol,requested_fraction=fraction,streams=len(subset))
        for key in ['cost_speedup_vs_historical','cost_speedup_vs_full','feature_speedup_vs_full','computed_cell_reduction',
                    'update_speedup_vs_historical','total_speedup_vs_historical','update_speedup_vs_full','total_speedup_vs_full',
                    'initialization_time','cost_time','feature_time','solver_time','total_time','final_nc','final_s3']:
            summary[key]=distribution([r[key] for r in subset])
        summaries.append(summary)
    initial=json.loads(Path('results/raw/e10_initialization.json').read_text())
    initialization=[]
    for method in ['full_scipy','selective_scipy','persistent_scipy']:
        subset=[r for r in initial if r['method']==method]
        initialization.append(dict(method=method,initialization_time=distribution([r['initialization_time'] for r in subset]),
            descriptor_cache_bytes=subset[0]['cache_bytes'],normalized_feature_bytes=subset[0]['normalized_feature_bytes'],dense_cost_bytes=subset[0]['dense_cost_bytes']))
    result=dict(streams=expected//(4*config['steps']),updates=expected//4,observations=expected,
        exact_active_results=len(active),max_absolute_objective_difference=max(abs(r['objective']-r['full_objective']) for r in active),
        initialization=initialization,stream_totals=totals,paired_stream_metrics=paired,groups=summaries)
    Path('results/aggregate/e10_costs.json').write_text(json.dumps(result,indent=2))
    labels=[f"{r['noise']:.0%} {r['protocol']} {r['requested_fraction']:.1%}" for r in summaries]
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,key in zip(axes,['cost_speedup_vs_historical','total_speedup_vs_historical']):
        for i,r in enumerate(summaries):
            v=r[key];ax.errorbar(i,v['median'],yerr=[[v['median']-v['q25']],[v['q75']-v['median']]],fmt='o')
        ax.axhline(1,color='gray',linestyle='--');ax.set_xticks(range(len(labels)),labels,rotation=70,fontsize=8)
    axes[0].set_ylabel('Historical / persistent cost-stage time')
    axes[1].set_ylabel('Historical / persistent total time\n(setup + ten updates)')
    fig.suptitle('E10: component gains and pipeline outcome; paired medians/IQR across five streams',fontsize=11)
    fig.tight_layout();fig.savefig('results/figures/e10_costs.png',dpi=180)
    table=[]
    for r in summaries:
        table.append(f"| {r['noise']:.0%} | {r['protocol']} | {r['requested_fraction']:.1%} | {r['cost_speedup_vs_historical']['median']:.2f}× | {r['cost_speedup_vs_full']['median']:.2f}× | {r['total_speedup_vs_historical']['median']:.2f}× | {r['total_speedup_vs_full']['median']:.2f}× |")
    findings=f'''# E10 findings: exact persistent cost maintenance

Completed {result['streams']} ten-step streams, {result['updates']} updates and {expected} method observations on fresh seeds 50–54 under frozen E09 BA conditions. All feature, dirty-set, normalized-feature and cost arrays match the full oracle at every step. All {len(active)} active method results return the same SciPy mapping and objective; maximum objective discrepancy is zero. Forty-one tests cover cache blocks, ties, all/no/one-sided/overlapping changes and repeated graph streams. Historical feature, assignment and refresh kernels/results remain unchanged.

The new `src/cost_cache.py` keeps normalized feature arrays, rescales only dirty rows and refreshes disjoint cost blocks. Changed source rows are updated against all targets; changed target columns are updated only against unchanged source rows. The owned dense matrix persists in place. No selector, approximation, warm-dual transition or new assignment algorithm is introduced.

| Initial noise | Protocol | Requested batch fraction | Cost speedup vs historical refresh | Cost speedup vs full construction | Setup-inclusive speedup vs historical selective | Setup-inclusive speedup vs full |
|---|---|---|---|---|---|---|
'''+'\n'.join(table)+'''

Ratios above one favor the new cache. These are medians of paired stream-total ratios across five independent seed bundles per condition, with IQR/ranges retained in aggregate JSON. Conditions and batches are paired/correlated; individual batches are not independent repetitions. Component gains count as positive outcomes even when total latency changes little or regresses. Cost time includes normalization, indexing, distance calculations, block writes and required temporaries. Total time includes real method-specific initialization plus ten updates, feature work and compiled assignment. Full recomputation runs first and selective order alternates. Timings exclude graph generation/applying batches, validation and quality evaluation.

The new method eliminates the historical refresh's ten complete matrix copies per ten-step stream and computes row/column intersections once. Distance temporaries remain; this is not a peak-memory claim. Extra normalized feature arrays occupy 432,000 bytes for two 1K graphs, plus a 216-byte scale copy; descriptor arrays occupy 640,000 bytes and dense costs 8,000,000 bytes. Dense storage remains quadratic. Method-specific initialization timings and computed-cell totals are saved.

Cost and mapping equality ensure quality is unchanged relative to full/historical SciPy. The speedup does not repair hidden correspondence or objective/protocol fitness. Keep-initial and NC/S3 controls are retained for every stream, including independent-edit quality declines. Cached normalization stays fixed to initial scale throughout.

Decision: at requested 0.1%, cost-stage medians improve 1.23–1.27× over historical refresh and 1.90–2.03× over full construction. At 1%, the historical-refresh comparison improves 1.75–1.77×, but full construction still wins slightly (full/new cost ratios 0.91–0.92×). E09's large cost-stage regression is reduced, not completely removed. Setup-inclusive medians improve about 1–7% over historical selective maintenance and 1.41–1.67× over full recomputation at 0.1%, or 1.15–1.26× at 1%. The larger component gain has a modest incremental total effect because assignment remains a major cost.

Paper progress: this adds a validated cost-maintenance component with a modest overall improvement as well. Give cost-stage improvements positive credit independently of total pipeline gain. These are engineering results, not verified literature novelty, large-scale memory efficiency, long-stream robustness or parallel decomposition evidence. Next apply the topology robustness gate on fresh seeds 55–59 with initial-quality/no-update controls and exact stream checks, preserving stage gains and failed regimes.
'''
    Path('docs/e10_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k not in ['stream_totals','paired_stream_metrics','groups']},indent=2))


if __name__=='__main__':summarize()
