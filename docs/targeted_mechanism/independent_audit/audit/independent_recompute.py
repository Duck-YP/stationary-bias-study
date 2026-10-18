"""Read-only audit from NPZ batch summaries; no submitted analysis/model code imported.
Replays the frozen descriptive estimators and bootstrap; does not simulate training.
"""
from pathlib import Path
import hashlib, json, math
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'review'; OUT=ROOT/'audit'; OUT.mkdir(exist_ok=True)
P=json.loads((SRC/'PROTOCOL_FROZEN.json').read_text())
conditions=['rho_minus_symmetric','rho_zero_symmetric','rho_plus_symmetric','rho_plus_asymmetric']
rhos=[-.25,0.,.25,.25]; names=['SCAFFOLD','FedAvg','difference']
checks=[]; totals={}
def compare(group,label,a,b,atol=3e-10,rtol=3e-12):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    assert a.shape==b.shape,(group,label,a.shape,b.shape)
    err=float(np.max(np.abs(a-b))) if a.size else 0.
    ok=bool(np.allclose(a,b,atol=atol,rtol=rtol,equal_nan=False))
    checks.append(dict(group=group,label=label,count=int(a.size),max_abs_error=err,passed=ok))
    if not ok: raise AssertionError((group,label,err))
def target(rho):
    # Independently obtained from symbolic third derivative: T111=.1,
    # T122=T212=T221=-.1; all other entries zero.
    A=np.diag([1.,2.]); C=np.diag([1+rho,1-rho]); T=np.zeros((2,2,2))
    T[0,0,0]=.1; T[0,1,1]=T[1,0,1]=T[1,1,0]=-.1
    SC=C/(np.diag(A)[:,None]+np.diag(A)[None,:])
    v=np.linalg.solve(A,np.einsum('ijk,jk->i',T,C))
    b11=-.5*np.linalg.solve(A,np.einsum('ijk,jk->i',T,SC))
    fa=-.75*v; ctrl=-7/16*v
    return b11,np.stack([fa+ctrl,fa,ctrl])

def key(phase,c,N,g,s):
    text=f'targeted-trigonometric-v1|{phase}|{c}|{N}|{g.hex()}|{s}'
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'little')

# Manifest checks (not claims about remote public availability).
manifest=json.loads((SRC/'PACKAGE_MANIFEST.json').read_text())
for rel,entry in manifest.items():
    f=SRC/rel
    assert f.is_file(),rel
    assert hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256'],rel
for rel,sha in P['simulation_source_hashes'].items():
    assert hashlib.sha256((SRC/rel).read_bytes()).hexdigest()==sha
    assert (SRC/rel).read_bytes()==(ROOT/'source'/rel).read_bytes()
totals['review_manifest_files']=len(manifest)
base=json.loads((SRC/'BASELINE_MANIFEST.json').read_text())['files']; matched=0; mismatches=[]
for rel,entry in base.items():
    if not rel.startswith('manuscript/'): continue
    f=ROOT/'manuscript_input'/rel
    if f.exists():
        if hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256']:matched+=1
        else:mismatches.append(rel)
    else:mismatches.append('missing:'+rel)
totals['manuscript_baseline_matching_files']=matched;totals['manuscript_baseline_mismatches']=mismatches

# Retain exact grid order for the frozen bootstrap stream.
cell_values={}; window_values={}; rows=[]; maximum_identity=0.; max_coefficient_identity=0.; max_control_mean=0.
keys=set(); batchcount=0; cost=0.
for cell in P['cells']:
    c,N,g,rho=cell['condition'],cell['N'],cell['gamma'],cell['rho']
    idx=(c,N,g); values=[]; temporal=[]; bh=target(rho)[0]
    PH=(1-g*np.array([1.,2.]))**P['H']
    # Stable evaluation, independent of submitted operators function.
    B=-np.expm1(P['H']*np.log1p(-g*np.array([1.,2.])))
    for seed in P['production_seeds']:
        path=SRC/'run_summaries/production'/f'{c}_N{N}_g{int(1/g)}'/f'seed_{seed}/result.npz'
        with np.load(path,allow_pickle=False) as z:
            a=z['rows']; sch=cell['schedule']
            assert a.shape==(64,27) and np.isfinite(a).all()
            assert np.all(a[:,26]==sch['batch_length'])
            assert int(z['t'])==sch['burn']+64*sch['batch_length']
            assert int(z['seed'])==seed and int(z['N'])==N and float(z['gamma'])==g
            assert float(z['rho'])==rho and bool(z['asymmetric'])==cell['asymmetric']
            assert int(z['key'])==key('production',c,N,g,seed)
            assert int(z['key']) not in keys; keys.add(int(z['key']))
            assert np.array_equal(a[1:,:4],a[:-1,4:8]) and np.array_equal(a[-1,4:8],z['x'].ravel())
            cost+=float(z['cpu']); batchcount+=len(a)
            wins={}
            for wn,sl in [('primary',slice(None)),('first_half',slice(0,32)),('last_half',slice(32,None))]:
                w=a[sl]; raw=np.average(w[:,8:12],axis=0,weights=w[:,26]).reshape(2,2)
                bal=np.average(w[:,12:16],axis=0,weights=w[:,26]).reshape(2,2)
                eta=np.average(w[:,16:18],axis=0,weights=w[:,26]); res=np.average(w[:,18:22],axis=0,weights=w[:,26]).reshape(2,2)
                endpoints=(w[-1,4:8]-w[0,:4]).reshape(2,2)/w[:,26].sum()
                ident=B*(raw-bal)-eta+PH*endpoints-res
                allident=np.concatenate([ident,ident[0:1]-ident[1:2]])
                maximum_identity=max(maximum_identity,float(abs(allident).max()))
                max_coefficient_identity=max(max_coefficient_identity,float(abs(allident/B/g**2).max()))
                max_control_mean=max(max_control_mean,float(w[:,25].max()))
                wins[wn]={}
                for en,arr in [('balance',bal),('raw',raw)]:
                    normalized=np.concatenate([(arr-g/N*bh)/g**2,((arr[0]-arr[1])/g**2)[None]])
                    wins[wn][en]=normalized
            for en in ['balance','raw']:
                for ai,name in enumerate(names):
                    for j in range(2):
                        rows.append(dict(condition=c,N=N,gamma=g,seed=seed,estimator=en,observable=name,coordinate=j+1,
                                         coefficient=wins['primary'][en][ai,j],first_half=wins['first_half'][en][ai,j],last_half=wins['last_half'][en][ai,j],
                                         last_minus_first=wins['last_half'][en][ai,j]-wins['first_half'][en][ai,j]))
            values.append(wins)
    cell_values[idx]=values
