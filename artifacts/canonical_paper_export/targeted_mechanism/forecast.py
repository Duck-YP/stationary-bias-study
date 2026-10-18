import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'supplementary_study/.deps'))
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import scipy.stats as st
import json,hashlib,platform,time,csv
from targeted.workflow import CONDITIONS,schedule,save_json
from targeted.model import targets
def main():
    cells=[dict(condition=c[0],rho=c[1],asymmetric=c[2],N=N,gamma=g,schedule=schedule(g)) for c in CONDITIONS for N in (64,128) for g in (1/512,1/1024,1/2048)]
    pilots=[]; forecasts=[]; covariance={}
    for cond in CONDITIONS:
        vectors=[]
        for seed in range(100101,100105):
            path=ROOT/'local/pilot'/f'{cond[0]}_N64_g1024'/f'seed_{seed}/result.npz'
            with np.load(path) as p:
                r=p['rows']; bal=r[:,12:16].reshape(-1,2,2); obs=np.concatenate([bal.mean(0),(bal[:,0]-bal[:,1]).mean(0)[None]],axis=0)/(1/1024)**2
                vectors.append(obs.ravel())
                lag=[]
                for values in bal.reshape(-1,4).T:
                    lag.append(float(np.corrcoef(values[:-1],values[1:])[0,1]))
                pilots.append(dict(condition=cond[0],seed=seed,cpu_seconds=float(p['cpu']),rounds=int(p['t']),seconds_per_round=float(p['cpu'])/int(p['t']),batch_lag1=lag,max_control_mean=float(r[:,25].max()),max_recursion_residual=float(r[:,24].max())))
        covariance[cond[0]]=np.cov(np.array(vectors),rowvar=False)
    worst_rate=max(p['seconds_per_round'] for p in pilots)
    pilot_cpu=sum(p['cpu_seconds'] for p in pilots)
    # Same tau-scaled tail: global-mean variance term scales ~1/(N gamma)^2.
    # Retain a floor of 1 for local-noise variability; no effect/target fitting.
    for cond in CONDITIONS:
        subset=[c for c in cells if c['condition']==cond[0]]
        X=np.array([[1,c['gamma'],1/c['N']] for c in subset]); w=np.linalg.pinv(X)[0]
        factors=np.array([max(1.,64/c['N']*(1/1024)/c['gamma']) for c in subset])
        se=np.sqrt(np.diag(covariance[cond[0]])*sum(w*w*factors*factors)/12)
        for j in range(6):
            margin=(.011875,.0075,.004375)[j//2]
            forecasts.append(dict(condition=cond[0],observable=('SCAFFOLD','FedAvg','difference')[j//2],coordinate=j%2+1,
                initial_intercept_se=float(se[j]),marginal_95_halfwidth=float(st.t.ppf(.975,11)*se[j]),
                bonferroni_36_halfwidth=float(st.t.ppf(1-.05/(2*36),11)*se[j]),resolution_margin=margin))
    initial_production=sum((c['schedule']['burn']+c['schedule']['batch_length']*64)*worst_rate*(c['N']/64)*12 for c in cells)
    # Keep proposed 64-batch schedule: pilot has only four independent seeds;
    # cannot justify precise horizon optimization from noisy variance estimates.
    safety=1.25
    projected=pilot_cpu+initial_production*safety
    forecast=dict(pilot_runs=pilots,pilot_cpu_seconds=pilot_cpu,worst_measured_seconds_per_round_at_N64=worst_rate,
        production_cpu_seconds_linear_N=initial_production,safety_factor=safety,total_projected_cpu_hours=projected/3600,
        cap_cpu_hours=6.,feasible=projected<=6*3600,precision_forecasts=forecasts,
        assumptions='N-linear CPU scaling, maximum measured pilot rate, 25% reserve. Precision uses 4 independent pilot seeds and conservative max(1,64/N * gamma_pilot/gamma) scaling; predictive approximation, not guaranteed precision.',
        horizon_decision='Retain initial 64 batches; no target-inclusion-based selection. Pilot precision forecasts are noisy (4 seeds) and do not establish margin resolution. All unresolved outputs will be reported.')
    save_json(ROOT/'COST_PRECISION_FORECAST.json',forecast)
    source={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'targeted').glob('*.py')) if p.name in ('model.py','kernels.py','workflow.py')}
    protocol=dict(version='targeted-trigonometric-v1',frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        objective='A=diag(1,2), alpha=1/20, three sine ridges; separate explicitly selected trigonometric_chunk',H=4,cells=cells,
        production_seeds=list(range(200101,200113)),pilot_seeds=list(range(100101,100105)),pilot_schedule=schedule(1/1024),
        primary_estimator='Nonlinear balance; raw POST-round global means as same-run cross-check',
        observable_order=['SCAFFOLD','FedAvg','difference'],coordinates=[1,2],
        estimands='C=(balance-(gamma/N)B11)/gamma^2; D=(balance_S-balance_F)/gamma^2; law and signed-covariance contrasts after separate fits',
        fit='Unweighted OLS intercept per condition/observable/coordinate on (1,gamma,1/N); no constraints',
        sensitivity='Omit largest gamma only; preserve primary full grid',
        coupling='Independent keyed streams across condition, grid cell, phase and seed; same indexed noises within SCAFFOLD/FedAvg pair. Seed labels alone do not create cross-cell dependence.',
        resampling='Resample each independent cell run vector jointly across algorithms/coordinates/raw/balance/windows; independently across cells. Fixed bootstrap seed 2026101401, 4000 draws.',
        primary_family='24 condition x observable x coordinate intercepts + 6 symmetric-minus-asymmetric law contrasts + 6 rho-plus-minus-rho-minus contrasts = 36 scalars',
        bootstrap_draws=4000,bootstrap_seed=2026101401,
        intervals='Marginal Student t (df=11 conservative) and bootstrap percentile; approximate simultaneous centered bootstrap max-|standardized error| family of 36; Bonferroni t df11 sensitivity.',
        practical_margins=dict(SCAFFOLD=.011875,FedAvg=.0075,difference=.004375),
        windows='Primary all 64 batches; diagnostic equal-length first32 and last32, same runs; not stationarity certification',
        precision_caveat='Sampling intervals exclude burn-in and deterministic grid remainder. Two N levels do not identify an N rate.',
        freeze_rule='No extension, outcome-dependent exclusion or estimator replacement. Keep all results.',
        simulation_source_hashes=source,production_authorized_by_cost_gate=forecast['feasible'],cpu_cap_seconds=21600.,
        cost_forecast='COST_PRECISION_FORECAST.json',checkpoints='Every burn-in and sampling batch; indexed-noise restart, saved states/controls/time/endpoints')
    save_json(ROOT/'PROTOCOL_FROZEN.json',protocol)
    environment=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),logical_cpus=os.cpu_count(),packages={})
    import importlib.metadata as md
    for pkg in ['numpy','scipy','numba','llvmlite','matplotlib','pytest']: environment['packages'][pkg]=md.version(pkg)
    save_json(ROOT/'ENVIRONMENT.json',environment)
    print(json.dumps({'pilot_cpu_seconds':pilot_cpu,'forecast_cpu_hours':projected/3600,'feasible':forecast['feasible'],'precision':forecasts[:6]},indent=2))
if __name__=='__main__': main()
