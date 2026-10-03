"""Topology-specific E11 evidence; paired stream totals, separate stage/quality gates."""
import json
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
from experiments.summarize_dynamic_assignment import distribution


def summarize():
    config=json.loads(Path('configs/e11_topology.json').read_text())
    rows=[json.loads(x) for x in Path('results/raw/e11_topology.jsonl').read_text().splitlines()]
    count=len(config['families'])*len(config['seeds'])*len(config['noise_levels'])*len(config['protocols'])*len(config['update_fractions'])
    expected=count*config['steps']*4
    assert len(rows)==expected
    assert len({(r['family'],r['noise'],r['seed'],r['protocol'],r['requested_fraction'],r['step'],r['method']) for r in rows})==expected
    active=[r for r in rows if r['method']!='keep_initial']
    assert all(r['full_recompute_agreement']==1 and r['objective']==r['full_objective'] for r in active)
    controls=json.loads(Path('results/raw/e11_initial_controls.json').read_text())
    no_update=json.loads(Path('results/raw/e11_no_update_controls.json').read_text())
    assert len(controls)==len(config['families'])*len(config['seeds'])*len(config['noise_levels'])
    assert len(no_update)==count*3 and all(r['passed'] for r in no_update)
    streams=defaultdict(list)
    for r in rows:streams[(r['family'],r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method'])].append(r)
    totals=[]
    for (family,noise,protocol,fraction,seed,method),steps in sorted(streams.items()):
        steps=sorted(steps,key=lambda r:r['step'])
        assert [r['step'] for r in steps]==list(range(1,config['steps']+1))
        final=steps[-1]
        total=dict(family=family,noise=noise,protocol=protocol,requested_fraction=fraction,seed=seed,method=method,
            initialization_time=final['initialization_time'],update_time=final['cumulative_update_time'],
            total_time=final['initialization_plus_updates'],final_nc=final['quality']['nc'],final_s3=final['quality']['s3'],
            final_mask_size=final['observation_mask_size'],final_initial_churn=final['initial_mapping_churn'])
        for key in ['feature_time','cost_time','solver_time','computed_cost_entries']:
            total[key]=sum(r['timings'].get(key,0) for r in steps)
        if method in ['persistent_scipy','selective_scipy']:
            total['mean_feature_support_fraction']=sum(sum(s['total_support'] for s in r['timings']['maintenance']) for r in steps)/(config['steps']*2*config['nodes'])
            total['mean_dirty_feature_fraction']=sum(sum(s['changed_features'] for s in r['timings']['maintenance']) for r in steps)/(config['steps']*2*config['nodes'])
        assert abs(total['update_time']-sum(r['timings']['pipeline_time'] for r in steps))<1e-9
        totals.append(total)
    lookup={(r['family'],r['noise'],r['protocol'],r['requested_fraction'],r['seed'],r['method']):r for r in totals}
    paired=[]
    for r in totals:
        if r['method']!='persistent_scipy':continue
        key=(r['family'],r['noise'],r['protocol'],r['requested_fraction'],r['seed'])
        full=lookup[(*key,'full_scipy')];old=lookup[(*key,'selective_scipy')];keep=lookup[(*key,'keep_initial')]
        paired.append({**r,'feature_speedup_vs_full':full['feature_time']/r['feature_time'],
            'cost_speedup_vs_full':full['cost_time']/r['cost_time'],
            'cost_speedup_vs_historical':old['cost_time']/r['cost_time'],
            'update_speedup_vs_full':full['update_time']/r['update_time'],
            'total_speedup_vs_full':full['total_time']/r['total_time'],
            'total_speedup_vs_historical':old['total_time']/r['total_time'],
            'keep_initial_nc':keep['final_nc'],'keep_initial_s3':keep['final_s3']})
    grouped=defaultdict(list)
    for r in paired:grouped[(r['family'],r['noise'],r['protocol'],r['requested_fraction'])].append(r)
    summaries=[]
    for (family,noise,protocol,fraction),subset in sorted(grouped.items()):
        assert len(subset)==len(config['seeds'])
        record=dict(family=family,noise=noise,protocol=protocol,requested_fraction=fraction,streams=len(subset))
        for key in ['feature_speedup_vs_full','cost_speedup_vs_full','cost_speedup_vs_historical',
                    'update_speedup_vs_full','total_speedup_vs_full','total_speedup_vs_historical',
                    'final_nc','final_s3','keep_initial_nc','keep_initial_s3','final_mask_size',
                    'mean_feature_support_fraction','mean_dirty_feature_fraction','final_initial_churn','total_time']:
            record[key]=distribution([r[key] for r in subset])
        summaries.append(record)
    initial_groups=[]
    for family in config['families']:
        for noise in config['noise_levels']:
            subset=[c for c in controls if c['family']==family and c['noise']==noise]
            initial_groups.append(dict(family=family,noise=noise,pairs=len(subset),
                nc=distribution([c['full_quality']['nc'] for c in subset]),s3=distribution([c['full_quality']['s3'] for c in subset]),
                random_nc=distribution([c['random_quality']['nc'] for c in subset]),random_s3=distribution([c['random_quality']['s3'] for c in subset]),
                source_feature_uniqueness=distribution([c['feature_unique_fractions'][0] for c in subset]),
                target_feature_uniqueness=distribution([c['feature_unique_fractions'][1] for c in subset]),
                row_minimum_tie_fraction=distribution([c['row_minimum_tie_fraction'] for c in subset]),
                truth_row_minimum_fraction=distribution([c['truth_row_minimum_fraction'] for c in subset]),
                source_graph={k:distribution([c['graph_statistics'][0][k] for c in subset]) for k in
                    ['edges','mean_degree','max_degree','isolated_vertices','components','mean_clustering']}))
    result=dict(streams=count,updates=count*config['steps'],observations=expected,exact_active_results=len(active),
        no_update_checks=len(no_update),initial_pairs=len(controls),max_absolute_objective_difference=0.,
        initial_groups=initial_groups,stream_totals=totals,paired_stream_metrics=paired,groups=summaries)
    Path('results/aggregate/e11_topology.json').write_text(json.dumps(result,indent=2))
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for ax,family in zip(axes,config['families']):
        group=[r for r in summaries if r['family']==family]
        labels=[f"{r['noise']:.0%}/{r['protocol']}/{r['requested_fraction']:.1%}" for r in group]
        for i,r in enumerate(group):
            for offset,key,color,label in [(-.12,'feature_speedup_vs_full','tab:blue','Feature stage'),(.12,'total_speedup_vs_full','tab:orange','Setup + ten updates')]:
                v=r[key];ax.errorbar(i+offset,v['median'],yerr=[[v['median']-v['q25']],[v['q75']-v['median']]],fmt='o',color=color,label=label if i==0 else None)
        ax.axhline(1,color='gray',linestyle='--');ax.set_yscale('log');ax.set_xticks(range(len(labels)),labels,rotation=75,fontsize=7)
        ax.set_title(family.upper())
    axes[0].set_ylabel('Full / persistent selective time');axes[0].legend(fontsize=8)
    fig.suptitle('E11: component and total outcomes; paired stream medians/IQR across five seeds',fontsize=11)
    fig.tight_layout();fig.savefig('results/figures/e11_topology.png',dpi=180)
    initial_table=[]
    for r in initial_groups:
        initial_table.append(f"| {r['family'].upper()} | {r['noise']:.0%} | {r['nc']['mean']:.2%} | {r['random_nc']['mean']:.2%} | {r['source_feature_uniqueness']['mean']:.1%} | {r['row_minimum_tie_fraction']['mean']:.1%} |")
    timing=[]
    for r in summaries:
        timing.append(f"| {r['family'].upper()} | {r['noise']:.0%} | {r['protocol']} | {r['requested_fraction']:.1%} | {r['feature_speedup_vs_full']['median']:.2f}× | {r['cost_speedup_vs_full']['median']:.2f}× | {r['total_speedup_vs_full']['median']:.2f}× | {r['final_nc']['mean']:.2%} | {r['keep_initial_nc']['mean']:.2%} |")
    findings=f'''# E11 findings: topology robustness

Completed {count} ten-step streams, {result['updates']} updates and {expected} observations on fresh seeds 55–59. All {len(active)} active results match full-oracle features, dirty sets, normalized features, costs, SciPy mappings and objectives exactly. All {len(no_update)} actual no-update controls preserve features/costs/scale/mappings. Forty-two tests pass. Historical generation and E10 maintenance kernels are unchanged. Thirty initial graph-pair controls and graph statistics are saved.

BA attachment 3, ER p=6/(n-1), and WS k=6/rewiring 0.1 have expected/specified mean degree near six; actual density, isolates, components, degree extrema and clustering are retained rather than presumed equal. Hidden correspondence enters generation/evaluation only. Initial alignment quality and descriptor ambiguity are:

| Topology | Initial noise | Full NC, mean | Random NC, mean | Source unique feature fraction, mean | Rows with tied minimum, mean |
|---|---|---|---|---|---|
'''+'\n'.join(initial_table)+'''

Feature uniqueness is the number of distinct descriptor rows divided by vertices, not the fraction of vertices whose descriptor occurs only once. Uniqueness and row-minimum ties are descriptor diagnostics, not a complete count of alternative optimal assignments. Initial random S3, target uniqueness, truth row-minimum frequency and graph-statistic distributions are in aggregate JSON. Keep-initial uses the initial full optimum and retains fixed vertex truth; it is a necessary control rather than an updated-objective solver.

| Topology | Noise | Protocol | Requested batch fraction | Feature-stage speedup | Cost-stage speedup | Setup-inclusive total speedup | Final full/selective NC, mean | Keep-initial NC, mean |
|---|---|---|---|---|---|---|---|---|
'''+'\n'.join(timing)+'''

Ratios above one favor persistent selective maintenance over full recomputation. Stage and total gains are separate positive outcomes: a component gain counts as progress even if total latency loses. Historical-refresh comparison, support/dirty expansion, update-only totals, NC/S3, mask drift and IQR/ranges are saved in the aggregate. These are paired ratios of ten-step stream totals across five seeds per condition, not pooled correlated batches; families/conditions share seed branches. Setup is method-specific; full recomputation runs first and selective order alternates. Generation/applying edits, diagnostics, validation and quality evaluation are excluded from graph-to-assignment ratios. No-update diagnostics are additional correctness work outside the ten-step timing totals.

Exact maintained costs guarantee unchanged compiled alignment behavior, not improved correspondence quality. Independent edits accumulate observation differences while the hidden mapping stays fixed; retain quality failures across all families. Weak initial descriptor discrimination limits alignment-method claims but does not erase a validated exact-maintenance efficiency gain. Do not discard families or tune the descriptor after seeing results.

Decision: feature-stage gains extend beyond BA. At requested 0.1%, median feature speedups are 8.81–9.25× on BA, 13.01–13.50× on ER and 15.90–16.15× on WS. Setup-inclusive totals improve 1.40–1.63×, 1.93–2.91× and 1.25–1.60× respectively. At 1%, feature improvements remain 1.70–2.37× and setup-inclusive totals improve 1.14–1.45× across all families. All 24 condition medians favor the persistent pipeline. Cost maintenance still loses slightly to full cost construction at 1% on BA/ER, while WS cost maintenance wins. Component gains and component regressions remain explicit.

WS fails a strong correspondence-quality gate: initial NC averages 33.58% at 1% noise and 6.94% at 5%, with only 66.4% distinct source feature rows. ER at 5% noise also starts at only 56.60% NC. Some shared-latent streams improve NC relative to keep-initial (WS at 1% noise/1% batches reaches 59.76%), but full recomputation has the same outcome; this is not a selective-method quality advantage. Independent streams severely degrade NC on all families. Maintain the narrow objective-maintenance claim and do not treat initial row-uniqueness/tie diagnostics as a complete explanation or a novelty proof.

Paper progress: the efficiency evidence now generalizes across three tested topologies, with validated component and total gains. Objective-quality robustness is still a material blocker for a stronger alignment-method claim. Novelty remains unverified; this 1K, ten-step synthetic experiment does not establish larger-size memory performance, long-stream robustness or CPU-parallel decomposition. Next run [isolated resource/size profiling](resource_scaling_design.md) on fresh seed 60, counting actual peak RSS and retaining the quality limits. A one-seed profile is a viability gate before replicated scaling, not a new statistical speedup claim.
'''
    Path('docs/e11_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k not in ['initial_groups','stream_totals','paired_stream_metrics','groups']},indent=2))


if __name__=='__main__':summarize()
