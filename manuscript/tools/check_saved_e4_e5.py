#!/usr/bin/env python3
"""Check saved E4/E5 point estimates and intervals; no fitting, resampling or training."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
checks=[]

def close(name,a,b,atol=5e-13,rtol=2e-10):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    assert a.shape==b.shape,(name,a.shape,b.shape)
    ok=bool(np.allclose(a,b,atol=atol,rtol=rtol,equal_nan=True))
    e=np.abs(a-b);finite=e[np.isfinite(e)]
    checks.append({'check':name,'values':int(a.size),'pass':ok,
                   'max_absolute_difference':float(finite.max()) if finite.size else 0.0})
    if not ok:raise AssertionError(checks[-1])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'revision_audit/point_estimate_checks.json'))
    ap.add_argument('--e4-batches',default=None,help='Optional original E4 inputs/batches.npz; not bundled in manuscript.')
    args=ap.parse_args()
    E4=ROOT/'supplementary_results/E4';E5=ROOT/'supplementary_results/E5'
    z=np.load(E4/'models.npz',allow_pickle=False)
    ids=list(z['cell_ids']);ks=list(z['K']);algs=list(z['algorithms']);dev=z['deviations'];R=dev.shape[1]
    close('model-reference consistency',z['models']-z['x_ref'],dev)
    if args.e4_batches:
        b=np.load(args.e4_batches,allow_pickle=False)
        rebuilt=np.stack([b['batch_raw_sum'][:,:,-k:].sum(axis=2)/b['batch_count'][:,:,-k:].sum(axis=2)[:,:,None,None] for k in ks],axis=3)
        close('original batch sums to all 1512 averaged models',rebuilt,z['models'])
    table=pd.read_csv(E4/'BIAS_VARIANCE_MSE.csv',float_precision='round_trip')
    infer=np.load(E4/'inference_arrays.npz',allow_pickle=False)
    names=list(infer['feature_names'])
    for i,row in table.iterrows():
        c=ids.index(row.cell_id);a=algs.index(row.algorithm);k=ks.index(row.K)
        e=dev[c,:,a,k];mu=e.mean(axis=0);mse=np.mean(np.sum(e*e,axis=1))
        U=(np.sum(e.sum(axis=0)**2)-np.sum(e*e))/(R*(R-1))
        V=np.sum((e-mu)**2)/(R-1)
        projection=mu@z['direction']
        close(f'E4/{i}/U,V,MSE,share,projection',[U,V,mse,U/mse,projection],
              [row.U,row.V,row.MSE,row.share,row.projection])
        close(f'E4/{i}/mean vector',mu,json.loads(row.mean_vector))
        close(f'E4/{i}/decomposition',[U+V],[mse])
        for key in ['U','V','MSE','share','projection','train_gap','test_loss']:
            f=names.index(f'{row.algorithm}:{key}')
            close(f'E4/{i}/{key} interval',[row[key+'_lower_simultaneous'],row[key+'_upper_simultaneous']],
                  [infer['lower'][c,f,k],infer['upper'][c,f,k]])
    pairs=table[table.algorithm=='SCAFFOLD']
    for i,row in pairs.iterrows():
        c=ids.index(row.cell_id);k=ks.index(row.K);s=dev[c,:,0,k];f=dev[c,:,1,k];d=s-f
        def u(e): return (np.sum(e.sum(0)**2)-np.sum(e*e))/(R*(R-1))
        du=u(s)-u(f);ud=u(d);cross=(du-ud)/2
        mse_d=np.mean(np.sum(s*s,axis=1)-np.sum(f*f,axis=1))
        v_d=(np.sum((s-s.mean(0))**2)-np.sum((f-f.mean(0))**2))/(R-1)
        close(f'E4/{i}/paired differences',[du,ud,cross,mse_d,v_d],
              [row.delta_U,row.U_delta,row.C_cross,row.delta_MSE,row.delta_V])
    qz=np.load(E5/'VECTORS.npz',allow_pickle=False)
    q=-np.linalg.solve(qz['A'],qz['T_Sigma'])
    close('E5 reference q independent linear solve',q,qz['q'])
    v=q/np.linalg.norm(q)
    align=pd.read_csv(E5/'FULL_VECTOR_ALIGNMENT.csv',float_precision='round_trip')
    for i,row in align.iterrows():
        c=ids.index(row.cell_id);k=ks.index(row.K)
        obs=(dev[c,:,0,k]-dev[c,:,1,k]).mean(0)
        p=row.gamma**2*((row.H-1)*(2*row.H-1)/(12*row.H))/row.m*q
        close(f'E5/{i}/observed vector',obs,qz['observed'][int(i)])
        close(f'E5/{i}/proxy vector',p,qz['proxy'][int(i)])
        pn=np.linalg.norm(p);on=np.linalg.norm(obs)
        if pn>0:
            ratio=obs@p/pn**2;cos=obs@p/pn/on;res=np.linalg.norm(obs-p)/pn
            close(f'E5/{i}/projection ratio,cosine,residual',[ratio,cos,res],
                  [row.projection_ratio,row.cosine,row.relative_residual])
        else: assert np.isnan(row.cosine) and np.isnan(row.projection_ratio)
    # Plot sources must preserve the exact selected columns and all seven windows.
    for alg,slug in [('SCAFFOLD','scaffold'),('FedAvg','fedavg')]:
        saved=pd.read_csv(ROOT/f'figures/redrawn/data/e4_averaging_{slug}.csv',float_precision='round_trip')
        orig=table[(table.cell_id=='E3_R0_p0_H4_N128_g0.196078431373')&(table.algorithm==alg)].sort_values('K')
        for key in ['K','U','U_lower_simultaneous','U_upper_simultaneous','V','V_lower_simultaneous','V_upper_simultaneous']:
            close(f'plotted/{slug}/{key}',saved[key].to_numpy(),orig[key].to_numpy(),atol=1e-18,rtol=1e-14)
    result={'checks':len(checks),'scalar_values_compared':sum(x['values'] for x in checks),
            'failures':sum(not x['pass'] for x in checks),
            'max_absolute_difference':max(x['max_absolute_difference'] for x in checks),
            'training':False,'resampling':False,'proof_audit':False,
            'batch_reconstruction':bool(args.e4_batches),'details':checks}
    out=Path(args.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))

if __name__=='__main__': main()
