import argparse, hashlib, json, math, os, platform, sys, time
from pathlib import Path
import numpy as np
from .model import operators,targets
from .kernels import trigonometric_chunk
ROOT=Path(__file__).resolve().parents[1]
CONDITIONS=[('rho_minus_symmetric',-.25,False),('rho_zero_symmetric',0.,False),('rho_plus_symmetric',.25,False),('rho_plus_asymmetric',.25,True)]
def save_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item()),encoding='utf8')
def key_for(phase,condition,N,gamma,seed):
    text=f'targeted-trigonometric-v1|{phase}|{condition}|{N}|{gamma.hex()}|{seed}'
    return np.uint64(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'little'))
def schedule(gamma):
    tau=math.ceil(1/(.6*4*gamma))
    return dict(tau=tau,burn=50*tau,batch_length=10*tau,batches=64)
def run_one(phase,condition,N,gamma,seed):
    name,rho,asym=condition; H=4; sc=schedule(gamma); ops=operators(gamma,H)
    folder=ROOT/'local'/phase/f'{name}_N{N}_g{round(1/gamma)}'/f'seed_{seed}'
    folder.mkdir(parents=True,exist_ok=True); result=folder/'result.npz'; checkpoint=folder/'checkpoint.npz'
    if result.exists(): return dict(np.load(result))
    if phase=='production':
        # Finish any active run. Reserve 10 CPU minutes for up to 8 in-flight
        # runs, well above the measured largest single-run forecast.
        used=0.
        for f in (ROOT/'local').glob('*/*/seed_*/result.npz'):
            with np.load(f) as saved: used+=float(saved['cpu'])
        if used+600>=21600:
            record=dict(status='RESOURCE_LIMITED',condition=name,N=N,gamma=gamma,seed=seed,completed_simulation_cpu_seconds=used)
            save_json(folder/'not_started.json',record)
            return record
    x=np.zeros((2,2)); c=np.zeros((N,2)); t=0; rows=[]; cpu=0.; wall=0.; burn_done=False
    if checkpoint.exists():
        with np.load(checkpoint) as p:
            x=p['x']; c=p['controls']; t=int(p['t']); rows=list(p['rows']); cpu=float(p['cpu']); wall=float(p['wall']); burn_done=bool(p['burn_done'])
    k=key_for(phase,name,N,gamma,seed)
    chunks=([sc['burn']] if not burn_done else [])+[sc['batch_length']]*(sc['batches']-len(rows))
    for count in chunks:
        start=x.copy(); tc=time.process_time(); tw=time.perf_counter()
        x,c,raw,bal,eta,res,cm=trigonometric_chunk(x,c,k,t,count,N,H,gamma,*ops,rho,asym)
        elapsed_cpu=time.process_time()-tc; elapsed_wall=time.perf_counter()-tw
        cpu+=elapsed_cpu; wall+=elapsed_wall; t+=count
        if burn_done:
            # fixed 2x2 arrays flattened: endpoints, means, recursion, control, maxima.
            row=np.concatenate([start.ravel(),x.ravel(),raw.mean(0).ravel(),bal.mean(0).ravel(),eta.mean(0),res.mean(0).ravel(),cm.mean(0),[np.max(abs(res)),np.max(abs(cm)),count]])
            rows.append(row)
        burn_done=True
        with open(folder/'checkpoint.tmp','wb') as f:
            np.savez(f,x=x,controls=c,t=t,rows=np.array(rows),cpu=cpu,wall=wall,burn_done=burn_done)
        os.replace(folder/'checkpoint.tmp',checkpoint)
        if not np.isfinite(x).all() or not np.isfinite(c).all(): raise FloatingPointError(str(folder))
    out=dict(x=x,controls=c,t=t,rows=np.array(rows),cpu=cpu,wall=wall,seed=seed,key=k,N=N,gamma=gamma,rho=rho,asymmetric=asym,batch_length=sc['batch_length'])
    np.savez_compressed(result,**out)
    print(json.dumps(dict(phase=phase,condition=name,N=N,gamma=gamma,seed=seed,cpu_seconds=cpu,rounds=t)),flush=True)
    return out
def warmup():
    g=1/1024
    trigonometric_chunk(np.zeros((2,2)),np.zeros((64,2)),np.uint64(1),0,10,64,4,g,*operators(g),0.,False)
def operators(gamma,H=4):
    from .model import operators as op
    return op(gamma,H)
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['test','pilot','benchmark','production']); parser.add_argument('--jobs',type=int,default=1); args=parser.parse_args()
    if args.command=='test':
        import pytest
        raise SystemExit(pytest.main([str(ROOT/'targeted/tests.py'),'-v','--tb=short','-o','addopts=','-p','no:cacheprovider','--basetemp',str(ROOT/'local/pytest_new')]))
    warmup()
    if args.command=='benchmark':
        g=1/1024; t=time.process_time()
        trigonometric_chunk(np.zeros((2,2)),np.zeros((64,2)),np.uint64(2),0,2000,64,4,g,*operators(g),.25,False)
        print('CPU seconds / 2000 rounds:',time.process_time()-t,flush=True); return
    if args.command=='pilot':
        save_json(ROOT/'PILOT_DESIGN.json',dict(conditions=CONDITIONS,N=64,gamma=1/1024,seeds=list(range(100101,100105)),schedule=schedule(1/1024),purpose='Performance, precision, autocorrelation, implementation; not hypothesis selection',cross_condition_coupling='independent indexed streams; algorithms paired within run'))
        tasks=[('pilot',c,64,1/1024,s) for c in CONDITIONS for s in range(100101,100105)]
        dispatch(tasks,args.jobs)
    if args.command=='production':
        p=json.loads((ROOT/'PROTOCOL_FROZEN.json').read_text())
        if not p['production_authorized_by_cost_gate']: raise RuntimeError('RESOURCE_LIMITED: production not authorized')
        for rel,expected in p['simulation_source_hashes'].items():
            if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected: raise RuntimeError('Frozen simulation source modified: '+rel)
        tasks=[]
        for c in p['cells']:
            condition=next(v for v in CONDITIONS if v[0]==c['condition'])
            for seed in p['production_seeds']: tasks.append(('production',condition,c['N'],c['gamma'],seed))
        dispatch(tasks,args.jobs)

def dispatch(tasks,jobs):
    if jobs==1:
        for task in tasks: run_one(*task)
    else:
        from concurrent.futures import ProcessPoolExecutor,as_completed
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures={pool.submit(run_one,*task):task for task in tasks}
            for f in as_completed(futures):
                try: f.result()
                except BaseException as e:
                    save_json(ROOT/'local'/'failure.json',dict(task=futures[f],error=repr(e)))
                    raise
