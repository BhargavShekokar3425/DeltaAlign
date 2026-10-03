import json
from pathlib import Path
import matplotlib.pyplot as plt


def summarize():
    rows=[json.loads(x) for x in Path('results/raw/e12_resources.jsonl').read_text().splitlines()]
    metadata=json.loads(Path('results/raw/e12_resources.metadata.json').read_text())
    config=metadata['config']
    permitted=[r['nodes'] for r in metadata['preflight'] if r['permitted']]
    assert len(rows)==len(permitted)*len(config['families'])*2
    lookup={(r['nodes'],r['family'],r['method']):r for r in rows}
    paired=[]
    for n in permitted:
        for family in config['families']:
            full=lookup[n,family,'full_scipy'];new=lookup[n,family,'persistent_scipy']
            assert len(full['records'])==len(new['records'])==config['steps']+1
            assert all(a['hashes']==b['hashes'] and a['objective']==b['objective'] for a,b in zip(full['records'],new['records']))
            record=dict(nodes=n,family=family,total_speedup=full['total_time']/new['total_time'],
                update_speedup=full['update_time']/new['update_time'],
                full_peak_rss_bytes=full['peak_rss_bytes'],persistent_peak_rss_bytes=new['peak_rss_bytes'],
                persistent_rss_ratio=new['peak_rss_bytes']/full['peak_rss_bytes'],
                full_total_time=full['total_time'],persistent_total_time=new['total_time'],
                array_bytes=new['array_bytes'],initial_nc=new['records'][0]['quality']['nc'],final_nc=new['records'][-1]['quality']['nc'])
            for key in ['feature_time','cost_time','solver_time']:
                old=sum(r['timings'][key] for r in full['records'][1:]);fresh=sum(r['timings'][key] for r in new['records'][1:])
                record[key+'_speedup']=old/fresh;record['persistent_'+key]=fresh;record['full_'+key]=old
            paired.append(record)
    result=dict(worker_runs=len(rows),paired_conditions=len(paired),matching_snapshots=len(paired)*(config['steps']+1),
                completed_sizes=permitted,profile_only=True,conditions=paired)
    Path('results/aggregate/e12_resources.json').write_text(json.dumps(result,indent=2))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for family in config['families']:
        selected=[r for r in paired if r['family']==family]
        x=[r['nodes'] for r in selected]
        axes[0].plot(x,[r['total_speedup'] for r in selected],marker='o',label=family.upper())
        axes[1].plot(x,[r['persistent_rss_ratio'] for r in selected],marker='o',label=family.upper())
    for ax in axes:ax.axhline(1,color='gray',linestyle='--');ax.set_xlabel('Vertices per graph');ax.legend()
    axes[0].set_ylabel('Full / persistent setup + three updates')
    axes[1].set_ylabel('Persistent / full whole-worker peak RSS')
    fig.suptitle('E12: single-seed resource profile; no replication or confidence intervals',fontsize=11)
    fig.tight_layout();fig.savefig('results/figures/e12_resources.png',dpi=180)
    table=[]
    for r in paired:
        table.append(f"| {r['nodes']:,} | {r['family'].upper()} | {r['feature_time_speedup']:.2f}× | {r['cost_time_speedup']:.2f}× | {r['total_speedup']:.2f}× | {r['full_peak_rss_bytes']/1024**2:.1f} | {r['persistent_peak_rss_bytes']/1024**2:.1f} | {r['final_nc']:.2%} |")
    findings=f'''# E12 findings: resource and size viability

Completed {len(rows)} sequential fresh-worker runs across {len(paired)} paired size/topology conditions on fresh seed 60. Sizes completed: {permitted}. All {result['matching_snapshots']} paired setup/update snapshots have identical feature, normalized-feature, scale, cost and mapping fingerprints and objectives. Forty-three tests pass, including small-instance fingerprint agreement and baseline cost release. This is one run per condition: no replicated scaling, statistical speedup or long-stream claim.

The final run uses corrected preflight inspection of visible cgroup session/ancestor limits, available memory and address-space soft limits; decisions and estimates are saved. A preliminary partial run was discarded when this inspection was expanded. Pre-existing topology/size/seed/update settings were unchanged. A 5K cost matrix alone is 200,000,000 bytes. Headroom estimation is conservative but cannot reveal hidden resource constraints.

| Nodes | Topology | Feature-stage speedup | Cost-stage speedup | Setup + three updates speedup | Full peak RSS MiB | Persistent peak RSS MiB | Final NC |
|---|---|---|---|---|---|---|---|
'''+'\n'.join(table)+'''

Stage ratios sum the three correlated updates within each worker; setup-inclusive ratios additionally count each method's actual initialization. Ratios above one favor maintenance for timings. RSS is the whole fresh-worker high-water mark, including imports, graph generation, setup, updates, fingerprint validation and quality evaluation. The RSS ratio in the aggregate is persistent/full, so values above one indicate more memory. Timing excludes generation and validation. Array storage and OS peak RSS are separate measurements.

Full recomputation discards each old dense matrix when no longer needed; persistent costs remain owned in place. This avoids an artificial baseline memory penalty. Contiguous-buffer fingerprints avoid another dense validation copy, while normalized-feature validation arrays and hashing/quality work still contribute to worker RSS. Both methods use the same frozen numerical kernels and deterministic graph/edit generation. No full oracle and maintained matrix coexist in a measured worker.

Component gains count as positive progress even if assignment limits total latency or persistent temporaries increase peak memory. Dense storage remains quadratic and solver scaling can dominate. Initial/final NC are diagnostic controls, not an accuracy advantage: identical mappings imply identical quality. E11's weak WS/high-noise quality and independent-stream decline remain limits.

Decision: 5K completed on all families. In this profile, feature-stage speedups are 6.52× BA, 13.05× ER and 18.53× WS; cost-stage speedups are 1.98×, 3.34× and 5.45×. Setup-inclusive ratios are only 1.032× BA, 1.185× ER and 1.032× WS because assignment dominates. Persistent peak RSS is 349.3/345.0/318.4 MiB versus full 302.6/299.7/302.7 MiB: approximately 5.2–15.4% more memory. Eliminating historical refresh copies does not imply lower memory than a full method that releases obsolete costs.

Paper progress: size viability and component gains are positive outcomes even with small total gains and higher peak RSS. A viable 5K run is not robust scaling evidence. Novelty, replicated larger-size timings, longer streams and certified parallel decomposition remain pending; initial WS quality at 5K is only 12.94% in this seed. Next follow the [bounded replicated scaling design](replicated_scaling_design.md): fresh seeds 61–65, 2K/5K and frozen three-update conditions, alternating method order. Preserve exact fingerprints and stage/RSS tradeoffs rather than extrapolate this single seed.
'''
    Path('docs/e12_findings.md').write_text(findings)
    print(json.dumps({k:v for k,v in result.items() if k!='conditions'},indent=2))


if __name__=='__main__':summarize()
