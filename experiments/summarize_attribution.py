"""E15 stream-level paired attribution; no independent-step statistics."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from experiments.summarize_scaling import distribution


def summarize():
    rows=[json.loads(x) for x in Path('results/raw/e15_attribution.jsonl').read_text().splitlines()]
    metadata=json.loads(Path('results/raw/e15_attribution.metadata.json').read_text());config=metadata['config']
    assert all(p['permitted'] for p in metadata['preflight']) and len(rows)==120
    lookup={(r['family'],r['requested_fraction'],r['seed'],r['method']):r for r in rows}
    assert len(lookup)==120
    pairs=[];conditions=[];workers=[]
    for family in config['families']:
        for fraction in config['requested_fractions']:
            selected=[]
            for seed in config['seeds']:
                group={m:lookup[family,fraction,seed,m] for m in config['methods']}
                full=group['full_scipy'];refined=group['persistent_scipy'];cf=group['conservative_features'];cc=group['conservative_costs']
                assert all(len(r['records'])==11 for r in group.values())
                assert len({r['position'] for r in group.values()})==4
                for r in group.values():
                    assert r['order']==full['order']
                    assert all(a['hashes']==b['hashes'] and a['objective']==b['objective'] for a,b in zip(r['records'],full['records']))
                def stage(r,k):return sum(v['timings'][k] for v in r['records'][1:])
                def work(r,k):return sum(sum(v[k] for v in record['timings']['maintenance']) for record in r['records'][1:])
                pair=dict(family=family,requested_fraction=fraction,seed=seed,
                    feature_control_ratio=stage(cf,'feature_time')/stage(refined,'feature_time'),
                    cost_control_ratio=stage(cc,'cost_time')/stage(refined,'cost_time'),
                    cost_with_support_ratio=(stage(cc,'cost_time')+stage(cc,'extra_support_time'))/stage(refined,'cost_time'),
                    second_support_ratio=work(cf,'second_layer_support')/work(refined,'second_layer_support'),
                    computed_entries_ratio=stage(cc,'computed_cost_entries')/stage(refined,'computed_cost_entries'),
                    feature_control_total_ratio=cf['total_time']/refined['total_time'],
                    cost_control_total_ratio=cc['total_time']/refined['total_time'],
                    refined_feature_seconds=stage(refined,'feature_time'),conservative_feature_seconds=stage(cf,'feature_time'),
                    refined_second_support=work(refined,'second_layer_support'),conservative_second_support=work(cf,'second_layer_support'))
                for method,r in group.items():
                    stages={k:stage(r,k) for k in ['feature_time','cost_time','solver_time','extra_support_time','computed_cost_entries']}
                    record=dict(family=family,requested_fraction=fraction,seed=seed,method=method,
                        total_time=r['total_time'],update_time=r['update_time'],initialization_time=r['initialization_time'],peak_rss_mib=r['peak_rss_bytes']/1024**2,
                        initial_quality=r['records'][0]['quality'],final_quality=r['records'][-1]['quality'],stages=stages,
                        rows_normalized=[sum(v['timings']['rows_normalized'][i] for v in r['records'][1:]) for i in range(2)])
                    if method!='full_scipy':record['work']={k:work(r,k) for k in ['first_layer_support','second_layer_support','changed_histograms','changed_features','total_support']}
                    workers.append(record)
                    if method!='full_scipy':
                        pair[method+'_total_speedup']=full['total_time']/r['total_time']
                        pair[method+'_update_speedup']=full['update_time']/r['update_time']
                        pair[method+'_rss_ratio']=r['peak_rss_bytes']/full['peak_rss_bytes']
                pairs.append(pair);selected.append(pair)
            keys=[k for k,v in selected[0].items() if isinstance(v,(float,int)) and k not in ['seed','requested_fraction']]
            conditions.append(dict(family=family,requested_fraction=fraction,seeds=config['seeds'],distributions={k:distribution([p[k] for p in selected]) for k in keys},feature_control_wins=sum(p['feature_control_ratio']>1 for p in selected),cost_control_wins=sum(p['cost_control_ratio']>1 for p in selected)))
    result=dict(execution_status='completed',worker_runs=120,paired_streams=30,unique_update_scenarios=300,method_updates=1200,matching_snapshots=990,conditions=conditions,pairs=pairs,workers=workers)
    Path('results/aggregate/e15_attribution.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    labels=[f"{c['family'].upper()} {c['requested_fraction']:.1%}" for c in conditions]
    for ax,key,title in zip(axes,['feature_control_ratio','cost_control_ratio'],['Conservative features / refined feature time','Conservative costs / refined cost time']):
        data=[[p[key] for p in pairs if (p['family'],p['requested_fraction'])==(c['family'],c['requested_fraction'])] for c in conditions]
        ax.boxplot(data,tick_labels=labels);ax.axhline(1,color='gray',linestyle='--');ax.set_ylabel(title);ax.tick_params(axis='x',rotation=25)
    fig.suptitle('E15: five paired seeds; ten correlated updates summed per worker');fig.tight_layout();fig.savefig('results/figures/e15_attribution.png',dpi=180)
    fig,ax=plt.subplots(figsize=(7,5))
    for method,color in [('persistent_scipy','tab:blue'),('conservative_features','tab:orange')]:
        subset=[r for r in workers if r['method']==method]
        ax.scatter([r['work']['second_layer_support'] for r in subset],[r['stages']['feature_time'] for r in subset],label=method,color=color,alpha=.7)
    ax.set_xlabel('Second-layer rows recomputed, summed across both graphs / ten steps');ax.set_ylabel('Total feature-stage seconds per stream');ax.legend();fig.tight_layout();fig.savefig('results/figures/e15_second_layer.png',dpi=180)
    table=[]
    for c in conditions:
        d=c['distributions']
        def fmt(k):
            v=d[k];return f"{v['median']:.2f} [{v['q25']:.2f}, {v['q75']:.2f}]; {v['min']:.2f}–{v['max']:.2f}"
        table.append(f"| {c['family'].upper()} | {c['requested_fraction']:.1%} | {fmt('feature_control_ratio')} | {fmt('cost_control_ratio')} | {fmt('second_support_ratio')} | {fmt('computed_entries_ratio')} | {fmt('persistent_scipy_total_speedup')} |")
    text='''# E15 findings: attribution beyond conservative locality

Completed all 120 sequential fresh workers across 30 paired streams on fresh seeds 66–70, 1K BA/ER/WS, 1% initial noise, two update budgets and ten shared-latent steps. All 990 non-full-versus-full setup/update snapshots have identical features, normalized features, scales, costs, mappings and objectives. There are 300 unique graph-update scenarios and 1,200 method-update observations. All inspected resource gates passed. Forty-six tests pass, including controls for no changes, isolates, bin crossings, degree-preserving edits and consecutive mixed updates. Historical kernels remain unchanged.

Each table cell is median [Q25, Q75]; range across five paired seed streams. Ten correlated steps are summed within each worker. Feature/cost ratios compare conservative control time to refined time; ratios above one favor refined maintenance. Work ratios compare conservative to refined row/entry counts. Total ratios compare full to refined setup plus ten updates.

| Topology | Budget | Feature control/refined | Cost control/refined | Second-layer work ratio | Cost-entry work ratio | Full/refined total |
|---|---|---|---|---|---|---|
'''+ '\n'.join(table)+'''

The aggregate retains every seed, all methods' update/setup-inclusive ratios, RSS, stage seconds, support counts, normalized-row counts, cost-entry counts and initial/final NC/EC/S3. Raw per-step records retain order and validation fingerprints. The second-layer plot shows work and time together; it does not infer timing from row counts. Extra conservative-cost support construction is recorded separately and included in pipeline time; its cost-plus-support ratio is also retained. Refined workers are not charged for unneeded conservative diagnostics.

This isolates implementation controls using the same features, frozen normalization, cache initialization and compiled solver. Conservative feature maintenance uses the same first-layer numerical operations and recomputes a safe second-layer superset; conservative cost maintenance refreshes a safe dirty superset. Neither control is an InkStream/RIPPLE++ reproduction. All workers use E13's dense-matrix lifecycle, buffer fingerprints and whole-worker peak RSS scope. Timings exclude graph generation and validation.

The config's `preregistered_not_run` status is retained as the frozen preregistration record; the execution status is completed in this aggregate and memo. No unfavorable seed/condition was excluded. These are seed replications on one machine, not repeated fixed-job timings. Small total effects remain timing-inconclusive. Identical mappings imply no accuracy advantage; weak WS quality and dense storage remain limitations. No 10K, real-data, long-stream or CPU parallelism claim follows.
'''
    text += """
