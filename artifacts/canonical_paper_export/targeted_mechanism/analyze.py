"""Frozen estimands and independent-cell, paired-run inference; no target fitting."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'supplementary_study/.deps'))
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
from scipy.stats import t as tdist
import json,csv,hashlib
from targeted.model import targets,operators
from targeted.workflow import CONDITIONS,save_json,key_for
OUT=ROOT/'results'
ALG=['SCAFFOLD','FedAvg','difference']
def csvout(name,rows):
    if not rows: return
    OUT.mkdir(exist_ok=True)
    with (OUT/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def observable(raw,bal,g,N,rho):
    out={}
    for name,b in [('balance',bal),('raw',raw)]:
        base=(b-g/N*targets(rho)['B11'])/g**2
        out[name]=np.concatenate([base,(b[0]-b[1])[None]/g**2],axis=0)
    return out
def family(base):
    # shape (..., condition=4, observable=3, coordinate=2)
    return np.concatenate([base.reshape(*base.shape[:-3],24),(base[...,2,:,:]-base[...,3,:,:]).reshape(*base.shape[:-3],6),
                           (base[...,2,:,:]-base[...,0,:,:]).reshape(*base.shape[:-3],6)],axis=-1)
def family_variance(v):
    return np.concatenate([v.reshape(24),(v[2]+v[3]).ravel(),(v[2]+v[0]).ravel()])
def labels():
    out=[]
    for c in CONDITIONS:
        for a in ALG:
            for j in range(2): out.append(dict(kind='intercept',comparison=c[0],observable=a,coordinate=j+1,target=float(targets(c[1])[a][j])))
    for kind,left,right in [('law_contrast',2,3),('signed_covariance_contrast',2,0)]:
        for a in ALG:
            for j in range(2): out.append(dict(kind=kind,comparison=CONDITIONS[left][0]+' minus '+CONDITIONS[right][0],observable=a,coordinate=j+1,
                target=float(targets(CONDITIONS[left][1])[a][j]-targets(CONDITIONS[right][1])[a][j])))
    return out
def classify_interval(lo,hi,margin):
    if lo>=-margin and hi<=margin: return 'inside_resolution_band'
    if hi<-margin or lo>margin: return 'outside_resolution_band'
    if hi-lo>2*margin: return 'too_wide_for_resolution'
    return 'intersects_resolution_band_edge'
def load_runs(protocol):
    data=[]; perrun=[]; batches=[]; identities=[]; window_rows=[]; costs=[]
    for cell in protocol['cells']:
        N=cell['N']; g=cell['gamma']; rho=cell['rho']; cname=cell['condition']; ops=operators(g,4)
        records=[]
        for seed in protocol['production_seeds']:
            path=ROOT/'local/production'/f'{cname}_N{N}_g{round(1/g)}'/f'seed_{seed}/result.npz'
            if not path.exists(): continue
            with np.load(path) as p:
                r=p['rows']; sc=cell['schedule']
                assert r.shape==(sc['batches'],27),f'Frozen batch shape mismatch: {path}'
                assert np.isfinite(r).all() and np.isfinite(p['x']).all() and np.isfinite(p['controls']).all(),str(path)
                assert np.all(r[:,26]==sc['batch_length'])
                assert int(p['t'])==sc['burn']+sc['batches']*sc['batch_length']
                assert int(p['N'])==N and float(p['gamma'])==g and float(p['rho'])==rho and int(p['seed'])==seed
                assert bool(p['asymmetric'])==cell['asymmetric'] and p['key']==key_for('production',cname,N,g,seed)
                np.testing.assert_array_equal(r[1:,:4],r[:-1,4:8])
                np.testing.assert_array_equal(r[-1,4:8],p['x'].ravel())
                costs.append(dict(condition=cname,N=N,gamma=g,seed=seed,cpu_seconds=float(p['cpu']),wall_seconds=float(p['wall']),rounds=int(p['t'])))
                windows={}
                for win,sub in [('primary',r),('first_half',r[:32]),('last_half',r[32:])]:
                    raw=sub[:,8:12].mean(0).reshape(2,2); bal=sub[:,12:16].mean(0).reshape(2,2)
                    windows[win]=observable(raw,bal,g,N,rho)
                    T=sub[:,26].sum(); start=sub[0,:4].reshape(2,2); end=sub[-1,4:8].reshape(2,2)
                    eta=sub[:,16:18].mean(0); res=sub[:,18:22].mean(0).reshape(2,2)
                    corrected=ops[1]*(raw-bal)-eta+ops[2]*(end-start)/T
                    identity=corrected-res
                    for a in range(2):
                        for j in range(2):
                            window_rows.append(dict(condition=cname,N=N,gamma=g,seed=seed,window=win,algorithm=ALG[a],coordinate=j+1,round_count=int(T),
                                start=float(start[a,j]),end=float(end[a,j]),raw_post_mean=float(raw[a,j]),balance_mean=float(bal[a,j]),noise_eta_mean=float(eta[j]),
                                round_recursion_residual_mean=float(res[a,j]),control_mean=float(sub[:,22+j].mean()),max_control_mean=float(sub[:,25].max())))
                            identities.append(dict(condition=cname,N=N,gamma=g,seed=seed,window=win,observable=ALG[a],coordinate=j+1,
                                endpoint_corrected_residual=float(corrected[a,j]),accumulated_round_recursion_residual=float(res[a,j]),
                                residual_after_arithmetic_accounting=float(identity[a,j]),coefficient_scale_residual=float(identity[a,j]/ops[1][j]/g**2)))
                    for j in range(2):
                        identities.append(dict(condition=cname,N=N,gamma=g,seed=seed,window=win,observable='difference',coordinate=j+1,
                            endpoint_corrected_residual=float(corrected[0,j]-corrected[1,j]),accumulated_round_recursion_residual=float(res[0,j]-res[1,j]),
                            residual_after_arithmetic_accounting=float(identity[0,j]-identity[1,j]),coefficient_scale_residual=float((identity[0,j]-identity[1,j])/ops[1][j]/g**2)))
                for b,row in enumerate(r):
                    for a in range(2):
                        for j in range(2):
                            batches.append(dict(condition=cname,N=N,gamma=g,seed=seed,batch=b,algorithm=ALG[a],coordinate=j+1,round_count=int(row[26]),
                                start=float(row[a*2+j]),end=float(row[4+a*2+j]),raw_post_mean=float(row[8+a*2+j]),balance_mean=float(row[12+a*2+j]),
                                eta_mean=float(row[16+j]),recursion_residual_mean=float(row[18+a*2+j]),control_mean=float(row[22+j]),
                                max_round_recursion_residual=float(row[24]),max_control_mean=float(row[25])))
                for obs in ['balance','raw']:
                    for a in range(3):
                        for j in range(2):
                            perrun.append(dict(condition=cname,N=N,gamma=g,seed=seed,estimator=obs,observable=ALG[a],coordinate=j+1,
                                coefficient=float(windows['primary'][obs][a,j]),first_half=float(windows['first_half'][obs][a,j]),last_half=float(windows['last_half'][obs][a,j]),
                                last_minus_first=float(windows['last_half'][obs][a,j]-windows['first_half'][obs][a,j])))
                records.append(windows)
        if len(records)!=12: raise RuntimeError(f'Incomplete production: {cname},N={N},g={g}: {len(records)}/12')
        data.append({**cell,'records':records})
    csvout('per_run_vectors.csv',perrun); csvout('batch_summaries.csv',batches); csvout('window_summaries.csv',window_rows)
    csvout('finite_window_identity.csv',identities); csvout('simulation_costs.csv',costs)
    save_json(OUT/'execution_diagnostics.json',dict(completed_runs=len(costs),production_cpu_hours=sum(c['cpu_seconds'] for c in costs)/3600,
        max_identity_residual=max(abs(r['residual_after_arithmetic_accounting']) for r in identities),
        max_identity_coefficient_scale_residual=max(abs(r['coefficient_scale_residual']) for r in identities),
        max_observed_control_mean=max(r['max_control_mean'] for r in window_rows)))
    return data
def fit_family(data,estimator,subset,protocol):
    rng=np.random.default_rng(protocol['bootstrap_seed']); B=protocol['bootstrap_draws']
    estimates=np.zeros((4,3,2)); boot=np.zeros((B,4,3,2)); variances=np.zeros((4,3,2))
    slopes=[]
    for ci,cond in enumerate(CONDITIONS):
        cells=[c for c in data if c['condition']==cond[0] and (subset=='full' or c['gamma']<1/512)]
        X=np.array([[1,c['gamma'],1/c['N']] for c in cells]); pinv=np.linalg.pinv(X); w=pinv[0]
        values=np.stack([np.stack([r['primary'][estimator] for r in c['records']]) for c in cells])
        coeff=np.einsum('ij,jak->iak',pinv,values.mean(1))
        estimates[ci]=coeff[0]
        variances[ci]=np.einsum('i,iak->ak',w*w,values.var(1,ddof=1)/12)
        for ii in range(len(cells)):
            indices=rng.integers(0,12,size=(B,12))
            boot[:,ci]+=w[ii]*values[ii][indices].mean(1)
        fitted=np.einsum('ij,jak->iak',X,coeff)
        for a in range(3):
            for j in range(2): slopes.append(dict(condition=cond[0],estimator=estimator,grid=subset,observable=ALG[a],coordinate=j+1,
                intercept=float(coeff[0,a,j]),gamma_slope=float(coeff[1,a,j]),inverse_N_slope=float(coeff[2,a,j]),
                residual_rms=float(np.sqrt(np.mean((fitted[:,a,j]-values.mean(1)[:,a,j])**2))),design_condition_number=float(np.linalg.cond(X))))
    est=family(estimates); bs=family(boot); se=np.sqrt(family_variance(variances))
    bse=bs.std(0,ddof=1); safe=np.where(bse>0,bse,1.)
    crit=float(np.quantile(np.max(abs((bs-est)/safe),axis=1),.95))
    rows=[]
    for i,label in enumerate(labels()):
        marginal=tdist.ppf(.975,11)*se[i]; bonf=tdist.ppf(1-.05/(2*36),11)*se[i]
        sim=crit*bse[i]; lo,hi=est[i]-sim,est[i]+sim
        band=protocol['practical_margins'][label['observable']]
        is_zero=abs(label['target'])<1e-16
        band_result=classify_interval(lo,hi,band)
        status=('SUPPORTS_WITHIN_REPORTED_RESOLUTION' if band_result=='inside_resolution_band' else
                ('DISCREPANCY_REQUIRES_AUDIT' if band_result=='outside_resolution_band' else 'INCONCLUSIVE_PRECISION')) if is_zero else (
                'SUPPORTS_WITHIN_REPORTED_RESOLUTION' if lo<=label['target']<=hi and (lo>0 or hi<0) else
                ('DISCREPANCY_REQUIRES_AUDIT' if not lo<=label['target']<=hi else 'INCONCLUSIVE_PRECISION'))
        rows.append(dict(**label,estimator=estimator,grid=subset,estimate=float(est[i]),standard_error=float(se[i]),
            marginal_t_lower=float(est[i]-marginal),marginal_t_upper=float(est[i]+marginal),
            marginal_bootstrap_lower=float(np.quantile(bs[:,i],.025)),marginal_bootstrap_upper=float(np.quantile(bs[:,i],.975)),
            simultaneous_lower=float(lo),simultaneous_upper=float(hi),simultaneous_width=float(2*sim),
            bonferroni_t_lower=float(est[i]-bonf),bonferroni_t_upper=float(est[i]+bonf),
            approximate_simultaneous_critical_value=crit,resolution_margin=band,
            resolution_band_result=band_result if is_zero else 'nonzero_control',
            target_in_simultaneous=bool(lo<=label['target']<=hi),exact_target_sampling_exclusion=bool(not lo<=label['target']<=hi),
            zero_excluded=bool(hi<0 or lo>0),status=status))
    return rows,slopes
def main():
    p=json.loads((ROOT/'PROTOCOL_FROZEN.json').read_text()); data=load_runs(p)
    grid=[]; timechecks=[]; pairedchecks=[]
    for c in data:
        meta={k:c[k] for k in ['condition','N','gamma','rho']}
        for estimator in ['balance','raw']:
            vals=np.stack([r['primary'][estimator] for r in c['records']])
            changes=np.stack([r['last_half'][estimator]-r['first_half'][estimator] for r in c['records']])
            for a in range(3):
                for j in range(2):
                    v=vals[:,a,j]; se=v.std(ddof=1)/np.sqrt(12); half=tdist.ppf(.975,11)*se
                    grid.append(dict(**meta,estimator=estimator,observable=ALG[a],coordinate=j+1,count=12,mean=float(v.mean()),
                        se=float(se),lower=float(v.mean()-half),upper=float(v.mean()+half),width=float(2*half),target=float(targets(c['rho'])[ALG[a]][j])))
                    v=changes[:,a,j]; se=v.std(ddof=1)/np.sqrt(12); half=tdist.ppf(.975,11)*se
                    timechecks.append(dict(**meta,estimator=estimator,observable=ALG[a],coordinate=j+1,last_minus_first=float(v.mean()),
                        paired_run_se=float(se),lower=float(v.mean()-half),upper=float(v.mean()+half),width=float(2*half)))
        deltas=np.stack([r['primary']['raw']-r['primary']['balance'] for r in c['records']])
        for a in range(3):
            for j in range(2):
                v=deltas[:,a,j]; se=v.std(ddof=1)/np.sqrt(12); half=tdist.ppf(.975,11)*se
                pairedchecks.append(dict(**meta,observable=ALG[a],coordinate=j+1,raw_minus_balance=float(v.mean()),paired_run_se=float(se),
                    lower=float(v.mean()-half),upper=float(v.mean()+half),width=float(2*half)))
    csvout('full_grid.csv',grid); csvout('temporal_diagnostics.csv',timechecks); csvout('paired_estimator_comparison.csv',pairedchecks)
    allrows=[]; allslopes=[]
    for estimator in ['balance','raw']:
        for subset in ['full','omit_largest_gamma']:
            rows,slopes=fit_family(data,estimator,subset,p); allrows+=rows; allslopes+=slopes
    csvout('intercepts_and_contrasts.csv',allrows); csvout('fit_diagnostics.csv',allslopes)
    primary=[r for r in allrows if r['estimator']=='balance' and r['grid']=='full']
    csvout('primary_family_36.csv',primary)
    print(json.dumps({'primary_status_counts':{s:sum(r['status']==s for r in primary) for s in sorted(set(r['status'] for r in primary))},
        'paired_rows':[r for r in primary if r['observable']=='difference']},indent=2))
if __name__=='__main__': main()
