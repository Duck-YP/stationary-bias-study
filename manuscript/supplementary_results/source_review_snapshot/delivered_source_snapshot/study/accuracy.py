"""Post-freeze roundoff audit. This kernel does not replace v1 formal evidence."""
import math
import time
import numpy as np
from numba import njit
from .kernels import random_key,stream_key,logistic_chunk
from .data import partition,save_json
from .engine import load_data,write_csv


@njit(cache=True)
def stable_logistic_chunk(x,controls,key,start,count,H,gamma,m,members,indptr,indices,values,labels):
    N,d=controls.shape
    raw=np.empty((count,2,d))
    maximum=0.
    for t in range(count):
        delta=np.zeros((2,N,d))
        for h in range(H):
            for c in range(N):
                g=np.zeros((2,d))
                for s in range(m):
                    row=members[c,int(random_key(key,start+t,h,c*m+s)%np.uint64(members.shape[1]))]
                    for a in range(2):
                        z=0.
                        for j in range(indptr[row],indptr[row+1]):
                            k=indices[j]
                            z+=values[j]*(x[a,k]+delta[a,c,k])
                        if z>=0:p=1/(1+math.exp(-z))
                        else:
                            e=math.exp(z);p=e/(1+e)
                        for j in range(indptr[row],indptr[row+1]):
                            g[a,indices[j]]+=(p-labels[row])/m*values[j]
                for j in range(d):
                    delta[0,c,j]-=gamma*(g[0,j]+.01*(x[0,j]+delta[0,c,j])+controls[c,j])
                    delta[1,c,j]-=gamma*(g[1,j]+.01*(x[1,j]+delta[1,c,j]))
        average=np.zeros((2,d))
        for c in range(N):
            average[0]+=delta[0,c]/N
            average[1]+=delta[1,c]/N
        for c in range(N):
            controls[c]+=(delta[0,c]-average[0])/(gamma*H)
        x+=average
        raw[t]=x
        total=np.zeros(d)
        for c in range(N):total+=controls[c]
        maximum=max(maximum,np.sqrt(np.dot(total,total)))
    return x,controls,raw,maximum


def roundoff_audit(out):
    Z,y,ref=load_data(out)
    csr=(Z.indptr.astype(np.int64),Z.indices.astype(np.int64),Z.data,y)
    # Worst observed R0 N=128 endpoint summation cases, declared as post-freeze numerical diagnostics.
    N=128;m=2;H=1;gamma=float(ref["gamma_base"])
    members=partition(y,N,"R0",0)
    id=f"E3_R0_p0_H1_N128_g{gamma:.12g}"
    rows=[]
    for seed in (20001,20011):
        key=stream_key("E3",0,seed,"R0_h1_shared_mapping")
        short=logistic_chunk(np.zeros((2,124)),np.zeros((N,124)),key,0,30,H,gamma,m,members,*csr)
        stable=stable_logistic_chunk(np.zeros((2,124)),np.zeros((N,124)),key,0,30,H,gamma,m,members,*csr)
        short_res=float(np.max(abs(short[2]-stable[2])))
        assert short_res<1e-10
        original=dict(np.load(out/"raw/production"/id/f"seed_{seed}/result.npz"))
        run=__import__('json').loads((out/"raw/production"/id/f"seed_{seed}/run.json").read_text())
        schedule=run["schedule"];burn=schedule["burn"];length=schedule["batch_length"];total=int(original["rounds"])
        x=np.zeros((2,124));controls=np.zeros((N,124));t=0;maximum=0.
        snapshots=[];batch_means=[];batchsum=np.zeros((2,124));start=time.perf_counter()
        while t<total:
            boundary=burn if t<burn else burn+(((t-burn)//length)+1)*length
            count=min(2048,boundary-t)
            x,controls,raw,res=stable_logistic_chunk(x,controls,key,t,count,H,gamma,m,members,*csr)
            maximum=max(maximum,res)
            if t>=burn:batchsum+=raw.sum(0)
            t+=count
            if t>burn and (t-burn)%length==0:
                snapshots.append(x.copy());batch_means.append(batchsum/length);batchsum[:]=0.
        snapshots=np.array(snapshots);batch_means=np.array(batch_means)
        residual=float(np.max(np.linalg.norm(snapshots[:,0]-snapshots[:,1],axis=1)))
        scale=1+float(np.max(np.linalg.norm(snapshots[:,1],axis=1)))
        numerical_shift=float(np.max(abs(batch_means.mean(0)-original["raw_mean"])))
        np.savez_compressed(out/f"diagnostics/stable_arithmetic_H1_seed{seed}.npz",snapshots=snapshots,batch_means=batch_means,
                            final_x=x,controls=controls,max_zero_sum=maximum,rounds=total)
        row=dict(cell_id=id,seed=seed,rounds=total,short_v1_stable_agreement=short_res,
            stable_max_global_identity_l2=residual,scaled_identity_residual=residual/scale,
            max_zero_sum=maximum,mean_parameter_change_from_frozen_v1=numerical_shift,
            passed_scale_aware_1e10=residual/scale<1e-10,elapsed_seconds=time.perf_counter()-start,
            scope="post-freeze numerical audit; same v1 indices/horizons; local endpoint increments averaged before adding x; no zero-sum projection; not v2 formal production")
        rows.append(row);print("ROUNDOFF AUDIT",row,flush=True)
    write_csv(out/"diagnostics/stable_arithmetic_roundoff_audit.csv",rows)
    save_json(out/"diagnostics/roundoff_resolution.json",dict(v1_formal_results_preserved=True,primary_fits_changed=False,
        stable_kernel_source="study/accuracy.py",stable_formal_production_executed=False,runs=rows,
        explanation="Averaging large endpoints and then subtracting their mean amplifies roundoff in control refresh. Averaging local increments gives the same exact-real recursion and reduces accumulated zero-sum error without projection.",
        limitation="Only two long representative H1 audits are run. No stable-arithmetic full-grid rerun or new frozen production protocol is claimed."))
