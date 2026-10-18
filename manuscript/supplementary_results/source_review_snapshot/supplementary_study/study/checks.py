import math
import numpy as np
from numba import njit
from scipy.optimize import root as root_solver
from scipy.special import expit
from .model import A,C,U,ALPHA,LAM,theory
from .kernels import production_round,stream_key,random_key
from .data import save_json,partition,sparse_logistic
from .engine import load_data,write_csv


@njit(cache=True)
def shifted_paths(key,rounds):
    N=32; H=4; gamma=1/128
    shifts=np.empty((N,2))
    for c in range(N): shifts[c]=U if c<N//2 else -U
    x=np.zeros(2); xh=x.copy(); controls=np.zeros((N,2)); ch=controls.copy()
    paths=np.empty((rounds,2,2)); res=np.empty(rounds)
    chol=np.linalg.cholesky(C)
    for t in range(rounds):
        eps=np.empty((H,N,2))
        for h in range(H):
            for c in range(N):
                z=np.empty(2)
                for j in range(2): z[j]=1. if random_key(key,t,h,c*2+j)&np.uint64(1) else -1.
                eps[h,c]=chol@z
        x,controls,_,_=production_round(x,controls,gamma,eps,True,np.zeros((N,2)),A,ALPHA,U)
        xh,ch,_,_=production_round(xh,ch,gamma,eps,True,shifts,A,ALPHA,U)
        paths[t,0]=x; paths[t,1]=xh
        res[t]=np.sqrt(np.dot(x-xh,x-xh))
    return paths,res


def zero_initialization(out):
    tau=int(np.ceil(1/(theory(4)["mu"]*(1/128)*4)))
    burn=50*tau; length=10*tau; rounds=burn+64*length
    rows=[]
    for seed in range(10001,10005):
        path,res=shifted_paths(stream_key("E2zero",0,seed,"N32_H4_rho1"),rounds)
        batch=path[burn:].reshape(64,length,2,2).mean(1)
        np.savez_compressed(out/f"diagnostics/E2_zero_seed{seed}.npz",batch_means=batch,global_residual_path=res,
                            snapshots=path[::length],tail_mean=path[burn:].mean(0),burn=burn,batch_length=length)
        row=dict(seed=seed,rounds=rounds,burn=burn,batches=64,batch_length=length,
            max_transient_difference=float(res[:burn].max()),max_tail_path_difference=float(res[burn:].max()),
            tail_mean_diff0=float((path[burn:,1]-path[burn:,0]).mean(0)[0]),tail_mean_diff1=float((path[burn:,1]-path[burn:,0]).mean(0)[1]))
        rows.append(row);print("E2 ZERO",row,flush=True)
    write_csv(out/"tables/E2_zero_initialization.csv",rows)


def deterministic_baselines(out):
    Z,y,ref=load_data(out); xref=ref["x_ref"]; rows=[]
    base=float(ref["gamma_base"])
    for regime in ("R1","R2"):
        members=partition(y,32,regime,4101)
        local=[(Z[r].tocsr(),y[r]) for r in members]
        local_ref_grads=np.array([sparse_logistic(z,yy,xref)[1] for z,yy in local])
        xi=-local_ref_grads+local_ref_grads.mean(0)
        for H,gamma in ((4,base),(4,base/2),(4,base/4),(2,base)):
            def fmap(x,jac=False,controls=None):
                endpoints=[]; Js=[]
                for c,(z,yy) in enumerate(local):
                    theta=x.copy(); J=np.eye(124)
                    for h in range(H):
                        if jac:
                            _,g,A=sparse_logistic(z,yy,theta)
                            J=(np.eye(124)-gamma*A)@J
                        else:
                            pp=expit(z@theta)
                            g=np.asarray(z.T@(pp-yy)).ravel()/len(yy)+LAM*theta
                        if controls is not None: g+=controls[c]
                        theta-=gamma*g
                    endpoints.append(theta)
                    if jac: Js.append(J)
                mean=np.mean(endpoints,0)
                return (mean,np.mean(Js,0)) if jac else (mean,np.array(endpoints))
            history=[]
            def fun(v):
                xn,J=fmap(v,True)
                history.append(float(np.linalg.norm(xn-v)))
                return xn-v,J-np.eye(124)
            result=root_solver(fun,xref,jac=True,method="hybr",options=dict(xtol=1e-10))
            xfa=result.x
            mapped,J=fmap(xfa,True)
            residual=float(np.linalg.norm(mapped-xfa)); radius=float(max(abs(np.linalg.eigvals(J))))
            # Independent perturbed start cross-checks the root and local attraction.
            second=root_solver(fun,xref+np.ones(124)*.001,jac=True,method="hybr",options=dict(xtol=1e-10))
            xs,ends=fmap(xref,False,xi)
            scaf_res=float(np.linalg.norm(xs-xref))
            control_res=float(np.linalg.norm((ends-xs)/(gamma*H)))
            filename=f"deterministic_{regime}_H{H}_g{gamma:.12g}"
            np.savez_compressed(out/"diagnostics"/(filename+".npz"),scaffold_fixed_point=xref,scaffold_controls=xi,
                                fedavg_fixed_point=xfa,fedavg_round_jacobian=J,solver_residual_history=history)
            row=dict(regime=regime,N=32,H=H,gamma=gamma,scaffold_fixedpoint_residual=scaf_res,
                     scaffold_control_refresh_residual=control_res,fedavg_fixedpoint_residual=residual,
                     fedavg_local_spectral_radius=radius,fedavg_parameter_displacement=float(np.linalg.norm(xfa-xref)),
                     independent_root_distance=float(np.linalg.norm(second.x-xfa)),solver_status=str(result.message),
                     scope="local fixed point and local attraction for FedAvg; SCAFFOLD exact consistency point; no global convergence certificate")
            rows.append(row); print("DETERMINISTIC",row,flush=True)
    write_csv(out/"tables/deterministic_baselines.csv",rows)
