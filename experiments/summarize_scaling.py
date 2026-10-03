"""Paired seed distributions; correlated stream steps remain within workers."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def distribution(values):
    q=np.quantile(values,[0,.25,.5,.75,1])
    return dict(zip(['min','q25','median','q75','max'],map(float,q)))


def summarize():
    rows=[json.loads(x) for x in Path('results/raw/e13_scaling.jsonl').read_text().splitlines()]
    metadata=json.loads(Path('results/raw/e13_scaling.metadata.json').read_text());config=metadata['config']
    assert len(rows)==60 and all(p['permitted'] for p in metadata['preflight'])
    lookup={(r['nodes'],r['family'],r['seed'],r['method']):r for r in rows}
    assert len(lookup)==len(rows)
    pairs=[];conditions=[]
    for n in config['sizes']:
        for family in config['families']:
            selected=[]
            for seed in config['seeds']:
                full=lookup[n,family,seed,'full_scipy'];new=lookup[n,family,seed,'persistent_scipy']
                assert len(full['records'])==len(new['records'])==4
                assert full['order']==new['order'] and full['position']!=new['position']
                assert all(a['hashes']==b['hashes'] and a['objective']==b['objective'] for a,b in zip(full['records'],new['records']))
                p=dict(nodes=n,family=family,seed=seed,order=full['order'],total_speedup=full['total_time']/new['total_time'],update_speedup=full['update_time']/new['update_time'],persistent_rss_ratio=new['peak_rss_bytes']/full['peak_rss_bytes'],full_rss_mib=full['peak_rss_bytes']/1024**2,persistent_rss_mib=new['peak_rss_bytes']/1024**2,initial_nc=new['records'][0]['quality']['nc'],final_nc=new['records'][-1]['quality']['nc'])
                for key in ['feature_time','cost_time','solver_time']:
                    old=sum(r['timings'][key] for r in full['records'][1:]);fresh=sum(r['timings'][key] for r in new['records'][1:])
                    p[key+'_speedup']=old/fresh;p['persistent_'+key]=fresh;p['full_'+key]=old
                pairs.append(p);selected.append(p)
            keys=[k for k,v in selected[0].items() if isinstance(v,(float,int)) and k not in ['nodes','seed']]
            conditions.append(dict(nodes=n,family=family,seeds=config['seeds'],distributions={k:distribution([p[k] for p in selected]) for k in keys},total_wins=sum(p['total_speedup']>1 for p in selected)))
    result=dict(worker_runs=len(rows),paired_bundles=len(pairs),matching_snapshots=120,conditions=conditions,pairs=pairs)
    Path('results/aggregate/e13_scaling.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    labels=[f"{c['nodes']//1000}K {c['family'].upper()}" for c in conditions]
    for ax,key,label in zip(axes,['total_speedup','persistent_rss_ratio'],['Full / persistent setup + three updates','Persistent / full peak RSS']):
        data=[[p[key] for p in pairs if (p['nodes'],p['family'])==(c['nodes'],c['family'])] for c in conditions]
        ax.boxplot(data,tick_labels=labels,showfliers=True)
        for i,values in enumerate(data,1):ax.scatter([i]*5,values,s=14,alpha=.7)
        ax.axhline(1,color='gray',linestyle='--');ax.set_ylabel(label)
    fig.suptitle('E13: five paired seed bundles per condition; three updates per worker')
    fig.tight_layout();fig.savefig('results/figures/e13_scaling.png',dpi=180)
    table=[]
    for c in conditions:
        d=c['distributions']
        def value(key):
            v=d[key];return f"{v['median']:.2f} [{v['q25']:.2f}, {v['q75']:.2f}]; {v['min']:.2f}–{v['max']:.2f}"
        table.append(f"| {c['nodes']:,} | {c['family'].upper()} | {value('feature_time_speedup')} | {value('cost_time_speedup')} | {value('update_speedup')} | {value('total_speedup')} | {value('persistent_rss_ratio')} | {c['total_wins']}/5 |")
    text='''# E13 findings: replicated bounded scaling

Completed 60 sequential fresh-worker runs: 30 paired seed bundles, with five fresh seeds (61–65) per size/topology. All 120 setup/update snapshots agree exactly in features, normalized features, scale, costs, mapping and objective. All planned conditions passed visible resource preflight. First-worker order alternates, balanced across all pairs. Frozen E12 numerical kernels and cost-matrix lifecycle are preserved.

Each cell reports median [Q25, Q75]; minimum–maximum across five paired seeds. Timing ratios are full/persistent; RSS ratios are persistent/full. Three correlated updates are summed within each worker, not treated as independent samples. Total includes actual initialization. RSS is the whole-worker high-water mark including validation and quality; generation and validation are excluded from stage timings.

| Nodes | Topology | Feature ratio | Cost ratio | Update ratio | Setup + updates ratio | RSS ratio | Total wins |
|---|---|---|---|---|---|---|---|---|
'''+ '\n'.join(table)+'''

All seed observations, stage seconds, quality controls and RSS MiB are retained in the aggregate. Boxplots show seed distributions and individual pairs; they are not confidence intervals. These are independent graph/edit seeds on one machine, not repeated executions of identical jobs. Near-one total ratios must be interpreted with that timing limitation. Resource gates inspect visible limits only.

Component gains are positive evidence even when total gains are small: the compiled assignment stage still dominates at larger sizes. Exact matching agreement demonstrates objective maintenance, not better correspondence accuracy. Maintained memory overhead and quadratic dense storage remain limitations. Noise, update budget and three-step stream length were deliberately fixed; no broad scaling or long-stream claim follows.
'''
    text += """
Decision: across all 30 paired bundles, observed setup-inclusive ratios favor maintenance. At 5K, median feature gains are 7.74× BA, 14.20× ER and 17.92× WS; cost gains are 1.84×, 3.64× and 5.42×. Setup-inclusive medians are 1.03×, 1.24× and 1.03×, with respective ranges 1.02–1.04×, 1.13–1.28× and 1.01–1.04×. Five seed bundles strengthen the component result, but the small BA/WS total effects still need repeated execution to separate timing variability.

Median 5K persistent peak RSS is 354.2 MiB BA, 343.4 MiB ER and 315.8 MiB WS; paired persistent/full median ratios are 1.17, 1.14 and 1.06. Dense assignment consumes about 97.8–97.9% of maintained BA update stages, 93.3–97.7% ER and 99.4–99.5% WS. Optimizing descriptor/cost work alone therefore has limited remaining total-latency headroom at this size.

Median initial/final NC at 5K is 96.36%/93.00% BA, 88.12%/87.86% ER and 15.64%/15.26% WS. These diagnostics preserve the objective-quality limitation; they do not show a maintenance accuracy benefit. Forty-four tests pass, including fresh-seed worker equality; all frozen E12 source hashes remain unchanged.

Paper progress: closer through replicated exact component efficiency and bounded 5K viability. This supports a component-focused experimental result even where total benefits are small and memory rises. It does not establish novelty, useful WS correspondence, broad noise/budget robustness, long-stream scaling or certified CPU decomposition. Next execute the [primary-source contribution audit](post_e13_research_gate.md) before expanding compute or claiming a new assignment method.
"""
    Path('docs/e13_findings.md').write_text(text)
    print(json.dumps({k:v for k,v in result.items() if k!='pairs'},indent=2))


if __name__=='__main__':summarize()
