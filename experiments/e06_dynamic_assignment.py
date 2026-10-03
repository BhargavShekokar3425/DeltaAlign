import hashlib
import json
import os
import platform
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from src.graph import graph_pair
from src.descriptors import descriptors
from src.normalization import initial_scale
from src.update_protocols import paired_updates, observation_mask
from src.candidates import refresh_costs
from src.dynamic_assignment import solve, repair, certificate
from src.metrics import quality
from src.repair_metrics import fidelity


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    config_path=Path('configs/e06_dynamic_assignment.json')
    config=json.loads(config_path.read_text())
    n,mode=config['nodes'],config['descriptor_mode']
    initial_records=[]
    with Path('results/raw/e06_dynamic_assignment.jsonl').open('w') as stream:
        for noise in config['noise_levels']:
            for seed in config['seeds']:
                g,h,truth,bundle=graph_pair(n,config['attachment'],seed,noise)
                start=perf_counter()
                fg,fh=descriptors(g,mode),descriptors(h,mode)
                scale=initial_scale(fg,fh)
                old_costs=cdist(fg/scale,fh/scale,'sqeuclidean')
                initial_cost_time=perf_counter()-start
                start=perf_counter()
                initial_state,initial_stats=solve(old_costs)
                initial_solve_time=perf_counter()-start
                initial_cert=certificate(initial_state,config['certificate_tolerance'])
                r,c=linear_sum_assignment(old_costs)
                np.testing.assert_allclose(old_costs[r,c].sum(),old_costs[np.arange(n),initial_state.mapping].sum(),rtol=1e-10,atol=1e-8)
                old=initial_state.mapping.copy()
                initial_records.append({'seed':seed,'noise':noise,'initial_cost_time':initial_cost_time,
                    'initial_solver_time':initial_solve_time,'initial_stats':initial_stats,
                    'initial_mapping_agreement_with_scipy':float(np.mean(old==c)),
                    'initial_quality':quality(g,h,old,truth),**initial_cert})
                for fraction in config['update_fractions']:
                    b=max(1,int(fraction*(g.number_of_edges()+h.number_of_edges())/2+.5))
                    for protocol in config['protocols']:
                        target_seed=int(np.random.SeedSequence(bundle[3]).generate_state(1)[0])
                        ng,nh,gb,hb=paired_updates(g,h,truth,b,bundle[3],target_seed,protocol)
                        if protocol=='shared_latent':
                            assert observation_mask(g,h,truth)==observation_mask(ng,nh,truth)
                        # Actual full pipeline: full features, all costs, compiled solve.
                        start=perf_counter()
                        full_fg,full_fh=descriptors(ng,mode),descriptors(nh,mode)
                        full_feature_time=perf_counter()-start
                        cost_start=perf_counter()
                        full_costs=cdist(full_fg/scale,full_fh/scale,'sqeuclidean')
                        full_cost_time=perf_counter()-cost_start
                        solve_start=perf_counter()
                        rows,cols=linear_sum_assignment(full_costs)
                        scipy_solver_time=perf_counter()-solve_start
                        full_pipeline_time=perf_counter()-start
                        full=np.empty(n,dtype=int); full[rows]=cols
                        # Actual dynamic pipeline: count full-feature oracle and all copies.
                        start=perf_counter()
                        copy_start=perf_counter()
                        state=initial_state.copy()
                        clone_time=perf_counter()-copy_start
                        feature_start=perf_counter()
                        new_fg,new_fh=descriptors(ng,mode),descriptors(nh,mode)
                        dynamic_feature_time=perf_counter()-feature_start
                        dirty_start=perf_counter()
                        changed_rows=set(np.flatnonzero(np.any(new_fg!=fg,axis=1)).tolist())
                        changed_columns=set(np.flatnonzero(np.any(new_fh!=fh,axis=1)).tolist())
                        dirty_time=perf_counter()-dirty_start
                        cost_start=perf_counter()
                        costs,rescored=refresh_costs(old_costs,new_fg,new_fh,changed_rows,changed_columns,scale)
                        dynamic_cost_time=perf_counter()-cost_start
                        solve_start=perf_counter()
                        state,dynamic_stats=repair(state,costs,changed_rows,changed_columns)
                        dynamic_solver_time=perf_counter()-solve_start
                        dynamic_pipeline_time=perf_counter()-start
                        validation_start=perf_counter()
                        np.testing.assert_array_equal(costs,full_costs)
                        dynamic_cert=certificate(state,config['certificate_tolerance'])
                        validation_time=perf_counter()-validation_start
                        cold_start=perf_counter()
                        cold_state,cold_stats=solve(full_costs)
                        cold_solver_time=perf_counter()-cold_start
                        cold_cert=certificate(cold_state,config['certificate_tolerance'])
                        full_quality=quality(ng,nh,full,truth)
                        common={'seed':seed,'noise':noise,'protocol':protocol,'requested_fraction':fraction,
                            'realized_fraction':2*b/(g.number_of_edges()+h.number_of_edges()),'edits':2*b,
                            'changed_rows':len(changed_rows),'changed_columns':len(changed_columns),
                            'rescored_cost_entries':rescored,'rescored_cost_fraction':rescored/(n*n),
                            'initial_quality':quality(g,h,old,truth),'full_quality':full_quality,
                            'initial_mapping_agreement_with_scipy':initial_records[-1]['initial_mapping_agreement_with_scipy'],
                            'full_feature_time':full_feature_time,'full_cost_time':full_cost_time,
                            'full_pipeline_time':full_pipeline_time,'scipy_solver_time':scipy_solver_time,
                            'dynamic_feature_time':dynamic_feature_time,'dynamic_dirty_time':dirty_time,
                            'dynamic_cost_time':dynamic_cost_time,'dynamic_clone_time':clone_time,
                            'dynamic_pipeline_time':dynamic_pipeline_time,'validation_time':validation_time,
                            'cold_solver_time':cold_solver_time,'dynamic_solver_time':dynamic_solver_time,
                            'same_kernel_solver_speedup':cold_solver_time/dynamic_solver_time,
                            'scipy_pipeline_speedup':full_pipeline_time/dynamic_pipeline_time,
                            'changed_full_mappings':int(np.sum(full!=old))}
                        methods=[('dynamic',state.mapping,dynamic_stats,dynamic_cert),
                            ('cold_hungarian',cold_state.mapping,cold_stats,cold_cert),
                            ('scipy_full',full,{},{}),('keep_old',old,{}, {})]
                        for name,mapping,stats,cert in methods:
                            quality_result=quality(ng,nh,mapping,truth)
                            row={**common,'method':name,'quality':quality_result,
                                'nc_difference_vs_keep_old':quality_result['nc']-common['initial_quality']['nc'],
                                'search_stats':stats,'optimality_certificate':cert,
                                **fidelity(costs,mapping,full,old)}
                            if name in ['dynamic','cold_hungarian']:
                                assert row['absolute_objective_gap'] <= 1e-8*max(1.,row['full_objective'])
                            stream.write(json.dumps(row)+'\n')
                        stream.flush()
                print(f'noise={noise}: finished seed {seed}',flush=True)
    Path('results/raw/e06_initialization.json').write_text(json.dumps(initial_records,indent=2))
    paths=sorted(Path('src').glob('*.py'))+[Path(__file__)]
    Path('results/raw/e06_dynamic_assignment.metadata.json').write_text(json.dumps({
        'config':config,'config_hash':digest(config_path),'source_hashes':{str(p):digest(p) for p in paths},
        'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count(),
        'numpy':np.__version__,'scipy':scipy.__version__,
        'provenance':'original primal-dual reference based on CMU-RI-TR-07-27 Figure 5 and batch extension',
        'scope':'actual updated-graphs-to-assignment pipeline; full feature oracle, dense caches; excludes generation, edge application and certificates'},indent=2))


if __name__=='__main__':
    run()
