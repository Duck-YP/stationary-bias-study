"""Analysis-only verification from extracted review inputs; never calls training."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def cast_rows(rows):
    result=[]
    for row in rows:
        item={}
        for key,value in row.items():
            if value=='':
                item[key]=''
                continue
            try:
                item[key]=int(value) if key in ('H','N','m','runs','term','coordinate','seed','partition_seed') else float(value)
            except ValueError:
                item[key]=value
        result.append(item)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--deps',type=Path,help='Optional existing isolated dependency directory; no install is performed')
    args=parser.parse_args()
    bundle=args.bundle.resolve();out=args.output.resolve()
    core=bundle/'REVIEW_CORE';source=bundle/'SOURCE_REVIEW/supplementary_study'
    assert not out.is_relative_to(core) and not out.is_relative_to(source)
    out.mkdir(parents=True,exist_ok=False)
    for relative in ('diagnostics','tables','figure_data','figures/main_candidates','figures/appendix_candidates'):
        (out/relative).mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(out/'mplconfig')
    os.environ['NUMBA_CACHE_DIR']=str(out/'numba_cache')
    os.environ['OPENBLAS_NUM_THREADS']='1'
    if args.deps:sys.path.insert(0,str(args.deps.resolve()))
    sys.path.insert(0,str(source))
    import numpy as np
    from study.report import fits,scalar_ci,variance_ci,policy_contrasts
    from study.analysis import ustat
    from study.model import theory
    from study.figures import figures
    from PIL import Image
    conf=json.loads((core/'PROTOCOL_FROZEN.json').read_text())
    shutil.copyfile(core/'PROTOCOL_FROZEN.json',out/'PROTOCOL_FROZEN.json')
    ref=dict(np.load(core/'reference_optimizers.npz',allow_pickle=False))
    full=cast_rows(read_csv(core/'full_results.csv'))
    per_run=read_csv(core/'per_run_estimates.csv')
    records={};per_run_lookup={}
    for row in per_run:
        cell=row['cell_id'];seed=int(row['seed']);axis=0 if row['algorithm']=='scaffold' else 1
        item=records.setdefault(cell,{}).setdefault(seed,dict(mean=np.zeros((2,len(json.loads(row['mean_vector'])))),
                                                           raw_mean=np.zeros((2,len(json.loads(row['raw_mean_vector']))))))
        item['mean'][axis]=json.loads(row['mean_vector'])
        item['raw_mean'][axis]=json.loads(row['raw_mean_vector'])
        per_run_lookup[cell,seed,axis]=row
    checks=[];maxerror=0.0
    def compare(name,actual,expected,context):
        nonlocal maxerror
        actual=float(actual);expected=float(expected)
        if np.isnan(actual) and np.isnan(expected):error=0.0
        else:
            error=abs(actual-expected)
            assert np.isclose(actual,expected,rtol=1e-12,atol=1e-14,equal_nan=True),(name,actual,expected,context)
        maxerror=max(maxerror,error)
        checks.append(dict(context=context,metric=name,actual=actual,original=expected,absolute_error=error,status='PASS'))
    batch_index=read_csv(core/'BATCH_INDEX.csv')
    batch_count=0
    for row in batch_index:
        path=bundle/row['export_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['export_sha256']
        with np.load(path,allow_pickle=False) as result:
            pb=int(result['primary_batches']);counts=result['batch_count'];samples=int(result['samples'])
            assert int(counts[:pb].sum())==samples
            mean=result['batch_sum'][:pb].sum(axis=0)/samples
            raw=result['batch_raw_sum'][:pb].sum(axis=0)/samples
            second=result['batch_sumsq'][:pb].sum(axis=0)/samples
            assert mean.tobytes()==result['mean'].tobytes()
            assert raw.tobytes()==result['raw_mean'].tobytes()
            assert second.tobytes()==result['second_moment'].tobytes()
            assert np.array_equal(result['paired_batch_difference'],result['batch_means'][:,0]-result['batch_means'][:,1])
            assert np.array_equal(result['paired_raw_batch_difference'],result['batch_raw_means'][:,0]-result['batch_raw_means'][:,1])
            if row['phase']=='production':
                item=records[row['cell_id']][int(row['seed'])]
                assert item['mean'].tobytes()==result['mean'].tobytes()
                assert item['raw_mean'].tobytes()==result['raw_mean'].tobytes()
            batch_count+=1
    fitrows,contrasts=fits(out,conf,records)
    original_fit=read_csv(core/'fitted_coefficients.csv')
    assert len(fitrows)==len(original_fit)
    for row,old in zip(fitrows,original_fit):
        assert row['fit']==old['fit'] and row['term']==int(old['term']) and row['coordinate']==int(old['coordinate'])
        for key,value in row.items():
            if isinstance(value,(float,int,np.floating,np.integer)):
                compare(key,value,old[key],row['fit'])
    policy_contrasts(out,conf,records,ref)
    original_policy=read_csv(core/'tables/E3_policy_allocation_contrasts.csv')
    rebuilt_policy=read_csv(out/'tables/E3_policy_allocation_contrasts.csv')
    assert len(original_policy)==len(rebuilt_policy)
    for row,old in zip(rebuilt_policy,original_policy):
        assert row['cell_id']==old['cell_id'] and row['algorithm']==old['algorithm']
        for key in ('signed_projection_difference','adjusted_ci_lower','adjusted_ci_upper'):
            compare(key,row[key],old[key],row['cell_id'])
    # Same existing statistics functions, using saved per-run means and centered second moments.
    # This intentionally does not evaluate any objective on examples or call build_report/CLI.
    directions={c['id']:(ref['direction'] if c['family']=='E3' else
                np.asarray(theory(2)['Z_target'])/np.linalg.norm(theory(2)['Z_target'])) for c in conf['cells']}
    by_cell={c['id']:c for c in conf['cells']}
    for row in full:
        cell=row['cell_id'];c=by_cell[cell];direction=directions[cell];seeds=conf['production_seeds']
        if row['algorithm']=='matched_difference':
            paired=np.array([records[cell][s]['mean'][0]-records[cell][s]['mean'][1] for s in seeds])
            if c['family']=='E1':paired=paired/c['gamma']**2
            m,lo,hi,_=scalar_ci(paired@direction)
            for key,v in (('signed_projection',m),('ci_lower',lo),('ci_upper',hi)):
                compare(key,v,row[key],cell+'/matched_difference')
            continue
        a=0 if row['algorithm']=='scaffold' else 1
        center=ref['x_ref'] if c['family']=='E3' else 0
        B=np.array([records[cell][s]['mean'][a]-center for s in seeds])
        rawB=np.array([records[cell][s]['raw_mean'][a]-center for s in seeds])
        mse=np.array([float(per_run_lookup[cell,s,a]['raw_second_moment']) for s in seeds])
        m,lo,hi,_=scalar_ci(B@direction)
        _,alo,ahi,_=scalar_ci(B@direction,conf['multiplicity']['E3_signed_projections'] if c['family']=='E3' else 16)
        u,ul,uh=ustat(B);rawu,_,_=ustat(rawB)
        variance,vlo,vhi=variance_ci(rawB,mse)
        mm,mlo,mhi,_=scalar_ci(mse)
        values=dict(signed_projection=m,ci_lower=lo,ci_upper=hi,adjusted_ci_lower=alo,adjusted_ci_upper=ahi,
            plugin_bias_squared=float(B.mean(axis=0)@B.mean(axis=0)),bias_squared_U=u,bias_squared_ci_lower=ul,
            bias_squared_ci_upper=uh,raw_bias_squared_U=rawu,raw_variance_trace=variance,
            total_parameter_MSE=mm,raw_variance_trace_ci_lower=vlo,raw_variance_trace_ci_upper=vhi,
            total_parameter_MSE_ci_lower=mlo,total_parameter_MSE_ci_upper=mhi)
        for key,v in values.items():compare(key,v,row[key],cell+'/'+row['algorithm'])
        if c['family']=='E3':
            losses=np.array([float(per_run_lookup[cell,s,a]['heldout_log_loss']) for s in seeds])
            loss,ll,lh,_=scalar_ci(losses)
            for key,v in (('heldout_log_loss',loss),('heldout_log_loss_ci_lower',ll),('heldout_log_loss_ci_upper',lh)):
                compare(key,v,row[key],cell+'/'+row['algorithm'])
    with np.load(bundle/'AUDIT_BATCHES/PAIRED_COVARIANCE.npz',allow_pickle=False) as covariance:
        for row in read_csv(bundle/'AUDIT_BATCHES/PAIRED_COVARIANCE_INDEX.csv'):
            proj=covariance[row['projection_key']]
            assert np.array_equal(np.cov(proj,rowvar=False,ddof=1),covariance[row['covariance_key']])
    for path in (core/'diagnostics').glob('E2_*.npz'):
        shutil.copyfile(path,out/'diagnostics'/path.name)
    figures(out,conf,full,fitrows)
    captions=json.loads((core/'figures/captions_and_provenance.json').read_text())
    figure_values=0;render_checks=[]
    for item in captions:
        original=read_csv(core/item['source_csv']);rebuilt=read_csv(out/item['source_csv'])
        assert len(original)==len(rebuilt),(item['figure'],len(original),len(rebuilt))
        for row,old in zip(rebuilt,original):
            for key,value in old.items():
                if row[key]==value:continue
                try:
                    # CSV render differences in int/float spelling are acceptable, numeric values are NOT rounded.
                    assert float(row[key])==float(value) or np.isnan(float(row[key])) and np.isnan(float(value)),(key,row[key],value)
                except ValueError:
                    raise AssertionError((item['figure'],key,row[key],value))
            figure_values+=1
        png=next((out/'figures').rglob(item['figure']+'.png'))
        oldpng=next((core/'figures').rglob(item['figure']+'.png'))
        im=np.asarray(Image.open(png).convert('RGB'));oldim=np.asarray(Image.open(oldpng).convert('RGB'))
        assert im.std()>1 and im.shape[0]>300 and im.shape[1]>300,png
        render_checks.append(dict(figure=item['figure'],shape=list(im.shape),nonblank=True,
            original_pixels_identical=bool(im.shape==oldim.shape and np.array_equal(im,oldim)),
            source_rows=len(original),exact_source_values=True))
    with (out/'STATISTIC_REPLAY_CHECKS.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(checks[0]));writer.writeheader();writer.writerows(checks)
    qa=dict(scope='analysis-only; no training/optimizer solve; input reports untouched',
        production_cells=len(records),production_paired_runs=sum(len(r) for r in records.values()),
        pilot_and_production_batch_pairs_checked=batch_count,primary_sums_bit_exact=True,
        coefficient_rows=len(fitrows),paired_policy_contrasts=len(rebuilt_policy),main_statistic_checks=len(checks),
        max_absolute_numeric_replay_error=maxerror,figures=len(captions),figure_source_rows=figure_values,
        figures_nonblank=True,figure_values_exact=True,figure_render_checks=render_checks,
        precision='retained float64 arrays bit-exact; QA replay tolerance 1e-12 relative/1e-14 absolute is only a reproduction check, NOT a changed scientific gate',
        limitations=['No complete dataset-dependent report rebuild','No new per-batch loss or within-round covariance',
                     'No LaTeX compilation','No replacement of unresolved scientific/numerical flags'])
    (out/'REPLAY_QA.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in qa.items() if k!='figure_render_checks'},indent=2))


if __name__=='__main__':
    main()