npzcount=len(keys); totals.update(production_runs=npzcount,paired_batches=batchcount,production_cpu_hours=cost/3600,
    max_window_identity_residual=maximum_identity,max_normalized_identity_residual=max_coefficient_identity,max_control_mean=max_control_mean)
new=pd.DataFrame(rows); old=pd.read_csv(SRC/'results/per_run_vectors.csv')
join=['condition','N','gamma','seed','estimator','observable','coordinate']; merged=new.merge(old,on=join,suffixes=('_new','_old'),validate='one_to_one')
assert len(merged)==len(old)==len(new)==3456
for col in ['coefficient','first_half','last_half','last_minus_first']:
    compare('NPZ-to-run',col,merged[col+'_new'],merged[col+'_old'])
new.to_csv(OUT/'reconstructed_per_run.csv',index=False)

labels=[]
for i,c in enumerate(conditions):
    tar=target(rhos[i])[1]
    for ai,name in enumerate(names):
        for j in range(2):labels.append(dict(kind='intercept',comparison=c,observable=name,coordinate=j+1,target=tar[ai,j]))
for kind,li,ri in [('law_contrast',2,3),('signed_covariance_contrast',2,0)]:
    for ai,name in enumerate(names):
        for j in range(2):labels.append(dict(kind=kind,comparison=conditions[li]+' minus '+conditions[ri],observable=name,coordinate=j+1,
                target=target(rhos[li])[1][ai,j]-target(rhos[ri])[1][ai,j]))

def fam(arr):
    # Four conditions, six paired coordinates. Works with a leading draw axis.
    return np.concatenate([arr.reshape(*arr.shape[:-2],24),arr[...,2,:]-arr[...,3,:],arr[...,2,:]-arr[...,0,:]],axis=-1)
replayed=[]; design_checks=[]
for en in ['balance','raw']:
 for subset in ['full','omit_largest_gamma']:
    rng=np.random.default_rng(P['bootstrap_seed']); nboot=P['bootstrap_draws']
    estim=np.zeros((4,6)); var=np.zeros((4,6)); bs=np.zeros((nboot,4,6))
    for ci,c in enumerate(conditions):
        cc=[x for x in P['cells'] if x['condition']==c and (subset=='full' or x['gamma']<1/512)]
        X=np.array([[1,x['gamma']*1024,128/x['N']] for x in cc])
        weights=np.linalg.lstsq(X.T,np.array([1.,0.,0.]),rcond=None)[0]
        val=np.array([[r['primary'][en].ravel() for r in cell_values[(c,x['N'],x['gamma'])]] for x in cc])
        fit=np.linalg.lstsq(X,val.mean(1),rcond=None)[0]; estim[ci]=fit[0]
        var[ci]=np.sum(weights[:,None]**2*val.var(1,ddof=1)/12,axis=0)
        for ii in range(len(cc)):
            choices=rng.integers(0,12,size=(nboot,12))
            bs[:,ci]+=weights[ii]*np.mean(val[ii][choices],axis=1)
        design_checks.append(dict(estimator=en,grid=subset,condition=c,scaled_condition_number=np.linalg.cond(X),
                                  weights=weights.tolist(),weight_squares_sum=float(weights@weights)))
    e=fam(estim); boot=fam(bs)
    se=np.sqrt(np.r_[var.ravel(),var[2]+var[3],var[2]+var[0]])
    bse=np.std(boot,axis=0,ddof=1); critical=np.quantile(np.max(np.abs(boot-e)/np.where(bse>0,bse,1),axis=1),.95)
    for i,lab in enumerate(labels):
        t95=student_t.ppf(.975,11)*se[i]; bon=student_t.ppf(1-.05/72,11)*se[i]; delta=critical*bse[i]
        replayed.append(dict(**lab,estimator=en,grid=subset,estimate=e[i],standard_error=se[i],
            marginal_t_lower=e[i]-t95,marginal_t_upper=e[i]+t95,
            marginal_bootstrap_lower=np.quantile(boot[:,i],.025),marginal_bootstrap_upper=np.quantile(boot[:,i],.975),
            simultaneous_lower=e[i]-delta,simultaneous_upper=e[i]+delta,simultaneous_width=2*delta,
            bonferroni_t_lower=e[i]-bon,bonferroni_t_upper=e[i]+bon,approximate_simultaneous_critical_value=critical))
