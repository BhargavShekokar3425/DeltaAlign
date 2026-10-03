"""Repeated executions of frozen E13 jobs; no numerical kernel changes."""
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import scipy
import networkx as nx
from experiments.e13_scaling import headroom
from experiments.e06_dynamic_assignment import digest


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def validate(record, reference):
    assert len(record['records'])==len(reference['records'])==4
    for actual,expected in zip(record['records'],reference['records']):
        assert actual['step']==expected['step']
        assert actual['hashes']==expected['hashes'] and actual['objective']==expected['objective']


def run():
    config_path=Path('configs/e16_timing.json');config=json.loads(config_path.read_text())
    frozen_path=Path(config['fixed_job_source']);frozen=json.loads(frozen_path.read_text())
    for key in ['noise','requested_fraction','steps','methods']:assert config[key]==frozen[key],key
    assert set(config['seeds'])<=set(frozen['seeds'])
    assert set(config['sizes'])<=set(frozen['sizes']) and set(config['families'])<=set(frozen['families'])
    historical_path=Path('results/raw/e13_scaling.jsonl')
    historical=[json.loads(line) for line in historical_path.read_text().splitlines()]
    reference={(r['nodes'],r['family'],r['seed'],r['method']):r for r in historical}
    historical_metadata=Path('results/raw/e13_scaling.metadata.json')
    for path,expected in json.loads(historical_metadata.read_text())['source_hashes'].items():assert digest(Path(path))==expected,path
    sources=sorted(Path('src').glob('*.py'))+[Path(__file__),Path('experiments/e13_scaling.py'),Path('experiments/e12_resources.py'),Path('experiments/e10_costs.py'),Path('experiments/e06_dynamic_assignment.py')]
    hashes={str(p):digest(p) for p in sources}
    cpu=[line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')]
    metadata=dict(execution_status='running',started_at=timestamp(),config=config,config_hash=digest(config_path),frozen_config_hash=digest(frozen_path),reference_hash=digest(historical_path),reference_metadata_hash=digest(historical_metadata),source_hashes=hashes,preflight=[],python=platform.python_version(),platform=platform.platform(),cpu_count=os.cpu_count(),cpu_model=cpu[0] if cpu else None,numpy=np.__version__,scipy=scipy.__version__,networkx=nx.__version__,thread_environment={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']},rss_scope='whole fresh E13 worker including imports, generation, setup, updates, fingerprints and quality',timing_scope='graph-to-assignment stages excluding generation and validation; actual initialization included in totals',caveat='only visible resource limits inspected; no fixed-job repetitions pooled as graph seeds')
    metadata_path=Path('results/raw/e16_timing.metadata.json')
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    count=0
    with Path('results/raw/e16_timing.jsonl').open('w') as stream:
        for round_index in range(config['rounds']):
            for n in config['sizes']:
                memory=headroom();estimate=4*n*n*8+256*1024**2
                gate=dict(round=round_index+1,nodes=n,memory=memory,conservative_estimate_bytes=estimate,permitted=estimate<=memory['effective_available_bytes']/2)
                metadata['preflight'].append(gate);metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
                if not gate['permitted']:raise RuntimeError('Resource gate failed; comparison stopped')
                for family_index,family in enumerate(config['families']):
                    for seed_index,seed in enumerate(config['seeds']):
                        order=list(config['methods'])
                        if (family_index+seed_index+round_index)%2:order.reverse()
                        pair=[]
                        for position,method in enumerate(order):
                            command=[sys.executable,'-m','experiments.e13_scaling','--worker','--nodes',str(n),'--family',family,'--method',method,'--seed',str(seed)]
                            started=timestamp();child=subprocess.run(command,capture_output=True,text=True,check=True);ended=timestamp()
                            result=json.loads(child.stdout)
                            validate(result,reference[n,family,seed,method])
                            result.update(round=round_index+1,order=order,position=position,started_at=started,ended_at=ended)
                            stream.write(json.dumps(result)+'\n');stream.flush();pair.append(result);count+=1
                            print(f'{count}/60, round {round_index+1}, {family}, seed {seed}, {method}: total={result["total_time"]:.3f}s, RSS={result["peak_rss_bytes"]/1024**2:.1f} MiB; E13 fingerprints exact',flush=True)
                        validate(pair[0],pair[1])
    for path,expected in hashes.items():assert digest(Path(path))==expected,path
    assert digest(config_path)==metadata['config_hash'] and digest(frozen_path)==metadata['frozen_config_hash']
    metadata.update(execution_status='completed',ended_at=timestamp(),worker_runs=count,paired_executions=count//2,matching_snapshots=count//2*4)
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__':run()
