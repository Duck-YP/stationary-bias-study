"""Pilot batch diagnostics, never used as independent-run observations."""
import os,sys,pathlib,csv,json
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'supplementary_study/.deps'))
import numpy as np
def iact_proxy(v):
    v=v-v.mean(); var=np.dot(v,v)
    if var==0: return 1.
    ac=[np.dot(v[:-k],v[k:])/var for k in range(1,min(21,len(v)//2))]
    total=0.
    for k in range(0,len(ac)-1,2):
        pair=ac[k]+ac[k+1]
        if pair<=0: break
        total+=pair
    return max(1.,1+2*total)
def main():
    rows=[]
    for p in sorted((ROOT/'local/pilot').glob('*/seed_*/result.npz')):
        with np.load(p) as d:
            r=d['rows']; bal=r[:,12:16].reshape(-1,2,2); raw=r[:,8:12].reshape(-1,2,2)
            for estimator,x in [('balance',bal),('raw',raw)]:
                obs=np.concatenate([x,(x[:,0]-x[:,1])[:,None]],axis=1)
                for a,name in enumerate(['SCAFFOLD','FedAvg','difference']):
                    for j in range(2):
                        v=obs[:,a,j]
                        rows.append(dict(condition=p.parent.parent.name,seed=int(d['seed']),estimator=estimator,observable=name,coordinate=j+1,
                            batches=len(v),batch_length=int(d['batch_length']),mean=float(v.mean()),batch_sd=float(v.std(ddof=1)),
                            batch_lag1=float(np.corrcoef(v[:-1],v[1:])[0,1]),initial_positive_pair_iact_proxy=float(iact_proxy(v))))
    with (ROOT/'PILOT_DIAGNOSTICS.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if __name__=='__main__': main()