replay=pd.DataFrame(replayed); saved=pd.read_csv(SRC/'results/intercepts_and_contrasts.csv')
k=['kind','comparison','observable','coordinate','estimator','grid']; joined=replay.merge(saved,on=k,suffixes=('_new','_old'),validate='one_to_one')
assert len(joined)==len(saved)==144
joined.to_csv(OUT/'inference_comparison_details.csv',index=False)
for col in sorted(set(replay.columns)-set(k)):
    compare('frozen-inference',col,joined[col+'_new'],joined[col+'_old'],atol=3e-8 if col=='approximate_simultaneous_critical_value' else 1e-8*np.maximum(joined['standard_error_old'].to_numpy(),1e-4),rtol=0)
replay.to_csv(OUT/'independent_fits_and_intervals.csv',index=False)
(OUT/'design_checks.json').write_text(json.dumps(design_checks,indent=2))

# Same-run summaries; no pseudo-replication of batches.
full=[]; temp=[]; rm=[]
for cell in P['cells']:
    c,N,g=cell['condition'],cell['N'],cell['gamma']; vals=cell_values[(c,N,g)];meta=dict(condition=c,N=N,gamma=g,rho=cell['rho'])
    for en in ['balance','raw']:
        v=np.array([x['primary'][en] for x in vals]); d=np.array([x['last_half'][en]-x['first_half'][en] for x in vals])
        for ai,alg in enumerate(names):
            for j in range(2):
                for typ,data in [('mean',v),('time',d)]:
                    mean=np.mean(data[:,ai,j]);se=np.std(data[:,ai,j],ddof=1)/np.sqrt(12)
                    rec=dict(**meta,estimator=en,observable=alg,coordinate=j+1)
                    if typ=='mean': full.append(dict(**rec,mean=mean,se=se,lower=mean-student_t.ppf(.975,11)*se,upper=mean+student_t.ppf(.975,11)*se))
                    else:temp.append(dict(**rec,last_minus_first=mean,paired_run_se=se,lower=mean-student_t.ppf(.975,11)*se,upper=mean+student_t.ppf(.975,11)*se))
    v=np.array([x['primary']['raw']-x['primary']['balance'] for x in vals])
    for ai,alg in enumerate(names):
        for j in range(2):
            mean=np.mean(v[:,ai,j]);se=np.std(v[:,ai,j],ddof=1)/np.sqrt(12)
            rm.append(dict(**meta,observable=alg,coordinate=j+1,raw_minus_balance=mean,paired_run_se=se,
                           lower=mean-student_t.ppf(.975,11)*se,upper=mean+student_t.ppf(.975,11)*se))
for arr,fn,k0,cols in [(full,'full_grid.csv',['condition','N','gamma','estimator','observable','coordinate'],['mean','se','lower','upper']),
                      (temp,'temporal_diagnostics.csv',['condition','N','gamma','estimator','observable','coordinate'],['last_minus_first','paired_run_se','lower','upper']),
                      (rm,'paired_estimator_comparison.csv',['condition','N','gamma','observable','coordinate'],['raw_minus_balance','paired_run_se','lower','upper'])]:
    z=pd.DataFrame(arr).merge(pd.read_csv(SRC/'results'/fn),on=k0,suffixes=('_new','_old'),validate='one_to_one')
    for col in cols:compare('run-statistics',fn+':'+col,z[col+'_new'],z[col+'_old'])

# Calculate stronger numerical resolution descriptions, not new hypothesis tests.
primary=replay[(replay.estimator=='balance')&(replay.grid=='full')].copy()
primary['max_abs_interval']=primary[['simultaneous_lower','simultaneous_upper']].abs().max(axis=1)
primary['fraction_of_matched_active_coefficient']=primary.max_abs_interval/.021875
primary.to_csv(OUT/'primary_resolution_readout.csv',index=False)
pd.DataFrame(checks).to_csv(OUT/'comparison_checks.csv',index=False)
totals.update(comparison_groups=len(checks),scalar_comparisons=sum(x['count'] for x in checks),
              numerical_comparison_failures=sum(not x['passed'] for x in checks),
              fitted_scalar_summaries=144,bootstrap_draws_replayed_per_family=P['bootstrap_draws'])
(OUT/'audit_summary.json').write_text(json.dumps(totals,indent=2))
print(json.dumps(totals,indent=2))
