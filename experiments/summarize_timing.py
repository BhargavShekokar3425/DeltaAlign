"""Hierarchical fixed-job repetitions: executions within seed, then five seeds."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from experiments.summarize_scaling import distribution
from experiments.e16_timing import validate
from experiments.e06_dynamic_assignment import digest


def summarize():
    raw=Path('results/raw/e16_timing.jsonl');metadata_path=Path('results/raw/e16_timing.metadata.json')
    metadata=json.loads(metadata_path.read_text());config=metadata['config']
    assert metadata['execution_status']=='completed'
    assert digest(Path('configs/e16_timing.json'))==metadata['config_hash']
    assert digest(Path(config['fixed_job_source']))==metadata['frozen_config_hash']
    assert digest(Path('results/raw/e13_scaling.jsonl'))==metadata['reference_hash']
    assert digest(Path('results/raw/e13_scaling.metadata.json'))==metadata['reference_metadata_hash']
    assert all(g['permitted'] for g in metadata['preflight'])
    rows=[json.loads(line) for line in raw.read_text().splitlines()]
    assert len(rows)==60
    lookup={(r['family'],r['seed'],r['round'],r['method']):r for r in rows}
    assert len(lookup)==60
    historical=[json.loads(line) for line in Path('results/raw/e13_scaling.jsonl').read_text().splitlines()]
    reference={(r['nodes'],r['family'],r['seed'],r['method']):r for r in historical}
    for path,h in metadata['source_hashes'].items():assert digest(Path(path))==h,path
    pairs=[];jobs=[];families=[]
    for family in config['families']:
        selected_jobs=[]
        for seed in config['seeds']:
            executions=[]
            for round_index in range(1,config['rounds']+1):
                full=lookup[family,seed,round_index,'full_scipy'];new=lookup[family,seed,round_index,'persistent_scipy']
                validate(full,new)
                for r in [full,new]:validate(r,reference[r['nodes'],family,seed,r['method']])
                assert full['order']==new['order'] and {full['position'],new['position']}=={0,1}
                p=dict(family=family,seed=seed,round=round_index,order=full['order'],total_speedup=full['total_time']/new['total_time'],update_speedup=full['update_time']/new['update_time'],rss_ratio=new['peak_rss_bytes']/full['peak_rss_bytes'],full_total_seconds=full['total_time'],persistent_total_seconds=new['total_time'],full_update_seconds=full['update_time'],persistent_update_seconds=new['update_time'],full_setup_seconds=full['initialization_time'],persistent_setup_seconds=new['initialization_time'],full_peak_rss_mib=full['peak_rss_bytes']/1024**2,persistent_peak_rss_mib=new['peak_rss_bytes']/1024**2,initial_quality=new['records'][0]['quality'],final_quality=new['records'][-1]['quality'])
                for stage in ['feature_time','cost_time','solver_time']:
                    old=sum(v['timings'][stage] for v in full['records'][1:]);fresh=sum(v['timings'][stage] for v in new['records'][1:])
                    p[stage+'_speedup']=old/fresh;p['full_'+stage]=old;p['persistent_'+stage]=fresh
                pairs.append(p);executions.append(p)
            keys=[k for k,v in executions[0].items() if isinstance(v,(float,int)) and k not in ['seed','round']]
            full_times=[e['full_total_seconds'] for e in executions];new_times=[e['persistent_total_seconds'] for e in executions]
            job=dict(family=family,seed=seed,executions=executions,distributions={k:distribution([e[k] for e in executions]) for k in keys},total_wins=sum(e['total_speedup']>1 for e in executions),total_time_ranges_overlap=max(min(full_times),min(new_times))<=min(max(full_times),max(new_times)),full_relative_total_range=(max(full_times)-min(full_times))/np.median(full_times),persistent_relative_total_range=(max(new_times)-min(new_times))/np.median(new_times))
            jobs.append(job);selected_jobs.append(job)
        keys=list(selected_jobs[0]['distributions'])
        family_record=dict(family=family,independent_seed_jobs=5,paired_executions=15,distributions_of_seed_medians={k:distribution([j['distributions'][k]['median'] for j in selected_jobs]) for k in keys},total_wins=sum(j['total_wins'] for j in selected_jobs),jobs_with_overlapping_total_ranges=sum(j['total_time_ranges_overlap'] for j in selected_jobs),full_relative_total_range=distribution([j['full_relative_total_range'] for j in selected_jobs]),persistent_relative_total_range=distribution([j['persistent_relative_total_range'] for j in selected_jobs]),order_descriptives={})
        for first in config['methods']:
            values=[p['total_speedup'] for p in pairs if p['family']==family and p['order'][0]==first]
            family_record['order_descriptives'][first]=dict(executions=len(values),total_speedup=distribution(values))
        families.append(family_record)
    assert sum(p['order'][0]=='full_scipy' for p in pairs)==15
    result=dict(execution_status='completed',worker_runs=60,fixed_seed_jobs=10,paired_executions=30,matching_snapshots=120,all_match_e13=True,metadata_hash=digest(metadata_path),raw_hash=digest(raw),families=families,jobs=jobs,pairs=pairs)
    Path('results/aggregate/e16_timing.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    colors={'ba':'tab:blue','ws':'tab:orange'}
    for i,j in enumerate(jobs):
        ratios=[e['total_speedup'] for e in j['executions']]
        axes[0].scatter([i-.12,i,i+.12],ratios,color=colors[j['family']],s=25)
        axes[0].plot([i-.2,i+.2],[np.median(ratios)]*2,color='black')
        for method,offset in [('full_total_seconds',-.12),('persistent_total_seconds',.12)]:
            times=[e[method] for e in j['executions']]
            axes[1].scatter([i+offset]*3,times,marker='o' if method.startswith('full') else 'x',color=colors[j['family']],s=25)
    labels=[f"{j['family'].upper()} {j['seed']}" for j in jobs]
    for ax in axes:ax.set_xticks(range(10),labels,rotation=45);ax.set_xlabel('Fixed graph/edit seed job; three execution rounds')
    axes[0].axhline(1,color='gray',linestyle='--');axes[0].set_ylabel('Paired full / persistent setup + three updates')
    axes[1].set_ylabel('Setup + three updates (seconds)')
    axes[1].legend(handles=[Line2D([],[],color='black',marker='o',linestyle='None',label='Full'),Line2D([],[],color='black',marker='x',linestyle='None',label='Persistent')],loc='upper left')
    fig.suptitle('E16: three execution rounds per fixed 5K job');fig.tight_layout(rect=(0,0,1,.95));fig.savefig('results/figures/e16_timing.png',dpi=180)
    table=[]
    for j in jobs:
        d=j['distributions'];ratio=d['total_speedup']
        repetitions=', '.join(f"{e['total_speedup']:.4f}" for e in j['executions'])
        table.append(f"| {j['family'].upper()} | {j['seed']} | {repetitions} | {ratio['median']:.4f} | {d['full_total_seconds']['min']:.3f}–{d['full_total_seconds']['max']:.3f} | {d['persistent_total_seconds']['min']:.3f}–{d['persistent_total_seconds']['max']:.3f} | {j['total_wins']}/3 |")
    text='''# E16 findings: repeated fixed-job timing

Completed 60 sequential fresh workers, three paired execution rounds within each of ten fixed 5K BA/WS seed jobs (61–65). All 120 paired setup/update snapshots match features, normalized features, scales, costs, mapping and objective, and every worker matches the saved E13 job fingerprints/objectives. All three round-level visible resource gates passed. Forty-seven tests pass, including rejection of historical fingerprint/objective/step drift. Historical kernels remain unchanged.

The E13 workers, initialization, graph/edit construction and cost-matrix lifecycle are frozen. Each total counts actual setup plus three shared-latent 0.1% updates under 1% initial noise. Stage timing excludes graph generation and validation; whole-worker RSS includes them. Method-first order is balanced across all 30 pairs; timestamps, hardware/software, inherited thread environment, hashes and headroom are saved. No first round, slower repeat or seed was discarded. Config status remains the frozen preregistration label; execution completion is recorded separately.

| Topology | Seed | Paired total ratios, rounds 1/2/3 | Median ratio | Full seconds range | Persistent seconds range | Observed wins |
|---|---|---|---|---|---|---|
'''+ '\n'.join(table)+ '\n\n## Across five per-seed medians\n\n'
    for f in families:
        d=f['distributions_of_seed_medians']
        def fmt(k):
            v=d[k];return f"{v['median']:.4f} [Q25 {v['q25']:.4f}, Q75 {v['q75']:.4f}]; range {v['min']:.4f}–{v['max']:.4f}"
        text+=f"- **{f['family'].upper()}**: feature ratio {fmt('feature_time_speedup')}; cost ratio {fmt('cost_time_speedup')}; update-only ratio {fmt('update_speedup')}; setup-inclusive ratio {fmt('total_speedup')}; persistent/full RSS ratio {fmt('rss_ratio')}. Total directions favor maintenance in {f['total_wins']}/15 executions; {f['jobs_with_overlapping_total_ranges']}/5 jobs have overlapping full/persistent total-time ranges across rounds.\n"
    text+='''
Each seed's three paired ratios are summarized first, then the five seed medians are summarized by topology. Fifteen executions per topology are not fifteen independent graph/edit seeds. The aggregate retains all raw stage/setup/update seconds, within-job ranges, RSS, quality and order descriptives. Box/point summaries are descriptive, not confidence intervals or significance tests. Historical E13 measurements are context, not a fourth repeat.

Repeated timing evidence is workload/machine-specific and does not establish algorithm novelty or useful WS correspondence. Component improvements count positively regardless of the total outcome. Larger noise/budgets, long streams, real topology and certified CPU decomposition remain untested here. Dense quadratic storage and higher maintained memory remain limitations.
'''
    text += """
