"""Persistent exact-maintenance stream pilot; historical kernels are frozen."""
import json
import platform
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from src.graph import graph_pair
from src.descriptors import descriptors
from src.descriptor_cache import initialize, update
from src.normalization import initial_scale
from src.candidates import refresh_costs
from src.dynamic_assignment import solve, repair, certificate
from src.update_protocols import paired_updates, observation_mask
from src.metrics import quality
from src.repair_metrics import fidelity
from experiments.e06_dynamic_assignment import digest


def setup(graphs, method):
    start = perf_counter()
    caches = [initialize(g) for g in graphs] if method != 'full_scipy' else None
    features = [c.features for c in caches] if caches else [descriptors(g,'two_hop_hist') for g in graphs]
    feature_time = perf_counter()-start
    cost_start = perf_counter()
    scale = initial_scale(*features)
    costs = cdist(features[0]/scale,features[1]/scale,'sqeuclidean')
    cost_time = perf_counter()-cost_start
    solver_start = perf_counter()
    if method == 'selective_dynamic':
        state, _ = solve(costs)
        mapping = state.mapping.copy()
    else:
        state = None
        rr, cc = linear_sum_assignment(costs)
        mapping = np.empty(len(costs),dtype=int);mapping[rr]=cc
    solver_time = perf_counter()-solver_start
    elapsed = perf_counter()-start
    return dict(caches=caches,features=features,scale=scale,costs=costs,state=state,mapping=mapping,
                initialization_time=elapsed,initialization_stages=dict(feature_time=feature_time,cost_time=cost_time,solver_time=solver_time))


def advance(context, old_graphs, new_graphs, batches, method):
    start = perf_counter()
    if method == 'full_scipy':
        features = [descriptors(g,'two_hop_hist') for g in new_graphs]
        dirty = None
        maintenance = []
    else:
        updates = [update(cache,old,new,batch) for cache,old,new,batch in zip(context['caches'],old_graphs,new_graphs,batches)]
        features = [c.features for c in context['caches']]
        dirty = [x[0] for x in updates]
        maintenance = [x[1] for x in updates]
    feature_time = perf_counter()-start
    cost_start = perf_counter()
    if method == 'full_scipy':
        costs = cdist(features[0]/context['scale'],features[1]/context['scale'],'sqeuclidean')
        rescored = len(costs)**2
    else:
        costs, rescored = refresh_costs(context['costs'],*features,*dirty,context['scale'])
    cost_time = perf_counter()-cost_start
    solver_start = perf_counter()
    if method == 'selective_dynamic':
        context['state'], stats = repair(context['state'],costs,*dirty)
        mapping = context['state'].mapping.copy()
    else:
        rr, cc = linear_sum_assignment(costs)
        mapping = np.empty(len(costs),dtype=int);mapping[rr]=cc
        stats = {}
    solver_time = perf_counter()-solver_start
    context.update(features=features,costs=costs,mapping=mapping)
    elapsed = perf_counter()-start
    return dirty,dict(feature_time=feature_time,cost_time=cost_time,solver_time=solver_time,
                     pipeline_time=elapsed,maintenance=maintenance,search_stats=stats,rescored_cost_entries=rescored)


