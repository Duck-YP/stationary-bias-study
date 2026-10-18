import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.special import expit
from scipy.optimize import minimize
from .model import LAM, logistic


def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def save_json(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item()),encoding="utf-8")


def read_libsvm(path, expected_rows):
    rows=[]; cols=[]; vals=[]; ys=[]; observed=set()
    for r,line in enumerate(Path(path).read_text(encoding="ascii").splitlines()):
        tokens=line.split()
        label=int(tokens[0]); assert label in (-1,1)
        ys.append((label+1)/2)
        seen=set()
        for feature in tokens[1:]:
            k,v=feature.split(":")
            k=int(k)-1
            assert 0<=k<123 and k not in seen
            seen.add(k); observed.add(k)
            rows.append(r); cols.append(k); vals.append(float(v))
    assert len(ys)==expected_rows
    Z=sparse.csr_matrix((vals,(rows,cols)),shape=(len(ys),123),dtype=np.float64)
    # Test file may omit feature 123; the common declared space is still 123.
    norms=np.sqrt(Z.multiply(Z).sum(axis=1)).A.ravel()
    Z=sparse.diags(1/np.maximum(1,norms)) @ Z
    Z=sparse.hstack([Z,np.ones((len(ys),1))],format="csr")
    Z.sort_indices()
    return Z,np.array(ys),dict(rows=len(ys),declared_features=123,observed_max_feature=max(observed)+1,
                               unique_features=len(observed),labels=[-1,1],parameters=124)


def sparse_logistic(Z,y,x):
    z=Z @ x
    p=expit(z)
    f=float(np.mean(np.logaddexp(0,z)-y*z)+LAM/2*(x@x))
    g=np.asarray(Z.T @ (p-y)).ravel()/len(y)+LAM*x
    H=(Z.T @ sparse.diags(p*(1-p)) @ Z).toarray()/len(y)+LAM*np.eye(Z.shape[1])
    return f,g,H


def prepare(root, out):
    root=Path(root); out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    Zall,yall,train_meta=read_libsvm(root/"data/a9a",32561)
    _,_,test_meta=read_libsvm(root/"data/a9a.t",16281)
    permutation=np.random.default_rng(20261009).permutation(len(yall))
    retained=permutation[:32512]; excluded=permutation[32512:]
    Z=Zall[retained].tocsr(); y=yall[retained]
    sparse.save_npz(out/"training_csr.npz",Z)
    np.savez_compressed(out/"membership.npz",retained_row_ids=retained,excluded_row_ids=excluded,labels=y)
    entries=[]
    for name,meta in [("a9a",train_meta),("a9a.t",test_meta)]:
        entries.append(dict(file=name,sha256=sha(root/"data"/name),
                            source_url="https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/"+name,
                            retrieved_date="2026-10-09",validation=meta))
    save_json(out/"DATA_MANIFEST.json",dict(files=entries,subset_seed=20261009,retained_count=len(y),
        excluded_count=len(excluded),row_id_origin="0-based original file row",preprocessing="row / max(1,l2 norm), then intercept=1; lambda=.01 on all 124 coordinates",
        processed_sha256=sha(out/"training_csr.npz"),membership_sha256=sha(out/"membership.npz")))
    history=[]; x=np.zeros(124)
    for iteration in range(50):
        f,g,H=sparse_logistic(Z,y,x)
        history.append(dict(iteration=iteration,objective=f,gradient_norm=float(np.linalg.norm(g))))
        if np.linalg.norm(g)<1e-14:
            break
        delta=np.linalg.solve(H,g)
        scale=1.
        while scale>1e-8:
            xn=x-scale*delta
            fn=sparse_logistic(Z,y,xn)[0]
            if fn<=f-1e-4*scale*(g@delta)+2e-16:
                break
            scale/=2
        x=xn
    f,g,H=sparse_logistic(Z,y,x)
    # A separate quasi-Newton path followed by Newton refinement cross-checks the solution.
    def fun(v):
        z=Z @ v
        return float(np.mean(np.logaddexp(0,z)-y*z)+LAM/2*(v@v)), np.asarray(Z.T @ (expit(z)-y)).ravel()/len(y)+LAM*v
    second=minimize(fun,np.full(124,.03),jac=True,method="L-BFGS-B",options=dict(gtol=1e-13,ftol=1e-15,maxiter=2000))
    x2=second.x.copy()
    for _ in range(4):
        _,g2,H2=sparse_logistic(Z,y,x2)
        x2-=np.linalg.solve(H2,g2)
    p=expit(Z @ x)
    E=Z.multiply((p-y)[:,None]).toarray()
    Sigma=E.T @ E/len(y)-np.outer(E.mean(0),E.mean(0))
    w=p*(1-p)*(1-2*p)*np.einsum("ij,jk,ik->i",Z.toarray(),Sigma,Z.toarray())
    tc=np.asarray(Z.T @ w).ravel()/len(y)
    direction=-np.linalg.solve(H,tc)
    fallback=False
    if np.linalg.norm(direction)<1e-12:
        direction=x.copy(); fallback=True
    direction/=np.linalg.norm(direction)
    Lsample=LAM+.25*float(np.max(Z.multiply(Z).sum(1)))
    np.savez_compressed(out/"reference_optimizers.npz",x_ref=x,A_ref=H,Sigma_ref=Sigma,direction=direction,
                        x_ref_crosscheck=x2,gamma_base=.1/Lsample,L_sample=Lsample)
    cert=dict(lambda_value=LAM,gradient_norm=float(np.linalg.norm(g)),parameter_error_bound=float(np.linalg.norm(g)/LAM),
              objective=f,crosscheck_distance=float(np.linalg.norm(x-x2)),second_solver=str(second.message),
              second_refined_gradient_norm=float(np.linalg.norm(sparse_logistic(Z,y,x2)[1])),history=history,
              eigmin_A_ref=float(np.linalg.eigvalsh(H)[0]),L_sample=Lsample,gamma_base=.1/Lsample,
              direction_scope="Frozen descriptive -A_ref^{-1}T[Sigma_ref], not a coefficient prediction for E3",direction_fallback=fallback)
    assert cert["parameter_error_bound"]<=1e-8
    save_json(out/"optimizer_certificates.json",cert)
    return cert


