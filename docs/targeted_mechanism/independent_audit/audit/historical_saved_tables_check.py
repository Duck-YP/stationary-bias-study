"""Independent replay of the historical H=4 fits from delivered sufficient statistics.
This is not a replay from the unavailable original archive/checkpoints.
"""
from pathlib import Path
import numpy as np,pandas as pd,json
R=Path(__file__).resolve().parents[1];H=R/'review/historical_audit';O=R/'audit'
w=pd.read_csv(H/'per_run_windows.csv'); c=pd.read_csv(H/'per_run_fit_coefficients.csv'); f=pd.read_csv(H/'fitted_coefficients.csv')
# Reproduce every stored seedwise fit using its actual design/grid.
print('grids',c.grid.unique(),'windows',c.window.unique(),'estimands',c.estimand.unique())
print('gamma',sorted(w.gamma.unique()),'N',sorted(w.N.unique()))
checks=[]
for keys,t in c.groupby(['window','grid','estimator','algorithm','estimand','seed','coordinate'],sort=False):
 win,grid,est,alg,estimand,seed,coord=keys
 z=w[(w.window==win)&(w.estimator==est)&(w.algorithm==alg)&(w.estimand==estimand)&(w.seed==seed)&(w.coordinate==coord)].copy()
 if grid=='drop_max_gamma':z=z[z.gamma<1/128]
 elif grid=='drop_N32':z=z[z.N>32]
 elif grid!='primary':raise ValueError(grid)
 z=z.sort_values(['N','gamma']); X=np.array([np.ones(len(z)),z.gamma*128,32/z.N]).T
 beta=np.linalg.lstsq(X,z.value,rcond=None)[0]*np.array([1.,128.,32.])
 target=t.sort_values('term').coefficient.to_numpy()
 err=float(abs(beta-target).max());scale=max(1.,float(abs(target).max()))
 assert err<1e-8*scale,(keys,err)
 checks.append(dict(window=win,grid=grid,estimator=est,algorithm=alg,estimand=estimand,seed=int(seed),coordinate=int(coord),max_abs=err))
out=pd.DataFrame(checks);out.to_csv(O/'historical_seedwise_fit_replay.csv',index=False)
# Compare primary observable fitted intercepts raw versus balance.
z=f[(f.window=='primary')&(f.grid=='primary')&(f.term==0)&(f.algorithm=='matched_difference')]
print(z[['estimator','estimand','coordinate','estimate','independent_cell_se']].to_string(index=False))
q=z.pivot(index='coordinate',columns='estimator',values='estimate'); delta=q['raw_post']-q['balance']
(O/'historical_fit_audit.json').write_text(json.dumps(dict(seedwise_fits=len(out),fitted_terms=len(c),
 max_abs_error=float(out.max_abs.max()),matched_raw_minus_balance=delta.to_dict(),
 scope='Replayed delivered historical per_run_windows sufficient statistics; original large archive not reopened in this check.'),indent=2))
