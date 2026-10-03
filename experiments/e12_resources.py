"""Sequential isolated resource profiles; frozen maintenance kernels."""
import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
import networkx as nx
from src.topology_pairs import topology_pair
from src.update_protocols import paired_updates, observation_mask
from src.metrics import quality
from experiments.e10_costs import setup, advance
from experiments.e06_dynamic_assignment import digest


def fingerprint(array):
    array=np.asarray(array)
    if not array.flags.c_contiguous:
        raise ValueError('Fingerprint requires contiguous storage')
    return hashlib.sha256(memoryview(array).cast('B')).hexdigest()


def snapshot(context,graphs,truth,step,timings):
    start=perf_counter()
    features=context['features']
    normalized=[x/context['scale'] for x in features]
    if context['cost_cache']:
        np.testing.assert_array_equal(normalized[0],context['cost_cache'].source)
        np.testing.assert_array_equal(normalized[1],context['cost_cache'].target)
    costs=context['costs'];mapping=context['mapping']
    result=dict(step=step,timings=timings,
        hashes=dict(features=[fingerprint(x) for x in features],normalized=[fingerprint(x) for x in normalized],
                    costs=fingerprint(costs),scale=fingerprint(context['scale']),mapping=fingerprint(mapping)),
        objective=float(costs[np.arange(len(costs)),mapping].sum()),quality=quality(*graphs,mapping,truth))
    result['validation_time']=perf_counter()-start
    return result


def worker(n,family,method):
    config=json.loads(Path('configs/e12_resources.json').read_text())
    generation_start=perf_counter()
    g,h,truth,bundle=topology_pair(n,config['seed'],config['noise'],family)
    generation_time=perf_counter()-generation_start
    mask=observation_mask(g,h,truth)
    context=setup([g,h],method)
    initialization_time=context['initialization_time']
    records=[snapshot(context,[g,h],truth,0,context['initialization_stages'])]
    array_bytes=dict(dense_cost=context['costs'].nbytes,
        descriptors=sum(c.nbytes for c in context['caches']) if context['caches'] else 0,
        normalized=context['cost_cache'].normalized_feature_bytes if context['cost_cache'] else 0)
    # Full recomputation has no need to retain its previous cost matrix.
    if method=='full_scipy':context['costs']=None
    budget=max(1,int(config['requested_fraction']*(g.number_of_edges()+h.number_of_edges())/2+.5))
    for step in range(1,config['steps']+1):
        old=[g,h]
        source=int(np.random.SeedSequence([bundle[3],step,0]).generate_state(1)[0])
        target=int(np.random.SeedSequence([bundle[3],step,1]).generate_state(1)[0])
        start=perf_counter()
        ng,nh,gb,hb=paired_updates(g,h,truth,budget,source,target,'shared_latent')
        apply_time=perf_counter()-start
        assert observation_mask(ng,nh,truth)==mask
        _,timings=advance(context,old,[ng,nh],[gb,hb],method)
        record=snapshot(context,[ng,nh],truth,step,timings)
        record.update(generation_time=apply_time,edits=2*budget,
            realized_fraction=2*budget/(g.number_of_edges()+h.number_of_edges()))
        records.append(record)
        if method=='full_scipy':context['costs']=None
        g,h=ng,nh
    result=dict(nodes=n,family=family,method=method,seed=config['seed'],records=records,
        initialization_time=initialization_time,update_time=sum(r['timings']['pipeline_time'] for r in records[1:]),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        array_bytes=array_bytes,generation_time=generation_time)
    result['total_time']=result['initialization_time']+result['update_time']
    print(json.dumps(result))


def headroom():
    mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:','MemTotal:'))}
    base=Path('/sys/fs/cgroup')
    folders={base}
    membership=Path('/proc/self/cgroup').read_text()
    for line in membership.splitlines():
        hierarchy,controllers,relative=line.split(':',2)
        if hierarchy=='0':
            folder=base/relative.lstrip('/')
            while folder==base or base in folder.parents:
                folders.add(folder)
                if folder==base:break
                folder=folder.parent
    paths=[folder/'memory.max' for folder in sorted(folders)]+[base/'memory/memory.limit_in_bytes']
    limits={str(p):p.read_text().strip() for p in paths if p.exists()}
    current_paths=[folder/'memory.current' for folder in sorted(folders)]+[base/'memory/memory.usage_in_bytes']
    usage={str(p):int(p.read_text()) for p in current_paths if p.exists()}
    available=mem['MemAvailable']
    for path,value in limits.items():
        if value.isdigit():
            current=usage.get(path.replace('memory.max','memory.current').replace('memory.limit_in_bytes','memory.usage_in_bytes'),0)
            available=min(available,max(0,int(value)-current))
    address_limit=resource.getrlimit(resource.RLIMIT_AS)[0]
    if address_limit!=resource.RLIM_INFINITY:available=min(available,address_limit)
    return dict(**mem,visible_cgroup_limits=limits,visible_cgroup_usage=usage,
                address_space_soft_limit=address_limit,effective_available_bytes=available,
                cgroup_membership=membership)


def run():
    config_path=Path('configs/e12_resources.json');config=json.loads(config_path.read_text())
    results=[];preflight=[]
    output_path=Path('results/raw/e12_resources.jsonl')
    with output_path.open('w') as stream:
        for n in config['sizes']:
            memory=headroom()
            estimate=4*n*n*8+256*1024**2
            permitted=estimate<=memory['effective_available_bytes']/2
            preflight.append(dict(nodes=n,memory=memory,conservative_estimate_bytes=estimate,permitted=permitted))
            if not permitted:
                print(f'n={n}: resource gate skipped',flush=True);continue
            for family in config['families']:
                pair=[]
                for method in config['methods']:
                    command=[sys.executable,'-m','experiments.e12_resources','--worker','--nodes',str(n),'--family',family,'--method',method]
                    child=subprocess.run(command,capture_output=True,text=True,check=True)
                    result=json.loads(child.stdout)
                    pair.append(result);results.append(result)
                    stream.write(json.dumps(result)+'\n');stream.flush()
                    print(f'n={n}, {family}, {method}: RSS={result["peak_rss_bytes"]/1024**2:.1f} MiB, total={result["total_time"]:.3f}s',flush=True)
                for a,b in zip(pair[0]['records'],pair[1]['records']):
                    assert a['hashes']==b['hashes'] and a['objective']==b['objective']
    sources=sorted(Path('src').glob('*.py'))+[Path(__file__),Path('experiments/e10_costs.py'),Path('experiments/e06_dynamic_assignment.py')]
    cpu=[line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')]
    Path('results/raw/e12_resources.metadata.json').write_text(json.dumps(dict(config=config,config_hash=digest(config_path),
        source_hashes={str(p):digest(p) for p in sources},preflight=preflight,python=platform.python_version(),
        platform=platform.platform(),cpu_count=os.cpu_count(),cpu_model=cpu[0] if cpu else None,
        numpy=np.__version__,scipy=scipy.__version__,networkx=nx.__version__,
        rss_scope='whole fresh worker including imports, generation, setup, updates, fingerprints and quality',
        timing_scope='graph-to-assignment stages, generation and validation excluded',
        caveat='only visible cgroup limits inspected; no hidden-limit guarantee'),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true')
    parser.add_argument('--nodes',type=int);parser.add_argument('--family');parser.add_argument('--method')
    args=parser.parse_args()
    if args.worker:worker(args.nodes,args.family,args.method)
    else:run()