def partition(y,N,regime,seed):
    M=len(y); rng=np.random.default_rng(seed)
    if regime=="R0":
        return np.tile(np.arange(M),(N,1))
    if regime=="R1":
        return rng.permutation(M).reshape(N,-1)
    order=np.concatenate([rng.permutation(np.flatnonzero(y==a)) for a in (0,1)])
    shards=order.reshape(2*N,-1)
    return shards[rng.permutation(2*N)].reshape(N,-1)


def partition_diagnostics(Z,y,x,Aref,members,m,out):
    p=expit(Z @ x); N=len(members)
    gs=[]; hs=[]; sigmas=[]; proportions=[]
    for rows in members:
        z=Z[rows]
        e=z.multiply((p[rows]-y[rows])[:,None]).toarray()
        g=e.mean(0)+LAM*x
        covariance=e.T @ e/len(rows)-np.outer(e.mean(0),e.mean(0))
        h=(z.T @ sparse.diags(p[rows]*(1-p[rows])) @ z).toarray()/len(rows)+LAM*np.eye(124)
        gs.append(g); hs.append(h); sigmas.append(covariance); proportions.append(float(y[rows].mean()))
    gs=np.array(gs); hs=np.array(hs); sigmas=np.array(sigmas)
    v=sigmas.sum(0)/(N*N*m)
    np.savez_compressed(out,members=members,g_c=gs,A_c=hs,Sigma_c=sigmas,Vbar_ref=v,label_proportions=proportions)
    return dict(N=N,m=m,sample_size=members.shape[1],G=float(np.mean(np.sum((gs-gs.mean(0))**2,axis=1))),
        curvature_heterogeneity=float(np.mean(np.sum((hs-Aref)**2,axis=(1,2)))),
        Vbar_trace=float(np.trace(v)),Vbar_frobenius=float(np.linalg.norm(v)),
        global_gradient_agreement=float(np.linalg.norm(gs.mean(0)-sparse_logistic(Z,y,x)[1])),
        label_proportion_min=min(proportions),label_proportion_max=max(proportions))
