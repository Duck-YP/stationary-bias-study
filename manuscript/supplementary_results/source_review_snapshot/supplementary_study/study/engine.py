import csv
import json
import time
from pathlib import Path
import numpy as np
from scipy import sparse
from .data import save_json, partition, partition_diagnostics, sparse_logistic
from .model import A,C,U,ALPHA,theory
from .kernels import controlled_chunk,logistic_chunk,production_round,random_key,stream_key
from .tests import controlled_args

ALGORITHMS=("scaffold","fedavg")


def cell_id(family,H,N,gamma,regime="",partition_seed=0):
    return f"{family}_{regime or 'controlled'}_p{partition_seed}_H{H}_N{N}_g{gamma:.12g}"


def cells(gamma_base):
    design={}
    def add(family,H,N,gamma,role,regime="",partition_seed=0):
        id=cell_id(family,H,N,gamma,regime,partition_seed)
        if id in design:
            design[id]["roles"].append(role); return
        design[id]=dict(id=id,family=family,H=H,N=N,gamma=gamma,regime=regime,partition_seed=partition_seed,
                        m=256//N if family=="E3" else 1,roles=[role])
    for H in (1,2,4,8):
        for gamma in (1/64,1/128,1/256,1/512): add("E1",H,32,gamma,"E1a")
    for H in (2,4,8):
        for N in (32,64,128):
            for gamma in (1/128,1/256,1/512): add("E1",H,N,gamma,"E1b")
    for regime in ("R0","R1","R2"):
        seed=0 if regime=="R0" else 4101
        for N in (8,32,128): add("E3",4,N,gamma_base,"allocation",regime,seed)
        for scale in (2,4): add("E3",4,32,gamma_base/scale,"policy",regime,seed)
        add("E3",2,32,gamma_base,"policy",regime,seed)
        for N in (8,32,128): add("E3",1,N,gamma_base,"negative_control",regime,seed)
        if regime!="R0":
            for seed in (4102,4103):
                for N in (8,128): add("E3",4,N,gamma_base,"partition_sensitivity",regime,seed)
    return list(design.values())


def load_data(out):
    Z=sparse.load_npz(out/"data/training_csr.npz")
    y=np.load(out/"data/membership.npz")["labels"]
    ref=dict(np.load(out/"reference_optimizers.npz"))
    return Z,y,ref


def run_one(cell,seed,phase,schedule,out,Z=None,y=None,ref=None,resume=False,deadline=float("inf"),max_memory_gb=4.):
    import psutil
    id=cell["id"]; directory=out/"raw"/phase/id/f"seed_{seed}"
    directory.mkdir(parents=True,exist_ok=True)
    checkpoint=directory/"checkpoint.npz"
    N,H,gamma=cell["N"],cell["H"],cell["gamma"]
    real=cell["family"]=="E3"; d=124 if real else 2
    if (directory/"result.npz").exists(): return True
    key=stream_key(cell["family"],cell["partition_seed"],seed,id)
    if real and cell["regime"]=="R0" and H==1:
        key=stream_key("E3",0,seed,"R0_h1_shared_mapping")
    burn=schedule["burn"]; batch_length=schedule["batch_length"]; batches=schedule["batches"]
    total=burn+batch_length*batches
    if resume and checkpoint.exists():
        state=dict(np.load(checkpoint))
        t=int(state["t"]); elapsed=float(state["elapsed"])
        assert int(state["key"])==int(key) and int(state["total"])==total
    else:
        if checkpoint.exists(): raise RuntimeError(f"Existing checkpoint requires --resume: {directory}")
        t=0; elapsed=0.
        state=dict(x=np.zeros((2,d)),controls=np.zeros((N,d)),raw_sum=np.zeros((2,d)),raw_sumsq=np.zeros(2),
            primary_sum=np.zeros((2,d)),batch_sum=np.zeros((batches,2,d)),batch_raw_sum=np.zeros((batches,2,d)),
            batch_count=np.zeros(batches,dtype=np.int64),batch_sumsq=np.zeros((batches,2)),
            batch_ctrl=np.zeros(batches),batch_ctrl_vector=np.zeros((batches,d)),batch_crossdiff=np.zeros((batches,2,d)),
            batch_control_sum=np.zeros((batches,N,d)),
            snapshot=np.zeros((batches,2,d)),max_zero_sum=np.array(0.),max_relative_zero_sum=np.array(0.),
            peak_memory=np.array(0.),key=np.array(key),total=np.array(total),diagnostic_full_gradients=np.array(0))
    if real:
        members=partition(y,N,cell["regime"],cell["partition_seed"])
        csr=(Z.indptr.astype(np.int64),Z.indices.astype(np.int64),Z.data,y)
        xref=ref["x_ref"]
    else:
        args=controlled_args(gamma,H); xref=np.zeros(2)
    start=time.perf_counter(); last_save=start
    def save():
        state["t"]=np.array(t); state["elapsed"]=np.array(elapsed+time.perf_counter()-start)
        temp=directory/"checkpoint.pending.npz"
        np.savez_compressed(temp,**state); temp.replace(checkpoint)
    while t<total:
        if time.monotonic()>=deadline:
            save(); return False
        memory=psutil.Process().memory_info().rss/1024**3
        state["peak_memory"]=np.array(max(memory,float(state["peak_memory"])))
        if memory>max_memory_gb:
            save(); return False
        if t<burn:
            count=min(2048,burn-t); batch=-1
        else:
            batch=(t-burn)//batch_length
            count=min(2048,burn+(batch+1)*batch_length-t)
        if real:
            x,control,raw,ctrl,res,controlsum=logistic_chunk(state["x"],state["controls"],key,t,count,H,gamma,cell["m"],members,*csr)
            primary=raw
        else:
            x,control,raw,primary,ctrl,res,controlsum=controlled_chunk(state["x"],state["controls"],key,t,count,N,H,gamma,*args)
        if not np.isfinite(raw).all():
            save(); save_json(directory/"failure.json",dict(reason="NUMERICAL_INSTABILITY",round=t)); return False
        state["x"]=x; state["controls"]=control
        state["max_zero_sum"]=np.array(max(float(state["max_zero_sum"]),float(res.max())))
        relative=float(res.max())/(1+np.linalg.norm(control))
        state["max_relative_zero_sum"]=np.array(max(float(state["max_relative_zero_sum"]),relative))
        if batch>=0:
            bs=raw.sum(0); ps=primary.sum(0); ss=np.sum((raw-xref)**2,axis=(0,2))
            state["raw_sum"]+=bs; state["primary_sum"]+=ps; state["raw_sumsq"]+=ss
            state["batch_sum"][batch]+=ps; state["batch_raw_sum"][batch]+=bs
            state["batch_sumsq"][batch]+=ss; state["batch_count"][batch]+=count
            state["batch_ctrl"][batch]+=ctrl.sum(); state["batch_ctrl_vector"][batch]+=count*control.mean(0)
            state["batch_control_sum"][batch]+=controlsum
            state["snapshot"][batch]=raw[-1]
            state["batch_crossdiff"][batch]+=(raw-primary).sum(0)
        t+=count
        if time.perf_counter()-last_save>=30:
            save(); last_save=time.perf_counter()
    save()
    primary_batches=schedule.get("primary_batches",batches)
    samples=int(state["batch_count"][:primary_batches].sum())
    result={name:val for name,val in state.items()}
    result.update(raw_mean=state["batch_raw_sum"][:primary_batches].sum(0)/samples,mean=state["batch_sum"][:primary_batches].sum(0)/samples,
                  second_moment=state["batch_sumsq"][:primary_batches].sum(0)/samples,
                  batch_means=state["batch_sum"]/state["batch_count"][:,None,None],
                  batch_raw_means=state["batch_raw_sum"]/state["batch_count"][:,None,None],
                  samples=np.array(samples),seed=np.array(seed),rounds=np.array(total),
                  primary_batches=np.array(primary_batches),
                  control_mean=state["batch_control_sum"][:primary_batches].sum(0)/samples,
                  control_second_moment=np.array(state["batch_ctrl"][:primary_batches].sum()/samples),
                  sample_gradient_evaluations=np.array(2*N*cell["m"]*H*total),
                  communication_parameter_scalars=np.array(2*N*d*total),
                  communication_control_scalars=np.array(N*d*total))
    np.savez_compressed(directory/"result.npz",**result)
    save_json(directory/"run.json",dict(cell=cell,seed=seed,phase=phase,schedule=schedule,
        estimator="direct mean" if real else "exact nonlinear stationary balance; direct cross-check retained",
        rng="SHA256-keyed SplitMix64 indexed by round/local-step/client/sample-slot; paired branches reuse keys",
        zero_sum_projection=False,elapsed_seconds=float(result["elapsed"])))
    return True


def e2(out):
    rows=[]
    for N in (8,32):
        for H in (2,4,8):
            for rho in (0.,.25,.5,1.):
                gamma=1/128; shifts=np.tile(rho*U,(N,1)); shifts[N//2:]*=-1
                x=np.zeros(2); controls=np.zeros((N,2)); xh=x.copy(); ch=-shifts.copy()
                key=stream_key("E2",0,10001,f"{N}_{H}_{rho}")
                residuals=[]
                for t in range(2000):
                    z=np.array([[[1. if random_key(key,t,h,c*2+j)&np.uint64(1) else -1. for j in range(2)] for c in range(N)] for h in range(H)])
                    eps=z@np.linalg.cholesky(C).T
                    x,controls,local,_=production_round(x,controls,gamma,eps,True,np.zeros((N,2)),A,ALPHA,U)
                    xh,ch,localh,_=production_round(xh,ch,gamma,eps,True,shifts,A,ALPHA,U)
                    residuals.append([t+1,float(np.max(abs(x-xh))),float(np.max(abs(local-localh))),float(np.max(abs(controls-(ch+shifts)))),float(np.linalg.norm(ch.sum(0)))])
                arr=np.array(residuals)
                np.savez_compressed(out/f"diagnostics/E2_N{N}_H{H}_rho{rho}.npz",residuals=arr,shifts=shifts,gradient_at_global_optimum=shifts)
                row=dict(N=N,H=H,rho=rho,rounds=2000,max_global_residual=float(arr[:,1].max()),max_local_residual=float(arr[:,2].max()),max_control_residual=float(arr[:,3].max()),max_zero_sum=float(arr[:,4].max()),gradient_heterogeneity=rho**2)
                assert max(row["max_global_residual"],row["max_local_residual"],row["max_control_residual"])<1e-10
                rows.append(row)
                print("E2",N,H,rho,row["max_control_residual"],flush=True)
    write_csv(out/"tables/E2_exact_checks.csv",rows)
    save_json(out/"diagnostics/E2_gate.json",dict(status="PASSED",cells=len(rows),scope="bounded affine objective shifts; corresponding initial controls; not different Hessians"))


def write_csv(path,rows,fields=None):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