def run():
    config_path=Path('configs/e09_streams.json')
    config=json.loads(config_path.read_text())
    methods=['full_scipy','selective_scipy','selective_dynamic']
    initial_records=[]
    with Path('results/raw/e09_streams.jsonl').open('w') as output:
        for noise in config['noise_levels']:
            for seed in config['seeds']:
                g,h,truth,bundle=graph_pair(config['nodes'],config['attachment'],seed,noise)
                for fraction in config['update_fractions']:
                    budget=max(1,int(fraction*(g.number_of_edges()+h.number_of_edges())/2+.5))
                    for protocol in config['protocols']:
                        identity=dict(seed=seed,noise=noise,requested_fraction=fraction,protocol=protocol)
                        contexts={m:setup([g,h],m) for m in methods}
                        reference=contexts['full_scipy']
                        initial_mapping=reference['mapping'].copy()
                        for method,c in contexts.items():
                            np.testing.assert_array_equal(c['costs'],reference['costs'])
                            np.testing.assert_array_equal(c['scale'],reference['scale'])
                            initial_objective=float(c['costs'][np.arange(config['nodes']),c['mapping']].sum())
                            expected=float(reference['costs'][np.arange(config['nodes']),initial_mapping].sum())
                            np.testing.assert_allclose(initial_objective,expected,rtol=1e-10,atol=1e-8)
                            if method=='selective_dynamic':certificate(c['state'],config['certificate_tolerance'])
                            initial_records.append({**identity,'method':method,'initialization_time':c['initialization_time'],
                                'timings':c['initialization_stages'],'cache_bytes':sum(x.nbytes for x in c['caches']) if c['caches'] else 0,
                                'dense_cost_bytes':c['costs'].nbytes,'initial_mapping_agreement':float(np.mean(c['mapping']==initial_mapping))})
                        cumulative={m:0. for m in methods}
                        cumulative['keep_initial']=0.
                        old_graphs=[g,h]
                        initial_mask=observation_mask(g,h,truth)
                        for step in range(1,config['steps']+1):
                            source_seed=int(np.random.SeedSequence([bundle[3],step,0]).generate_state(1)[0])
                            target_seed=int(np.random.SeedSequence([bundle[3],step,1]).generate_state(1)[0])
                            generation_start=perf_counter()
                            ng,nh,gb,hb=paired_updates(*old_graphs,truth,budget,source_seed,target_seed,protocol)
                            generation_time=perf_counter()-generation_start
                            new_graphs=[ng,nh]
                            if protocol=='shared_latent':assert observation_mask(ng,nh,truth)==initial_mask
                            previous={m:c['mapping'].copy() for m,c in contexts.items()}
                            previous_features=[f.copy() for f in reference['features']]
                            order=['full_scipy']+(['selective_dynamic','selective_scipy'] if step%2 else ['selective_scipy','selective_dynamic'])
                            outputs={m:advance(contexts[m],old_graphs,new_graphs,[gb,hb],m) for m in order}
                            validation_start=perf_counter()
                            certs={}
                            full=reference['mapping']
                            full_costs=reference['costs']
                            for m in ['selective_scipy','selective_dynamic']:
                                for actual,expected,old,dirty in zip(contexts[m]['features'],reference['features'],previous_features,outputs[m][0]):
                                    np.testing.assert_array_equal(actual,expected)
                                    assert dirty==set(np.flatnonzero(np.any(expected!=old,axis=1)))
                                np.testing.assert_array_equal(contexts[m]['costs'],full_costs)
                            np.testing.assert_array_equal(contexts['selective_scipy']['mapping'],full)
                            certs['selective_dynamic']=certificate(contexts['selective_dynamic']['state'],config['certificate_tolerance'])
                            validation_time=perf_counter()-validation_start
                            for m in methods+['keep_initial']:
                                mapping=contexts[m]['mapping'] if m in contexts else initial_mapping
                                old=previous[m] if m in previous else initial_mapping
                                timing=outputs[m][1] if m in outputs else dict(pipeline_time=0.,feature_time=0.,cost_time=0.,solver_time=0.)
                                cumulative[m]+=timing['pipeline_time']
                                init=contexts[m]['initialization_time'] if m in contexts else reference['initialization_time']
                                metrics=fidelity(full_costs,mapping,full,old)
                                if m!='keep_initial':assert abs(metrics['objective']-metrics['full_objective'])<=1e-8*max(1.,metrics['full_objective'])
                                row={**identity,'step':step,'edits':2*budget,'realized_fraction':2*budget/sum(x.number_of_edges() for x in old_graphs),
                                    'batch_counts':[{k:len(v) for k,v in b.items()} for b in [gb,hb]],'cumulative_edits':step*2*budget,
                                    'observation_mask_size':len(observation_mask(ng,nh,truth)),
                                    'generation_time':generation_time,'validation_time':validation_time,'timing_order':order,
                                    'method':m,'timings':timing,'initialization_time':init,'cumulative_update_time':cumulative[m],
                                    'initialization_plus_updates':init+cumulative[m],
                                    'initial_mapping_churn':float(np.mean(mapping!=initial_mapping)),
                                    'quality':quality(ng,nh,mapping,truth),'optimality_certificate':certs.get(m,{}),**metrics}
                                output.write(json.dumps(row)+'\n')
                            output.flush()
                            old_graphs=new_graphs
                        print(f'noise={noise}, seed={seed}, fraction={fraction}, protocol={protocol}: ten steps complete',flush=True)
    Path('results/raw/e09_initialization.json').write_text(json.dumps(initial_records,indent=2))
    sources=sorted(Path('src').glob('*.py'))+[Path(__file__),Path('experiments/e06_dynamic_assignment.py')]
    Path('results/raw/e09_streams.metadata.json').write_text(json.dumps(dict(config=config,config_hash=digest(config_path),
        source_hashes={str(p):digest(p) for p in sources},python=platform.python_version(),platform=platform.platform(),
        cpu_count=os.cpu_count(),numpy=np.__version__,scipy=scipy.__version__,
        scope='persistent updated-graphs-to-assignment, method-specific initialization, validation and generation excluded'),indent=2))


if __name__=='__main__':run()