## Decision and paper progress

BA's across-seed median total ratio is 1.0391×; every execution favors maintenance, and each job's observed full/persistent time ranges are separated. Full relative within-job timing ranges are 0.50–1.51%, maintained ranges 0.40–0.89%. This supports a small repeatable setup-inclusive saving for these fixed BA jobs on this machine, not broad scalability or a statistical guarantee.

WS's across-seed median total ratio is 1.0341×, but seed 63 reverses direction in round 1 (0.9637×) and its maintained timing range spans 6.31%. The other four WS jobs favor maintenance throughout; 14/15 WS executions favor it overall. Thus median savings are positive and generally consistent, while a uniformly robust whole-pipeline WS win remains unsupported. No repeat is discarded, and no extra repetitions were added after seeing the reversal.

Component gains persist under repetition: BA feature/cost median ratios are 7.79×/1.86× and WS 17.96×/5.37×. These remain positive outcomes even where total timing is variable. Median persistent/full peak-RSS ratios are 1.182 BA and 1.058 WS, approximately 18% and 6% more memory. All mappings and quality remain E13's; no new correspondence-quality benefit or graph-seed robustness is claimed.

Order descriptives favor maintenance at their medians for either first method: BA 1.0379× full-first / 1.0359× maintained-first; WS 1.0367× / 1.0300×. They are descriptive execution groups, not independent-seed significance tests or proof that order has no effect.

Paper progress is positive through repeated component efficiency, a modest consistent BA total result and honest calibration of WS variability. The work is closer to a defensible empirical component paper; E14 novelty overlap, weak WS quality, quadratic dense memory and missing real-topology/longer-stream evidence remain. More synthetic repetitions are not the next priority. Execute the [bounded real-topology provenance and initial-quality gate](real_topology_gate.md): verify ingestion/projection of one real topology, then freeze a small matching/maintenance pilot. Do not expand to 10K, claim natural correspondence from synthetic permutations, or start parallel assignment without a certificate.
"""
    Path('docs/e16_findings.md').write_text(text)
    print(json.dumps(families,indent=2))


if __name__=='__main__':summarize()