Decision: refined feature maintenance is faster than conservative feature maintenance in all 30 seed streams. At 0.1%, median feature-stage gains are 1.41× BA, 1.31× ER and 1.12× WS; cost-stage gains over conservative dirty supersets are 1.61×, 1.65× and 1.43×. Conservative controls recompute 1.45–1.96× as many second-layer rows and 1.43–1.78× as many cost entries at these condition medians. These are validated component improvements beyond simpler locality and count as better outcomes.

At 1%, feature medians still favor refined maintenance by 1.05–1.09×. Cost medians are 0.99× BA, 1.04× ER and 1.11× WS. BA costs therefore do not improve despite a 1.05× cost-entry work ratio. Including conservative support construction gives a BA cost-plus-support ratio of 1.08×, but that is a different measurement, not a bare-cost win. This counterexample prevents equating avoided entries with lower measured latency.

Most total savings come from locality shared by all maintained methods. Conservative/refined setup-inclusive median ratios range 1.004–1.044 for feature controls and 1.006–1.053 for cost controls; these small differences need fixed-job repetition for robust timing claims. Refined/full setup-inclusive medians range 1.25–2.85×. All maintained methods preserve identical quality, and memory outcomes must remain separate from time benefits.

Paper progress: closer through an explicit attribution control showing consistent refined feature benefits and sparse cost benefits. This strengthens a component-focused empirical result; it does not overcome E14's prior-art overlap or establish a new propagation algorithm. Weak WS correspondence, dense memory, real-topology/longer-stream evidence and certified CPU repair remain gaps. Next isolate repeated-execution variability for E13's near-one 5K BA/WS totals using the fixed-job [E16 timing protocol](e16_protocol.md). Do not use a 1K component gain to claim a robust 5K whole-pipeline gain.
"""
    text += "\n## All maintained methods versus full\n\nEach cell is a paired-seed median. Ratios above one favor maintenance for latency and indicate more memory for RSS.\n\n| Topology | Budget | Method | Update-only full/method | Setup + updates full/method | Method/full peak RSS |\n|---|---|---|---|---|---|\n"
    for c in conditions:
        d=c['distributions']
        for method in config['methods'][1:]:
            text += f"| {c['family'].upper()} | {c['requested_fraction']:.1%} | {method} | {d[method+'_update_speedup']['median']:.3f} | {d[method+'_total_speedup']['median']:.3f} | {d[method+'_rss_ratio']['median']:.3f} |\n"
    Path('docs/e15_findings.md').write_text(text)
    print(json.dumps(conditions,indent=2))


if __name__=='__main__':summarize()
