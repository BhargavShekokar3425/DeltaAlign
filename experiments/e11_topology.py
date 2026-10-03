"""Persistent exact cost-maintenance comparison; historical kernels are frozen."""
import json
import platform
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from src.topology_pairs import topology_pair, statistics
from src.descriptors import descriptors
from src.descriptor_cache import initialize, update
from src.normalization import initial_scale
from src.candidates import refresh_costs
from src.cost_cache import CostCache
from src.dynamic_assignment import solve, repair, certificate
from src.update_protocols import paired_updates, observation_mask
from src.metrics import quality
from src.repair_metrics import fidelity
from experiments.e06_dynamic_assignment import digest


from experiments.e10_costs import setup, advance

def run():
    config_path=Path('configs/e11_topology.json')
    config=json.loads(config_path.read_text())
    methods=['full_scipy','selective_scipy','persistent_scipy']
    initial_records=[]
    controls=[]
    no_update=[]
    with Path('results/raw/e11_topology.jsonl').open('w') as output:
        for family in config['families']:
            for noise in config['noise_levels']:
                for seed in config['seeds']:
                    g,h,truth,bundle=topology_pair(config['nodes'],seed,noise,family)
                    diagnostic=setup([g,h],'full_scipy')
                    random_mapping=np.random.default_rng(np.random.SeedSequence([bundle[1],99])).permutation(config['nodes'])
                    features=diagnostic['features']
                    costs=diagnostic['costs']
                    minima=costs.min(axis=1)
                    controls.append(dict(family=family,noise=noise,seed=seed,generation_seeds=bundle,
                        graph_statistics=[statistics(g),statistics(h)],full_quality=quality(g,h,diagnostic['mapping'],truth),
                        random_quality=quality(g,h,random_mapping,truth),initial_objective=float(costs[np.arange(config['nodes']),diagnostic['mapping']].sum()),
                        feature_unique_fractions=[len(np.unique(f,axis=0))/len(f) for f in features],
                        row_minimum_tie_fraction=float(np.mean(np.sum(costs==minima[:,None],axis=1)>1)),
                        truth_row_minimum_fraction=float(np.mean(costs[np.arange(config['nodes']),truth]==minima))))
                    del diagnostic,features,costs
                    for fraction in config['update_fractions']:
                        budget=max(1,int(fraction*(g.number_of_edges()+h.number_of_edges())/2+.5))
                        for protocol in config['protocols']:
                            identity=dict(family=family,seed=seed,noise=noise,requested_fraction=fraction,protocol=protocol)
                            contexts={m:setup([g,h],m) for m in methods}
                            reference=contexts['full_scipy']
                            initial_mapping=reference['mapping'].copy()
                            for method,c in contexts.items():
                                old_features=[x.copy() for x in c['features']]
                                old_costs=c['costs'].copy();old_mapping=c['mapping'].copy();old_scale=c['scale'].copy()
                                _,no_update_timings=advance(c,[g,h],[g,h],[{'inserted':[],'deleted':[]},{'inserted':[],'deleted':[]}],method)
                                np.testing.assert_array_equal(c['costs'],old_costs)
                                np.testing.assert_array_equal(c['mapping'],old_mapping)
                                np.testing.assert_array_equal(c['scale'],old_scale)
                                for new,old in zip(c['features'],old_features):np.testing.assert_array_equal(new,old)
                                if method=='persistent_scipy':
                                    np.testing.assert_array_equal(c['cost_cache'].source,old_features[0]/old_scale)
                                    np.testing.assert_array_equal(c['cost_cache'].target,old_features[1]/old_scale)
                                no_update.append({**identity,'method':method,'passed':True,'timings':no_update_timings})
                                np.testing.assert_array_equal(c['costs'],reference['costs'])
                                np.testing.assert_array_equal(c['scale'],reference['scale'])
                                initial_objective=float(c['costs'][np.arange(config['nodes']),c['mapping']].sum())
                                expected=float(reference['costs'][np.arange(config['nodes']),initial_mapping].sum())
                                np.testing.assert_allclose(initial_objective,expected,rtol=1e-10,atol=1e-8)
                                if method=='selective_dynamic':certificate(c['state'],config['certificate_tolerance'])
                                initial_records.append({**identity,'method':method,'initialization_time':c['initialization_time'],
                                    'timings':c['initialization_stages'],'cache_bytes':sum(x.nbytes for x in c['caches']) if c['caches'] else 0,
                                    'normalized_feature_bytes':c['cost_cache'].normalized_feature_bytes if c['cost_cache'] else 0,
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
                                order=['full_scipy']+(['persistent_scipy','selective_scipy'] if step%2 else ['selective_scipy','persistent_scipy'])
                                outputs={m:advance(contexts[m],old_graphs,new_graphs,[gb,hb],m) for m in order}
                                validation_start=perf_counter()
                                certs={}
                                full=reference['mapping']
                                full_costs=reference['costs']
                                for m in ['selective_scipy','persistent_scipy']:
                                    for actual,expected,old,dirty in zip(contexts[m]['features'],reference['features'],previous_features,outputs[m][0]):
                                        np.testing.assert_array_equal(actual,expected)
                                        assert dirty==set(np.flatnonzero(np.any(expected!=old,axis=1)))
                                    np.testing.assert_array_equal(contexts[m]['costs'],full_costs)
                                np.testing.assert_array_equal(contexts['selective_scipy']['mapping'],full)
                                np.testing.assert_array_equal(contexts['persistent_scipy']['mapping'],full)
                                normalized=contexts['persistent_scipy']['cost_cache']
                                np.testing.assert_array_equal(normalized.source,reference['features'][0]/reference['scale'])
                                np.testing.assert_array_equal(normalized.target,reference['features'][1]/reference['scale'])
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
                            print(f'family={family}, noise={noise}, seed={seed}, fraction={fraction}, protocol={protocol}: ten steps complete',flush=True)
    Path('results/raw/e11_initialization.json').write_text(json.dumps(initial_records,indent=2))
    Path('results/raw/e11_initial_controls.json').write_text(json.dumps(controls,indent=2))
    Path('results/raw/e11_no_update_controls.json').write_text(json.dumps(no_update,indent=2))
    sources=sorted(Path('src').glob('*.py'))+[Path(__file__),Path('experiments/e06_dynamic_assignment.py'),Path('experiments/e10_costs.py')]
    Path('results/raw/e11_topology.metadata.json').write_text(json.dumps(dict(config=config,config_hash=digest(config_path),
        source_hashes={str(p):digest(p) for p in sources},python=platform.python_version(),platform=platform.platform(),
        cpu_count=os.cpu_count(),numpy=np.__version__,scipy=scipy.__version__,
        scope='persistent updated-graphs-to-assignment, method-specific initialization, validation and generation excluded'),indent=2))


if __name__=='__main__':run()
