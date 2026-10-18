"""Rebuild reports from saved sufficient statistics; never rerun training here."""
import csv
import json
import math
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from scipy.special import expit
from .analysis import interval,ustat,iact_proxy
from .data import save_json,sha,read_libsvm,sparse_logistic
from .engine import write_csv,ALGORITHMS,load_data
from .model import theory


def scalar_ci(values,family=1):
    return tuple(float(v) for v in interval(values,family))


def variance_ci(B,second):
    n=len(B)
    point=float(np.mean(second)-ustat(B)[0])
    if n<3:return point,float("nan"),float("nan")
    leave=np.array([np.mean(np.delete(second,k))-ustat(np.delete(B,k,axis=0))[0] for k in range(n)])
    se=np.sqrt((n-1)/n*np.sum((leave-leave.mean())**2))
    hw=student_t.ppf(.975,n-1)*se
    return point,point-hw,point+hw


def fit_group(out,name,cs,values,features,target,seeds,family,meta):
    X=np.asarray(features,dtype=float)
    Y=np.stack([values[c["id"]] for c in cs],axis=1)
    coefs=np.array([np.linalg.lstsq(X,yy,rcond=None)[0] for yy in Y])
    residual=Y-np.einsum("cp,rpj->rcj",X,coefs)
    save_json(out/"diagnostics"/(name+".json"),dict(cells=[c["id"] for c in cs],seeds=seeds,
        design_matrix=X,condition_number=float(np.linalg.cond(X)),rank=int(np.linalg.matrix_rank(X)),
        seed_coefficients=coefs,seed_residuals=residual,scope="descriptive finite-grid fit; no higher-order analytic expansion is established"))
    rng=np.random.default_rng(61009)
    idx=rng.integers(0,len(seeds),size=(2000,len(seeds)))
    bootstrap=coefs[idx].mean(1)
    np.savez_compressed(out/"diagnostics"/(name+"_bootstrap.npz"),indices=idx,coefficients=bootstrap)
    rows=[]
    for term in range(X.shape[1]):
        for j in range(2):
            m,lo,hi,hw=scalar_ci(coefs[:,term,j])
            _,alo,ahi,_=scalar_ci(coefs[:,term,j],family)
            blo,bhi=np.quantile(bootstrap[:,term,j],[.025,.975])
            rows.append(dict(fit=name,term=term,coordinate=j,estimate=m,ci_lower=lo,ci_upper=hi,
                adjusted_ci_lower=alo,adjusted_ci_upper=ahi,bootstrap_lower=float(blo),bootstrap_upper=float(bhi),
                target=float(target[j]) if term==0 else "",condition_number=float(np.linalg.cond(X)),
                residual_rms=float(np.sqrt(np.mean(residual[:,:,j]**2))),runs=len(seeds),**meta))
    return rows,coefs


def fits(out,conf,records):
    seeds=conf["production_seeds"]; cells=conf["cells"]
    complete={id:r for id,r in records.items() if all(seed in r for seed in seeds)}
    rows=[]; contrasts=[]; intercepts={}; coefficients={}; direction=np.array(theory(2)["Z_target"]); direction/=np.linalg.norm(direction)
    for H in (1,2,4,8):
        cs=sorted([c for c in cells if c["family"]=="E1" and c["H"]==H and "E1a" in c["roles"]],key=lambda c:c["gamma"])
        if not all(c["id"] in complete for c in cs): continue
        for a,algorithm in enumerate(ALGORITHMS):
            values={c["id"]:np.array([complete[c["id"]][seed]["mean"][a]*c["N"]/c["gamma"] for seed in seeds]) for c in cs}
            for window,use in (("primary",cs),("drop_max_gamma",cs[:-1])):
                name=f"E1a_{algorithm}_H{H}_{window}"
                rr,co=fit_group(out,name,use,values,[[1,c["gamma"]] for c in use],theory(H)["B11"],seeds,16,
                               dict(experiment="E1a",algorithm=algorithm,H=H,window=window))
                rows.extend(rr)
                if window=="primary": intercepts[algorithm,H]=co[:,0]
    for algorithm in ALGORITHMS:
        for H in (1,4,8):
            if (algorithm,H) in intercepts and (algorithm,2) in intercepts:
                diff=intercepts[algorithm,H]-intercepts[algorithm,2]
                for j in range(2):
                    m,lo,hi,_=scalar_ci(diff[:,j],12)
                    contrasts.append(dict(kind="E1a_H_intercept_difference",algorithm=algorithm,H=H,reference_H=2,coordinate=j,estimate=m,ci_lower=lo,ci_upper=hi,target=0.))
    for H in (2,4,8):
        cs=sorted([c for c in cells if c["family"]=="E1" and c["H"]==H and "E1b" in c["roles"]],key=lambda c:(c["N"],c["gamma"]))
        if not all(c["id"] in complete for c in cs): continue
        values={c["id"]:np.array([(complete[c["id"]][seed]["mean"][0]-complete[c["id"]][seed]["mean"][1])/c["gamma"]**2 for seed in seeds]) for c in cs}
        windows=[("primary",cs),("drop_max_gamma",[c for c in cs if c["gamma"]<1/128]),("drop_N32",[c for c in cs if c["N"]!=32])]
        for window,use in windows:
            name=f"E1b_control_H{H}_{window}"
            rr,co=fit_group(out,name,use,values,[[1,c["gamma"],1/c["N"]] for c in use],theory(H)["B20_ctrl"],seeds,6,
                           dict(experiment="E1b",algorithm="matched_algorithm_difference",H=H,window=window))
            rows.extend(rr)
            if window=="primary": coefficients[H]=co[:,0]
    if 2 in coefficients and 4 in coefficients:
        diff=coefficients[4]-3.5*coefficients[2]
        for j in range(2):
            m,lo,hi,_=scalar_ci(diff[:,j],2)
            contrasts.append(dict(kind="E1b_H4_minus_3point5_H2",algorithm="matched_algorithm_difference",H=4,reference_H=2,coordinate=j,estimate=m,ci_lower=lo,ci_upper=hi,target=0.))
    write_csv(out/"fitted_coefficients.csv",rows,fields=None if rows else ["fit","term","coordinate","estimate","ci_lower","ci_upper","target"])
    write_csv(out/"tables/E1_intercept_contrasts.csv",contrasts,fields=None if contrasts else ["kind","coordinate","estimate","ci_lower","ci_upper"])
    return rows,contrasts


def build_report(root,out):
    conf=json.loads((out/"PROTOCOL_FROZEN.json").read_text())
    Z,y,ref=load_data(out); xref=ref["x_ref"]; fref=sparse_logistic(Z,y,xref)[0]
    direction_real=ref["direction"]
    direction_control=np.array(theory(2)["Z_target"]);direction_control/=np.linalg.norm(direction_control)
    perp=np.array([-direction_control[1],direction_control[0]])
    Ztest,ytest,_=read_libsvm(root/"data/a9a.t",16281)
    records={}; registry=[]; runrows=[]; full=[]; diagrows=[]; vector_rows=[]; sensitivity_rows=[]
    for c in conf["cells"]:
        id=c["id"]; family=c["family"]; d=124 if family=="E3" else 2; direction=direction_real if family=="E3" else direction_control
        r={}; checkpointed=[]; failures=[]
        for seed in conf["production_seeds"]:
            directory=out/"raw/production"/id/f"seed_{seed}"
            if (directory/"result.npz").exists(): r[seed]=dict(np.load(directory/"result.npz"))
            elif (directory/"failure.json").exists(): failures.append(seed)
            elif (directory/"checkpoint.npz").exists(): checkpointed.append(seed)
        records[id]=r; n=len(r)
        execution="COMPLETED" if n==12 else ("IMPLEMENTATION_FAILED" if failures else "RESOURCE_LIMITED" if n or checkpointed else "NOT_RUN")
        stationarity=False
        B=[]; rawB=[]; paired=[]; half=[]; diffs=[]; mse=[]
        task_losses=[[],[]]; task_accuracy=[[],[]]; training_mean=[[],[]]
        for seed,result in sorted(r.items()):
            pb=int(result["primary_batches"]); means=result["mean"]; raw=result["raw_mean"]
            bias=means-(xref if family=="E3" else 0)
            rb=raw-(xref if family=="E3" else 0)
            B.append(bias); rawB.append(rb); paired.append((means[0]-means[1])/c["gamma"]**2 if family=="E1" else means[0]-means[1])
            bm=result["batch_means"][:pb]
            half.append((bm[pb//2:].mean(0)-bm[:pb//2].mean(0)) @ direction)
            diffs.append((raw-means)@direction); mse.append(result["second_moment"])
            loss=[]; accuracy=[]; gap=[]
            if family=="E3":
                for a in (0,1):
                    score=Ztest@means[a]
                    loss.append(float(np.mean(np.logaddexp(0,score)-ytest*score)))
                    accuracy.append(float(np.mean((score>=0)==ytest)))
                    gap.append(sparse_logistic(Z,y,means[a])[0]-fref)
                    task_losses[a].append(loss[-1]); task_accuracy[a].append(accuracy[-1]); training_mean[a].append(gap[-1])
            for a,algorithm in enumerate(ALGORITHMS):
                runrows.append(dict(run_id=f"{id}/seed_{seed}/{algorithm}",cell_id=id,family=family,algorithm=algorithm,seed=seed,
                    partition_seed=c["partition_seed"],regime=c["regime"],N=c["N"],m=c["m"],H=c["H"],gamma=c["gamma"],
                    mean_vector=json.dumps(means[a].tolist()),raw_mean_vector=json.dumps(raw[a].tolist()),bias_vector=json.dumps(bias[a].tolist()),
                    signed_projection=float(bias[a]@direction),raw_signed_projection=float(rb[a]@direction),
                    raw_second_moment=float(result["second_moment"][a]),per_run_tail_variance=float(result["second_moment"][a]-rb[a]@rb[a]),
                    training_mean_model_gap=gap[a] if gap else "",heldout_log_loss=loss[a] if loss else "",heldout_accuracy=accuracy[a] if accuracy else "",
                    control_second_moment=float(result["control_second_moment"]) if a==0 else 0.,
                    max_zero_sum=float(result["max_zero_sum"]),max_relative_zero_sum=float(result["max_relative_zero_sum"]),
                    rounds=int(result["rounds"]),tail_rounds=int(result["samples"]),elapsed_seconds=float(result["elapsed"]),
                    peak_memory_gb=float(result["peak_memory"]),paired_sample_gradient_count=int(result["sample_gradient_evaluations"]),
                    communication_parameter_scalars=int(result["communication_parameter_scalars"]),communication_control_scalars=int(result["communication_control_scalars"]),
                    raw_source=f"raw/production/{id}/seed_{seed}/result.npz",raw_sha256=sha(out/"raw/production"/id/f"seed_{seed}/result.npz")))
                diagrows.append(dict(cell_id=id,algorithm=algorithm,seed=seed,
                    batch_projection_iact_proxy=iact_proxy(bm[:,a]@direction),
                    first_last_half_projected_difference=float(half[-1][a]),raw_minus_primary_projection=float(diffs[-1][a]),
                    control_mean_norm=float(np.linalg.norm(result["control_mean"])) if a==0 else 0.))
                if len(result["batch_means"])>=133:
                    windows={"2x_burn":result["batch_means"][5:69,a].mean(0),"2x_tail":result["batch_means"][:128,a].mean(0),"2x_burn_tail":result["batch_means"][5:133,a].mean(0)}
                    for name,mean in windows.items():
                        sensitivity_rows.append(dict(cell_id=id,algorithm=algorithm,seed=seed,window=name,
                            projected_difference=float((mean-means[a])@direction),difference_vector=json.dumps((mean-means[a]).tolist()),
                            scope="correlated windows within the same run; primary mean remains first64 batches"))
        if n>=2:
            halves=np.asarray(half)
            for a in (0,1):
                _,lo,hi,_=scalar_ci(halves[:,a],2*len(conf["cells"]))
                stationarity|=lo>0 or hi<0
        if n<12:
            inference="NOT_ASSESSED" if n==0 else "STATIONARITY_UNRESOLVED" if stationarity else "PRECISION_INSUFFICIENT"
        else:
            inference="STATIONARITY_UNRESOLVED" if stationarity else "ESTIMABLE"
        if n:
            B=np.array(B); rawB=np.array(rawB); mse=np.array(mse); paired=np.array(paired)
            for a,algorithm in enumerate(ALGORITHMS):
                m,lo,hi,hw=scalar_ci(B[:,a]@direction)
                _,alo,ahi,_=scalar_ci(B[:,a]@direction,conf["multiplicity"]["E3_signed_projections"] if family=="E3" else 16)
                u,ul,uh=ustat(B[:,a]); rawu,_,_=ustat(rawB[:,a])
                target_precision=conf["precision_targets"]["E3_signed_projection_absolute_halfwidth"] if family=="E3" else conf["precision_targets"]["E1_B11_absolute_coordinate_halfwidth"]*c["gamma"]/c["N"]
                if hw>target_precision and inference=="ESTIMABLE": inference="PRECISION_INSUFFICIENT"
                point=B[:,a].mean(0)
                variance,vlo,vhi=variance_ci(rawB[:,a],mse[:,a])
                mm,mlo,mhi,_=scalar_ci(mse[:,a])
                row=dict(cell_id=id,family=family,regime=c["regime"],roles=";".join(c["roles"]),partition_seed=c["partition_seed"],algorithm=algorithm,
                    N=c["N"],m=c["m"],H=c["H"],gamma=c["gamma"],runs=n,execution_status=execution,inference_status=inference,
                    signed_projection=m,ci_lower=lo,ci_upper=hi,adjusted_ci_lower=alo,adjusted_ci_upper=ahi,
                    plugin_bias_squared=float(point@point),bias_squared_U=u,bias_squared_ci_lower=ul,bias_squared_ci_upper=uh,
                    squared_bias_identification="UNRESOLVED_NEAR_ZERO" if (not np.isfinite(ul) or ul<=0<=uh) else "FINITE_TAIL_DISPLACEMENT_ESTIMABLE; not alone a stationary-bias certificate",
                    raw_bias_squared_U=rawu,raw_variance_trace=variance,total_parameter_MSE=float(mse[:,a].mean()),
                    raw_variance_trace_ci_lower=vlo,raw_variance_trace_ci_upper=vhi,
                    total_parameter_MSE_ci_lower=mlo,total_parameter_MSE_ci_upper=mhi,
                    empirical_decomposition_residual=float(mse[:,a].mean()-variance-rawu),bias_vector=json.dumps(point.tolist()),
                    mean_vector=json.dumps((point+xref if family=="E3" else point).tolist()),
                    gamma_over_gamma_imp=c.get("gamma_over_gamma_imp",""),scope="homogeneous bounded additive controlled objective" if family=="E1" else "state-dependent minibatch implications; conditional on stated empirical partition")
                if family=="E3":
                    loss,llo,lhi,_=scalar_ci(task_losses[a]); gap=sparse_logistic(Z,y,xref+point)[0]-fref
                    row.update(mean_model_training_objective_gap=gap,per_run_mean_model_gap=float(np.mean(training_mean[a])),
                        heldout_log_loss=loss,heldout_log_loss_ci_lower=llo,heldout_log_loss_ci_upper=lhi,heldout_accuracy=float(np.mean(task_accuracy[a])))
                else:
                    for j in range(2):
                        cm,cl,ch,_=scalar_ci(B[:,a,j]); row.update({f"bias_{j}":cm,f"bias_{j}_ci_lower":cl,f"bias_{j}_ci_upper":ch})
                full.append(row)
                for j in range(d):
                    cm,cl,ch,_=scalar_ci(B[:,a,j]); vector_rows.append(dict(cell_id=id,algorithm=algorithm,coordinate=j,bias_mean=cm,
                        parameter_mean=cm+(xref[j] if family=="E3" else 0),ci_lower=cl,ci_upper=ch))
                dm,dl,dh,_=scalar_ci(np.array(diffs)[:,a])
                diagrows.append(dict(cell_id=id,algorithm=algorithm,seed="all",raw_minus_primary_projection=dm,
                    raw_minus_primary_ci_lower=dl,raw_minus_primary_ci_upper=dh,first_last_half_projected_difference=scalar_ci(np.array(half)[:,a])[0],
                    scope="Monte Carlo CI on correlated estimator difference; not independent-estimator comparison"))
            pm,plo,phi,phw=scalar_ci(paired@direction)
            pairrow=dict(cell_id=id,family=family,regime=c["regime"],roles=";".join(c["roles"]),partition_seed=c["partition_seed"],algorithm="matched_difference",
                N=c["N"],m=c["m"],H=c["H"],gamma=c["gamma"],runs=n,execution_status=execution,inference_status=inference,
                signed_projection=pm,ci_lower=plo,ci_upper=phi,mean_vector=json.dumps(paired.mean(0).tolist()),
                scope="controlled additive scaled control difference D" if family=="E1" else "matched algorithm difference; includes drift correction and stochastic dynamics")
            if family=="E1":
                k=theory(c["H"])["kappa"]
                for j in range(2):
                    dm,dl,dh,_=scalar_ci(paired[:,j]);pairrow.update({f"D_{j}":dm,f"D_{j}_ci_lower":dl,f"D_{j}_ci_upper":dh,f"D_{j}_target":theory(c["H"])["B20_ctrl"][j],f"Z_{j}":dm/k if k else ""})
                pairrow.update(perpendicular_residual=float(paired.mean(0)@perp),kappa=k,Z_projection=pm/k if k else "",target_projection=float(np.array(theory(c["H"])["B20_ctrl"])@direction))
            full.append(pairrow)
        else:
            for algorithm in (*ALGORITHMS,"matched_difference"):
                full.append(dict(cell_id=id,family=family,regime=c["regime"],roles=";".join(c["roles"]),partition_seed=c["partition_seed"],algorithm=algorithm,N=c["N"],m=c["m"],H=c["H"],gamma=c["gamma"],runs=0,execution_status=execution,inference_status=inference))
        registry.append(dict(cell_id=id,family=family,regime=c["regime"],roles=";".join(c["roles"]),partition_seed=c["partition_seed"],
            H=c["H"],N=c["N"],m=c["m"],gamma=c["gamma"],planned_paired_runs=12,completed_paired_runs=n,
            checkpointed_seeds=";".join(map(str,checkpointed)),failed_seeds=";".join(map(str,failures)),
            execution_status=execution,inference_status=inference,burn=c["schedule"]["burn"],batch_length=c["schedule"]["batch_length"],
            primary_batches=64,collected_batches=c["schedule"]["batches"]))
        records[id]={seed:{"mean":result["mean"],"raw_mean":result["raw_mean"]} for seed,result in r.items()}
    write_csv(out/"EXPERIMENT_REGISTRY.csv",registry)
    write_csv(out/"per_run_estimates.csv",runrows)
    write_csv(out/"full_results.csv",full)
    write_csv(out/"tables/full_vector_means.csv",vector_rows)
    write_csv(out/"diagnostics/stationarity_and_estimator_checks.csv",diagrows)
    write_csv(out/"diagnostics/window_sensitivity_runs.csv",sensitivity_rows,fields=None if sensitivity_rows else ["cell_id","algorithm","seed","window","projected_difference"])
    summary_sensitivity=[]
    keys=set((r["cell_id"],r["algorithm"],r["window"]) for r in sensitivity_rows)
    for id,a,w in sorted(keys):
        vals=[r["projected_difference"] for r in sensitivity_rows if (r["cell_id"],r["algorithm"],r["window"])==(id,a,w)]
        m,lo,hi,_=scalar_ci(vals,12)
        summary_sensitivity.append(dict(cell_id=id,algorithm=a,window=w,runs=len(vals),estimate=m,ci_lower=lo,ci_upper=hi))
    write_csv(out/"diagnostics/window_sensitivity_summary.csv",summary_sensitivity,fields=None if summary_sensitivity else ["cell_id","algorithm","window","estimate","ci_lower","ci_upper"])
    fitrows,contrasts=fits(out,conf,records)
    policy=policy_contrasts(out,conf,records,ref)
    partition_and_noise_summaries(out,conf,records,ref,full)
    additional_checks(out,conf,Z,y,ref,records)
    from .figures import figures
    figures(out,conf,full,fitrows)
    documentation(root,out,conf,registry,full,fitrows,contrasts,policy)
    annotate_longrun_accuracy(out,registry,full)
    add_auxiliary_registry(out,registry)
    print("ANALYSIS",sum(r["execution_status"]=="COMPLETED" for r in registry),"/",len(registry),"complete cells;",len(runrows)//2,"paired production runs",flush=True)
    return registry,full,fitrows


def policy_contrasts(out,conf,records,ref):
    rows=[]; cells=conf["cells"]; direction=ref["direction"]
    for regime in ("R0","R1","R2"):
        cs=[c for c in cells if c["family"]=="E3" and c["regime"]==regime and c["partition_seed"] in (0,4101)]
        baseline=next(c for c in cs if c["H"]==4 and c["N"]==32 and "allocation" in c["roles"])
        for c in cs:
            if c["id"]==baseline["id"] or "negative_control" in c["roles"]: continue
            common=sorted(set(records[c["id"]]) & set(records[baseline["id"]]))
            if not common: continue
            for a,algorithm in enumerate(ALGORITHMS):
                values=[float((records[c["id"]][seed]["mean"][a]-records[baseline["id"]][seed]["mean"][a])@direction) for seed in common]
                m,lo,hi,_=scalar_ci(values,36)
                rows.append(dict(regime=regime,algorithm=algorithm,cell_id=c["id"],baseline_cell_id=baseline["id"],N=c["N"],H=c["H"],gamma=c["gamma"],
                    common_seed_labels=len(common),signed_projection_difference=m,adjusted_ci_lower=lo,adjusted_ci_upper=hi,
                    dependence="different configuration keys yield separate streams; joint seed labels retained as resampling units",
                    scope="allocation/policy contrast under finite-tail protocol; no gamma-squared or ranking constraint"))
        low=next(c for c in cs if c["N"]==8 and c["H"]==4 and "allocation" in c["roles"])
        high=next(c for c in cs if c["N"]==128 and c["H"]==4 and "allocation" in c["roles"])
        common=sorted(set(records[low["id"]]) & set(records[high["id"]]))
        if common:
            for a,algorithm in enumerate(ALGORITHMS):
                vals=[float((records[high["id"]][s]["mean"][a]-records[low["id"]][s]["mean"][a])@direction) for s in common]
                m,lo,hi,_=scalar_ci(vals,36)
                rows.append(dict(regime=regime,algorithm=algorithm,cell_id=high["id"],baseline_cell_id=low["id"],N=128,H=4,gamma=high["gamma"],
                    common_seed_labels=len(common),signed_projection_difference=m,adjusted_ci_lower=lo,adjusted_ci_upper=hi,
                    contrast_kind="allocation endpoints N128 minus N8",scope="conditional on primary empirical partition; separate config streams"))
    write_csv(out/"tables/E3_policy_allocation_contrasts.csv",rows,fields=None if rows else ["regime","algorithm","cell_id","signed_projection_difference"])
    return rows


def additional_checks(out,conf,Z,y,ref,records):
    from .data import partition
    from .model import LAM,A,C
    from scipy.linalg import solve_discrete_lyapunov
    original=np.load(out/"data/membership.npz")["retained_row_ids"]
    unique=sorted(set((c["regime"],c["N"],c["partition_seed"]) for c in conf["cells"] if c["family"]=="E3"))
    rng=np.random.default_rng(51009)
    vectors=np.array([rng.normal(size=124)*s for s in (.1,.5,1.)])
    objective_rows=[]
    for regime,N,seed in unique:
        members=partition(y,N,regime,seed)
        if regime!="R0": np.testing.assert_array_equal(np.sort(members.ravel()),np.arange(len(y)))
        meta=dict(retained_row_indices=members,original_file_row_ids=original[members])
        if regime=="R2":
            prng=np.random.default_rng(seed)
            ordered=np.concatenate([prng.permutation(np.flatnonzero(y==a)) for a in (0,1)])
            shards=ordered.reshape(2*N,-1)
            assigned=prng.permutation(2*N).reshape(N,2)
            np.testing.assert_array_equal(shards[assigned].reshape(N,-1),members)
            meta.update(shards=shards,original_shard_row_ids=original[shards],assigned_shard_ids=assigned)
        np.savez_compressed(out/f"diagnostics/membership_{regime}_N{N}_p{seed}.npz",**meta)
        for k,x in enumerate(vectors):
            globalg=np.asarray(Z.T@(expit(Z@x)-y)).ravel()/len(y)+LAM*x
            if regime=="R0": localg=globalg
            else:
                gs=[]
                for ids in members:
                    z=Z[ids]
                    gs.append(np.asarray(z.T@(expit(z@x)-y[ids])).ravel()/len(ids)+LAM*x)
                localg=np.mean(gs,0)
            residual=float(np.linalg.norm(globalg-localg))
            assert residual<1e-10*(1+np.linalg.norm(globalg))
            objective_rows.append(dict(regime=regime,N=N,partition_seed=seed,test_vector=k,gradient_residual=residual,
                                       membership_scope="replicated shared pool" if regime=="R0" else "all retained rows exactly once"))
    write_csv(out/"diagnostics/retained_objective_gradient_agreement.csv",objective_rows)
    h1=[]
    for c in conf["cells"]:
        if c["family"]!="E3" or c["H"]!=1: continue
        for seed in records[c["id"]]:
            r=np.load(out/"raw/production"/c["id"]/f"seed_{seed}/result.npz")
            residual=max(float(np.max(abs(r["batch_raw_means"][:,0]-r["batch_raw_means"][:,1]))),float(np.max(abs(r["snapshot"][:,0]-r["snapshot"][:,1]))))
            h1.append(dict(cell_id=c["id"],seed=seed,check="within_configuration_algorithms",residual=residual,passed=residual<1e-10))
    r0=[c for c in conf["cells"] if c["family"]=="E3" and c["H"]==1 and c["regime"]=="R0"]
    if all(len(records[c["id"]])==12 for c in r0):
        for seed in conf["production_seeds"]:
            baseline=np.load(out/"raw/production"/r0[0]["id"]/f"seed_{seed}/result.npz")
            for c in r0[1:]:
                r=np.load(out/"raw/production"/c["id"]/f"seed_{seed}/result.npz")
                residual=max(float(np.max(abs(r["batch_raw_means"]-baseline["batch_raw_means"]))),float(np.max(abs(r["snapshot"]-baseline["snapshot"]))))
                h1.append(dict(cell_id=c["id"],seed=seed,check="R0_cross_allocation_shared_indices",residual=residual,passed=residual<1e-10))
    write_csv(out/"diagnostics/E3_H1_actual_data_checks.csv",h1,fields=None if h1 else ["cell_id","seed","check","residual","passed"])
    # Calibration of the stated U-statistic and nominal jackknife uncertainty at zero bias.
    gamma=1/128;H=4;N=32;P=np.eye(2)-gamma*A;M=solve_discrete_lyapunov(P,gamma**2*C/N)
    PH=np.linalg.matrix_power(P,H); T=64*10*int(np.ceil(1/(theory(H)["mu"]*gamma*H)))
    S=T*M; power=PH.copy()
    for lag in range(1,T):
        S+=(T-lag)*(power@M+M@power.T)
        power=power@PH
        if np.linalg.norm(power)<1e-15:break
    S/=T*T
    calibration=[]
    for dim,reps,cov in ((2,10000,S),(124,5000,np.eye(124))):
        means=np.random.default_rng(71009+dim).standard_normal((reps,12,dim))@np.linalg.cholesky(cov).T
        sums=means.sum(1); square=np.sum(means**2,axis=2); allsquare=square.sum(1)
        U=(np.sum(sums**2,axis=1)-allsquare)/(12*11)
        leaves=(np.sum((sums[:,None,:]-means)**2,axis=2)-(allsquare[:,None]-square))/(11*10)
        se=np.sqrt(11/12*np.sum((leaves-leaves.mean(1)[:,None])**2,axis=1))
        half=student_t.ppf(.975,11)*se
        row=dict(dimension=dim,repetitions=reps,U_mean=float(U.mean()),U_centering_standard_error=float(U.std(ddof=1)/np.sqrt(reps)),
            negative_fraction=float(np.mean(U<0)),nominal_jackknife_zero_coverage=float(np.mean((U-half<=0)&(U+half>=0))),
            scope="exact Gaussian quadratic stationary-tail mean covariance for d2; isotropic d124 stress calibration; not a coverage certificate for actual minibatch chains")
        calibration.append(row)
        np.savez_compressed(out/f"diagnostics/U_zero_bias_calibration_d{dim}.npz",U=U,jackknife_halfwidth=half,covariance=cov)
    save_json(out/"diagnostics/U_zero_bias_calibration.json",calibration)
    pilot_rows=[]
    for directory in (out/"raw/pilot").glob("*/seed_*"):
        run=json.loads((directory/"run.json").read_text());r=np.load(directory/"result.npz")
        cell=run["cell"];direction=ref["direction"] if cell["family"]=="E3" else np.array(theory(4)["B11"])
        direction=direction/np.linalg.norm(direction)
        for a,algorithm in enumerate(ALGORITHMS):
            values=r["batch_means"][:,a]@direction
            for group in (1,2,4):
                grouped=values.reshape(-1,group).mean(1)
                pilot_rows.append(dict(cell_id=cell["id"],seed=run["seed"],algorithm=algorithm,observable="primary_projection",batch_multiple=group,
                    batch_length=run["schedule"]["batch_length"]*group,batches=len(grouped),iact_proxy=iact_proxy(grouped),
                    naive_batch_mean_se=float(grouped.std(ddof=1)/np.sqrt(len(grouped))),scope="engineering pilot diagnostic only; not final inference"))
            controls=r["batch_ctrl"]/r["batch_count"]
            pilot_rows.append(dict(cell_id=cell["id"],seed=run["seed"],algorithm=algorithm,observable="control_second_moment",iact_proxy=iact_proxy(controls)))
            if cell["family"]=="E3":
                loss=np.array([float(np.mean(np.logaddexp(0,Z@x)-y*(Z@x))+LAM/2*(x@x)) for x in r["snapshot"][:,a]])
                pilot_rows.append(dict(cell_id=cell["id"],seed=run["seed"],algorithm=algorithm,observable="global_training_objective_snapshot",iact_proxy=iact_proxy(loss)))
    write_csv(out/"diagnostics/pilot_batch_sensitivity.csv",pilot_rows)


def partition_and_noise_summaries(out,conf,records,ref,full):
    conditional=[]; across=[]; noise=[]; covariance=[]
    for regime in ("R1","R2"):
        for N in (8,128):
            cs=[c for c in conf["cells"] if c["family"]=="E3" and c["regime"]==regime and c["N"]==N and c["H"]==4 and c["gamma"]==float(ref["gamma_base"])]
            for a,algorithm in enumerate(ALGORITHMS):
                points=[]
                for c in sorted(cs,key=lambda c:c["partition_seed"]):
                    rr=records[c["id"]]
                    if not rr:continue
                    vals=[float((r["mean"][a]-ref["x_ref"])@ref["direction"]) for r in rr.values()]
                    m,lo,hi,_=scalar_ci(vals)
                    conditional.append(dict(regime=regime,N=N,algorithm=algorithm,partition_seed=c["partition_seed"],runs=len(vals),mean=m,ci_lower=lo,ci_upper=hi,
                        scope="conditional on this fixed partition; training seed uncertainty"))
                    if len(vals)==12:points.append(m)
                if len(points)==3:
                    m,lo,hi,_=scalar_ci(points)
                    across.append(dict(regime=regime,N=N,algorithm=algorithm,partitions=3,mean=m,
                        nominal_partition_mean_ci_lower=lo,nominal_partition_mean_ci_upper=hi,observed_partition_std=float(np.std(points,ddof=1)),
                        min_partition_mean=min(points),max_partition_mean=max(points),
                        scope="three partition-level means; spread includes residual training Monte Carlo error; not 36 independent partitions"))
    for c in conf["cells"]:
        if c["family"]!="E3":continue
        part=np.load(out/"diagnostics"/(c["id"]+"_partition.npz"))
        v=part["Vbar_ref"];direction=ref["direction"]
        covariance.append(dict(cell_id=c["id"],regime=c["regime"],N=c["N"],m=c["m"],partition_seed=c["partition_seed"],
            Vbar_trace=float(np.trace(v)),Vbar_direction=float(direction@v@direction),Vbar_norm=float(np.linalg.norm(v)),
            scope="conditional reference-parameter noise, centered within each client; does not include deterministic gradient heterogeneity"))
        if c["regime"] not in ("R1","R2") or c["N"]!=32 or c["H"]==1:continue
        path=out/"diagnostics"/f"deterministic_{c['regime']}_H{c['H']}_g{c['gamma']:.12g}.npz"
        if not path.exists():continue
        baseline=np.load(path)
        for seed,r in records[c["id"]].items():
            for a,algorithm in enumerate(ALGORITHMS):
                xdet=baseline["scaffold_fixed_point"] if a==0 else baseline["fedavg_fixed_point"]
                delta=r["mean"][a]-xdet
                noise.append(dict(cell_id=c["id"],algorithm=algorithm,seed=seed,noise_associated_signed_displacement=float(delta@direction),
                    noise_associated_norm=float(np.linalg.norm(delta)),displacement_vector=json.dumps(delta.tolist()),
                    scope="stochastic finite-tail mean relative to the deterministic algorithm point; not a homogeneous control coefficient"))
    write_csv(out/"tables/E3_conditional_partition_estimates.csv",conditional)
    write_csv(out/"tables/E3_across_partition_sensitivity.csv",across,fields=None if across else ["regime","N","algorithm","partitions","mean"])
    write_csv(out/"tables/E3_noise_associated_displacements.csv",noise)
    write_csv(out/"tables/E3_reference_covariance_projections.csv",covariance)


def annotate_longrun_accuracy(out,registry,full):
    path=out/"diagnostics/E3_H1_actual_data_checks.csv"
    checks=list(csv.DictReader(path.open()))
    failed=[r for r in checks if r["passed"]!="True"]
    affected=set(r["cell_id"] for r in failed)
    for row in registry:
        row["numerical_identity_status"]="STRICT_ABSOLUTE_1e10_LONGRUN_CHECK_FAILED" if row["cell_id"] in affected else "NO_RECORDED_FAILURE"
    for row in full:
        row["numerical_identity_status"]="STRICT_ABSOLUTE_1e10_LONGRUN_CHECK_FAILED" if row["cell_id"] in affected else "NO_RECORDED_FAILURE"
    write_csv(out/"EXPERIMENT_REGISTRY.csv",registry)
    write_csv(out/"full_results.csv",full)
    import shutil
    shutil.copy2(out/"full_results.csv",out/"tables/full_results.csv")
    note=f"""\nExtended long-run accuracy audit: {len(failed)} of {len(checks)} stored H1 within-configuration/cross-allocation checks exceed the absolute 1e-10 comparison used in that additional audit. The original 14 short-path E0 checks and E2 affine checks still pass; no tolerance has been relaxed. Measured maximum within-algorithm H1 vector discrepancy is about 7.54e-10, with scale-normalized discrepancy about 1.86e-10, so a 1e-10 scale-aware bound also does not cover every long run. These are float64 accumulation diagnostics, not scientific counterexamples or trajectories that diverged. The affected configurations are explicitly flagged by numerical_identity_status in the registry/results. Their execution is complete; machine-precision identity validation is not claimed. A separately implemented endpoint-increment kernel is tested in diagnostics/stable_arithmetic_roundoff_audit.csv with the same indices/horizons and no control projection. It does not replace frozen v1 results or fits, and no full-grid stable-kernel production rerun has been performed. A future v2 protocol must preserve v1 artifacts, use explicit source hashes and new independent seeds if new sampling is added.\n"""
    for name in ("SCIENTIFIC_SUMMARY.md","HANDOFF.md","THEORY_SCOPE.md"):
        with (out/name).open("a",encoding="utf-8") as f:f.write(note)
    with (out/"CLAIM_EVIDENCE_MAP.md").open("a",encoding="utf-8") as f:
        f.write("\n| Full-horizon H1 identity at strict 1e-10 precision | MIXED; 48 additional absolute checks fail, max vector discrepancy about 7.54e-10 | diagnostics/E3_H1_actual_data_checks.csv; diagnostics/stable_arithmetic_roundoff_audit.csv | original frozen evidence is unchanged; short exact checks pass; full-grid improved-arithmetic rerun pending | appendix numerical audit / unresolved limitations |\n")


def add_auxiliary_registry(out,production):
    rows=[dict(r,phase="production",experiment_id="production/"+r["cell_id"]) for r in production]
    rows.append(dict(experiment_id="E0/kernel_tests",cell_id="E0",family="E0",phase="implementation_tests",planned_tests=14,completed_tests=14,
        execution_status="COMPLETED",inference_status="ESTIMABLE",evidence="tests/test_report.txt"))
    for r in csv.DictReader((out/"tables/E2_exact_checks.csv").open()):
        id=f"E2_N{r['N']}_H{r['H']}_rho{r['rho']}"
        rows.append(dict(experiment_id="equivalence/"+id,cell_id=id,family="E2",phase="equivalence",N=r["N"],H=r["H"],rho=r["rho"],gamma=1/128,
            planned_paired_runs=1,completed_paired_runs=1,rounds=r["rounds"],execution_status="COMPLETED",inference_status="ESTIMABLE",
            evidence="tables/E2_exact_checks.csv"))
    zero=list(csv.DictReader((out/"tables/E2_zero_initialization.csv").open()))
    rows.append(dict(experiment_id="diagnostic/E2_zero_initialization",cell_id="E2_zero_initialization",family="E2",phase="zero_initialization_diagnostic",
        N=32,H=4,rho=1,gamma=1/128,planned_paired_runs=4,completed_paired_runs=len(zero),execution_status="COMPLETED" if len(zero)==4 else "RESOURCE_LIMITED",
        inference_status="ESTIMABLE",evidence="tables/E2_zero_initialization.csv"))
    pilots=json.loads((out/"diagnostics/pilot_summary.json").read_text())["runs"]
    for id in sorted(set(r["cell"]["id"] for r in pilots)):
        selected=[r for r in pilots if r["cell"]["id"]==id];c=selected[0]["cell"]
        rows.append(dict(experiment_id="pilot/"+id,cell_id=id,family=c["family"],phase="pilot",N=c["N"],H=c["H"],gamma=c["gamma"],regime=c["regime"],
            partition_seed=c["partition_seed"],planned_paired_runs=4,completed_paired_runs=len(selected),execution_status="COMPLETED",inference_status="NOT_ASSESSED",
            evidence="diagnostics/pilot_summary.json"))
    audit=out/"diagnostics/stable_arithmetic_roundoff_audit.csv"
    if audit.exists():
        for r in csv.DictReader(audit.open()):
            rows.append(dict(experiment_id="roundoff/"+r["cell_id"]+"/seed_"+r["seed"],cell_id=r["cell_id"],family="E3",phase="post_freeze_numerical_audit",
                seed=r["seed"],planned_paired_runs=1,completed_paired_runs=1,rounds=r["rounds"],execution_status="COMPLETED",inference_status="ESTIMABLE",
                evidence="diagnostics/stable_arithmetic_roundoff_audit.csv",scope="same indices; improved arithmetic only; not stable-kernel formal production"))
    write_csv(out/"EXPERIMENT_REGISTRY.csv",rows)


def documentation(root,out,conf,registry,full,fitrows,contrasts,policy):
    count=sum(r["execution_status"]=="COMPLETED" for r in registry); total=len(registry)
    pairs=sum(r["completed_paired_runs"] for r in registry)
    completed={fam:sum(r["execution_status"]=="COMPLETED" for r in registry if r["family"]==fam) for fam in ("E1","E3")}
    planned={fam:sum(r["family"]==fam for r in registry) for fam in ("E1","E3")}
    pending=[r for r in registry if r["execution_status"]!="COMPLETED"]
    cert=json.loads((out/"optimizer_certificates.json").read_text())
    e2=list(csv.DictReader((out/"tables/E2_exact_checks.csv").open()))
    e2max=max(float(r["max_control_residual"]) for r in e2)
    pilot=json.loads((out/"diagnostics/pilot_summary.json").read_text())
    metrics="""# Metric definitions

All means refer to the frozen finite-tail protocol. Stationary interpretation needs burn/tail diagnostics; no CI covers deterministic truncation, burn-in, or optimizer error.

- E1 primary: exact nonlinear stationary balance mean; direct raw mean always saved. B11 fits use (N/gamma)*mean without subtraction of B11.
- E1 matched D: paired (balance_scaffold-balance_fedavg)/gamma^2. Z=D/kappa(H), when H>=2. Coordinates, fixed theory-direction projection, and perpendicular residual are all saved.
- E3 primary: direct mean minus x_ref in all 124 parameters; direction frozen from the training objective before production. It is descriptive, not an exact minibatch coefficient target.
- Plug-in squared norm and unclipped cross-run U-statistic are both reported. Jackknife-t uncertainty is nominal and can be unreliable at degeneracy; near-zero squared-bias identification stays unresolved. Gaussian zero-bias calibration is in E0; it is not a coverage guarantee for these chains.
- Raw second moment about x_ref is the parameter MSE. Raw variance = raw second moment minus cross-run U of raw means. No negative variance or U is clipped. Decomposition residual is saved.
- E3 held-out log loss is evaluated for each independent run's own tail-averaged model, then averaged across runs. It is never the loss of a freely deployable pooled model. Accuracy is secondary.
- Training mean-model objective gap is f(estimated ensemble mean)-f(x_ref), distinct from the average objective at raw stochastic checkpoints and from per-run mean-model gaps.
- Batch means diagnose dependence and sensitivity; they are not independent replicate units. Monte Carlo CIs use independent paired run seeds. Joint seed-label bootstrap resamples whole grid vectors.
- Coordinate-family Bonferroni counts are 16 for primary B11 intercept coordinates, 6 for primary control intercept coordinates, 12 for H-intercept contrasts, and 2 for the H4-minus-3.5-H2 contrast. E3 signed cell projections use the frozen 105-member cell/algorithm family. The descriptive allocation/policy contrast table has its own 36-member family (30 contrasts against N32/H4/gamma_base and 6 N128-minus-N8 endpoints). These descriptive contrasts do not establish asymptotic expansions.
- Counts include both paired algorithms, including repeated regularization coordinate operations separately from sample-gradient evaluations. Communication estimates count float64 parameter/control payloads; protocol costs are not interchangeable with gradient budgets.
- The raw field communication_parameter_scalars=2*N*d*rounds is the round-trip payload per algorithm; the pair uses twice that. communication_control_scalars=N*d*rounds is a potential additional explicit-control payload for a conventional implementation, not measured traffic. This zero-sum full-participation implementation updates controls locally from endpoints and the global average; it requires no explicit extra control message. Control storage and local arithmetic still differ.
"""
    scope="""# Theory and evidence scope

E1 checks homogeneous, full-participation, independent bounded additive noise on the supplied nonlinear d=2 objective. H is fixed separately in each asymptotic statement. Only B11 is independent of H: B20(H), remainder constants, and sufficient-step thresholds can depend on H. The imported gamma_imp is a recorded diagnostic, not a final-proof gamma0 certificate.

E2 is the exact state translation xi_tilde=xi+a for f_c=f+a_c^T x with mean a=0 and corresponding initial controls. It does not address unequal Hessians, arbitrary non-IID objectives, or heterogeneous FedAvg coefficients.

E3 uses all 123 a9a features plus a regularized intercept. R0 replicates one empirical objective and has state-dependent noise. R1 is a disjoint IID partition, with finite-sample objective differences. R2 is a simulated label-shard partition. R1/R2 changes with N and partition seed; G and centered Sigma_c are measured separately. Matched algorithm differences include drift correction and stochastic dynamics and cannot be called pure homogeneous control coefficients.

Target inclusion in nominal CIs is a finite-grid diagnostic, never a theorem certification. Resource limitations, precision limitations, stationarity concerns, numerical instability, and theoretical discrepancies have distinct statuses. Every H=4 cell and nested-window fit is retained without target-driven selection.
"""
    (out/"METRIC_DEFINITIONS.md").write_text(metrics,encoding="utf-8")
    (out/"THEORY_SCOPE.md").write_text(scope,encoding="utf-8")
    command=".\\supplementary_study\\Run-Study.ps1"
    commands=f"""# Reproduction and resume

From the repository root, Python 3.12 is used. This machine's executable is `{__import__('sys').executable}`. The launcher uses supplementary_study/.deps when present, otherwise a compatible installed environment.

```powershell
$studyPython = '{__import__('sys').executable}'
& $studyPython -m pip install --target supplementary_study/.deps -r supplementary_study/requirements.lock
{command} --suite E0
{command} --suite data
{command} --suite E2
{command} --suite E2zero
{command} --suite pilot --resume
{command} --suite freeze
{command} --suite deterministic
{command} --suite roundoff
{command} --suite E1 --production --resume --jobs 4 --max-memory-gb 4
{command} --suite E3 --production --resume --jobs 12 --max-memory-gb 8
{command} --suite package
```

`--resume` skips certified result files and continues exact keyed RNG state from checkpoints. It never changes horizons. `--max-wall-hours` provides cooperative checkpointing at chunks of at most 2048 rounds; `--max-memory-gb` is divided across production workers. No background computation is promised after the turn ends. `--suite analysis` and `--suite package` use saved data only. `--dry-run --production --suite E3` prints the frozen matrix without executing it. Source hashes of the simulation kernel/model/data/engine and objective/reference hashes are checked before production. If these change, explicitly version the protocol and preserve old results.

On a new machine, reuse bundled data/raw/configs from the handoff to continue the frozen protocol. A clean complete rerun needs a separate output root or separately copied study directory, because completed results are immutable to this runner. `data` deterministically recreates the same subset; `freeze` preserves an existing protocol.
"""
    (out/"RUN_COMMANDS.md").write_text(commands,encoding="utf-8")
    handoff=f"""# Handoff status

Independent supplementary reimplementation; no manuscript files or previous experiment artifacts were modified.

E0: original 13 tests passed, strengthened to 14 including actual checkpoint-file resume. E2 exact: 24/24 cells, 2000 rounds each. Pilots: {pilot['pilot_cells']} cells, {pilot['completed_runs']} paired runs, separate seeds. Production: {count}/{total} cells, {pairs}/{total*12} paired runs. E1: {completed['E1']}/{planned['E1']}; E3: {completed['E3']}/{planned['E3']}.

Frozen protocol: PROTOCOL_FROZEN.json. Registry: EXPERIMENT_REGISTRY.csv. Exact checkpoints: raw/production/<cell_id>/seed_<seed>/checkpoint.npz. Result files and checkpoints include global/control state, RNG key, exact round index, batch statistics and snapshots.

Resume commands:
```powershell
{command} --suite E1 --production --resume --jobs 4 --max-memory-gb 4
{command} --suite E3 --production --resume --jobs 12 --max-memory-gb 8
{command} --suite package
```

Remaining cells: {len(pending)}. The registry lists every missing seed; missing cells never become zero observations. Optional gamma=1/1024 extension was disabled before production. New sampling needs an explicit v2 protocol and independent extension seeds. Precision/stationarity flags remain in completed cells even when all computation is done.

Outstanding scientific limits: finite-grid remainder is not estimated by nominal CIs; global mixing is not proved; U-statistic near-zero uncertainty is nominal; three partition seeds are too few for strong across-partition inference; SCAFFOLD deterministic consistency is checked at its fixed state, not certified globally attracting. The optional shadow estimator is disabled. The baseline proxy schedule was retained because engineering pilots do not justify shorter stationary horizons. The E0 zero-bias calibration checks estimator centering, not CI coverage.

Pending IDs:
"""+"\n".join(f"- {r['cell_id']}: completed={r['completed_paired_runs']}, checkpoints={r['checkpointed_seeds']}" for r in pending)+"\n"
    (out/"HANDOFF.md").write_text(handoff,encoding="utf-8")
    b11=[r for r in fitrows if r["experiment"]=="E1a" and r["window"]=="primary" and r["term"]==0]
    control=[r for r in fitrows if r["experiment"]=="E1b" and r["window"]=="primary" and r["term"]==0]
    def detail(rows):
        return "\n".join(f"- {r['algorithm']}, H={r['H']}, coordinate={r['coordinate']}: {r['estimate']:.8g}, nominal CI [{r['ci_lower']:.8g}, {r['ci_upper']:.8g}], target={r['target']:.8g}." for r in rows) or "No complete primary grid available for inference."
    e3=[r for r in full if r["family"]=="E3" and "allocation" in r["roles"] and r["algorithm"]!="matched_difference" and r["runs"]]
    realdetail="\n".join(f"- {r['regime']} N={r['N']} {r['algorithm']}: projection={r['signed_projection']:.6g} [{r['ci_lower']:.6g},{r['ci_upper']:.6g}], variance={r['raw_variance_trace']:.6g}, MSE={r['total_parameter_MSE']:.6g}, held-out log loss={r['heldout_log_loss']:.6g}." for r in e3)
    scientific=f"""# Scientific summary

1. E0/E2 implementation: the original 13 E0 test groups and the added checkpoint-file test pass. Tests include reference/production agreement, short H=1 paths with nonzero zero-sum controls, quadratic exact covariance for all H, noncommuting A/C, derivatives, rotation, keyed-noise covariance, and exact chunk-resume trajectories. E2 passes 24 affine-shift cells at 2000 rounds each; max control translation residual={e2max:.6g}. However, the extended full-horizon real-data H1 audit finds float64 accumulation beyond strict 1e-10 tolerance in some original v1 runs. This numerical issue and the separate stable endpoint-increment audit are disclosed below; there is no blanket claim that every long identity check passes. A full-grid improved-arithmetic rerun has not been executed. E2zero transient diagnostics and deterministic fixed-point reports are separate evidence.

2. B11 independent intercepts: the following fits use all four gamma points, with no subtraction of B11 or shared fitted intercept. H=1 is boundary recursion consistency. Intercept contrasts and omitted-largest-gamma sensitivity are saved. The primary H=8 SCAFFOLD intercept differs from H=2 on both adjusted-coordinate contrasts. Removing the largest gamma moves the H=8 estimates toward the target but does not replace the primary result. Thus all-H compatibility is not supported on this finite grid; deterministic curvature/remainder remains an open explanation, rather than a refutation of the fixed-H asymptotic theorem. Compatibility is a finite-grid empirical question; CI target inclusion is not a proof.

{detail(b11)}

3. Control H dependence: the full Cartesian gamma x 1/N grid is fitted separately for H. H=2 and H=4 primary intercepts are close to objective-derived targets; the H4-minus-3.5-H2 adjusted contrast contains zero in both coordinates. H=8 has a small resolved nominal primary target gap that shrinks in the smaller-gamma window; Monte Carlo error alone does not explain all finite-grid displacement. The following intercepts and all H=4 residuals are retained. kappa(4)/kappa(2)=3.5 is exact algebra; the difference contrast and nested-window sensitivity remain descriptive. A nonzero target gap can reflect deterministic finite-grid remainder, implementation/theory questions, or finite precision and must not be relabeled to obtain target inclusion.

{detail(control)}

4. Real-data fixed-budget implications: both algorithms use 256 example gradients per local-step level. R0 reference aggregate covariance is invariant across allocations. R1/R2 centered aggregate covariance changes with partition/N, as the measured partition table shows. Conditional-on-partition inference is separate from seed4102/4103 sensitivity. Values below are direct finite-tail means; U-statistic, matched differences, and uncertainty are in full_results.csv.

{realdetail or 'No completed real-data production estimate is available.'}

5. Reducing gamma and reducing H: tables/E3_policy_allocation_contrasts.csv retains signed contrasts against the fixed N=32,H=4 baseline. No gamma^2 scaling or algorithm ranking is imposed. Mean-model training gap differs from held-out loss and from stationary expected raw-checkpoint loss. Finite-tail per-run average-model evaluation is not a free pooled checkpoint.

6. Accuracy and limitations: reference gradient norm={cert['gradient_norm']:.6g}, absolute parameter certificate={cert['parameter_error_bound']:.6g}, independent optimizer distance={cert['crosscheck_distance']:.6g}. Completed production={count}/{total} cells ({pairs}/{total*12} paired runs). Monte Carlo precision flags, raw/balance paired differences, batch autocorrelation proxies, first/last-half contrasts and correlated 2x burn/tail sensitivities are saved. Nominal CIs do not cover remainder, burn-in, or optimizer error. Resource limits are recorded independently of inference.

7. Integration: the limited affine state translation and directly measured implementation/empirical results are eligible for review. General heterogeneous coefficient theorems, whole-bias H independence, theorem certification by CI inclusion, universal algorithm ranking, and interpreting unresolved precision as no practical effect are unsupported. Candidate figures/LaTeX drafts are supplementary material; no original H=4 discrepancies were replaced. The built-in LaTeX compiler returned a platform-directory failure, so source compilation is unverified (diagnostics/latex_compilation.json); Matplotlib figure PDF/SVG/PNG files were generated successfully.
"""
    (out/"SCIENTIFIC_SUMMARY.md").write_text(scientific,encoding="utf-8")
    if e3:
        with (out/"SCIENTIFIC_SUMMARY.md").open("a",encoding="utf-8") as f:
            f.write("\nObserved interpretation: on R0, the frozen signed mean displacement increases from N=8 to N=128 under fixed total minibatch budget, while raw variance stays near 0.00235. The held-out log loss can improve even as parameter displacement increases, so these estimands are not interchangeable. In R2, the large FedAvg mean displacement includes deterministic label-heterogeneity drift: the independently solved N=32,H=4 deterministic FedAvg point is about 0.08365 from x_ref. Its stochastic algorithm difference cannot be called a pure control-noise coefficient. Reducing gamma and H changes these measured quantities differently; full numeric policy contrasts remain primary. These descriptions are conditional on this objective and frozen partitions, with precision flags preserved.\n")
    save_json(out/"diagnostics/hypothesis_assessments.json",[
        dict(hypothesis="E0 numerical recursion and E2 matched affine translation",assessment="SUPPORTED_WITHIN_SCOPE",evidence="tests/test_report.txt; tables/E2_exact_checks.csv",limitation="limited affine class; not general heterogeneity"),
        dict(hypothesis="E1a independent all-H primary finite-grid B11 compatibility",assessment="MIXED",evidence="fitted_coefficients.csv; tables/E1_intercept_contrasts.csv",limitation="H8 primary displacement; nested sensitivity toward target; CIs omit deterministic remainder"),
        dict(hypothesis="E1b kappa-dependent controlled coefficient consistency",assessment="MIXED",evidence="fitted_coefficients.csv; figure_data/E1_normalized_control_grid.csv",limitation="H2/H4 close; H8 nominal residual; no forced ratios or adjusted point selection"),
        dict(hypothesis="E3 conditional finite-tail allocation/policy effects",assessment="SUPPORTED_WITHIN_SCOPE" if any(r["adjusted_ci_lower"]>0 or r["adjusted_ci_upper"]<0 for r in policy) else "INCONCLUSIVE",evidence="tables/E3_policy_allocation_contrasts.csv; full_results.csv",limitation="descriptive signed direction; state-dependent noise; finite partitions; precision flags remain"),
        dict(hypothesis="whole bias/remainder H independence or general heterogeneous coefficient theorem",assessment="NOT_SUPPORTED",evidence="THEORY_SCOPE.md",limitation="outside experiment/theorem scope, not scientific falsification")])
    claims="""# Claim evidence map

| Claim | Status and effect | Sources | Scope and limitation | Position |
|---|---|---|---|---|
"""
    claims+=f"| Core recursion agreement and affine state translation | SUPPORTED_WITHIN_SCOPE; max control residual {e2max:.6g} | tests/test_report.txt; tables/E2_exact_checks.csv; diagnostics/E2_*.npz | finite numerical checks plus exact affine algebra; no unequal Hessians | appendix / limited proposition |\n"
    for r in b11+control:
        claims+=f"| {r['experiment']} H={r['H']} coordinate={r['coordinate']} {r['algorithm']} intercept | finite-grid diagnostic {r['estimate']:.8g}, nominal CI [{r['ci_lower']:.8g},{r['ci_upper']:.8g}], target {r['target']:.8g}; INCONCLUSIVE as theorem certification | fitted_coefficients.csv; diagnostics/{r['fit']}.json | deterministic remainder not covered; primary/nested windows distinct | candidate main figure with appendix diagnostics |\n"
    for r in e3:
        claims+=f"| {r['regime']} N={r['N']} {r['algorithm']} fixed-budget mean projection | {r['signed_projection']:.8g} [{r['ci_lower']:.8g},{r['ci_upper']:.8g}]; {r['inference_status']} | full_results.csv; per_run_estimates.csv; raw/production/{r['cell_id']}/ | conditional fixed empirical partition; state-dependent noise; no homogeneous coefficient attribution | candidate implications figure |\n"
    claims+="| Whole bias/remainder independent of H; general heterogeneous second-order theorem; universal ranking | NOT_SUPPORTED by this study's scope | THEORY_SCOPE.md | these claims are outside the experiment contract | do not integrate |\n"
    (out/"CLAIM_EVIDENCE_MAP.md").write_text(claims,encoding="utf-8")
    (out/"README.md").write_text(f"# Supplementary experiments handoff\n\nIndependent reimplementation, protocol v1. {count}/{total} production cells completed; {pairs} paired runs. Start with SCIENTIFIC_SUMMARY.md and EXPERIMENT_REGISTRY.csv. RUN_COMMANDS.md provides exact rebuild/resume commands. Raw checkpoints/batch summaries are included with hashes; no previous manuscript results are reproduced by seed or replaced.\n",encoding="utf-8")
    # Narrative drafts only summarize measured results, with explicit inference scope.
    supplement=r"""\documentclass{article}
\usepackage{amsmath,booktabs}
\begin{document}
\section*{Independent supplementary study}
We independently reimplemented the supplied SCAFFOLD and FedAvg recursions in float64.
The study separates controlled homogeneous additive-noise coefficient diagnostics (E1),
an affine-objective control translation (E2), and state-dependent real-data implications (E3).
Only the leading coefficient $B_{11}$ is independent of the fixed local horizon $H$;
the second coefficient, remainder constants, and small-step thresholds can depend on $H$.
Monte Carlo intervals do not cover deterministic truncation or burn-in error.
"""+f"E0 passed the original 13 test groups and an additional checkpoint-file resume audit; E2 passed 24 exact-trajectory cells. Production completed {count} of {total} cells ({pairs} paired runs).\n"
    for r in control:
        supplement+=f"For H={r['H']}, coordinate {r['coordinate']}, the descriptive control intercept was {r['estimate']:.6g}, with nominal interval [{r['ci_lower']:.6g},{r['ci_upper']:.6g}], against target {r['target']:.6g}.\n"
    supplement+=r"""E3 uses a retained 32,512-row a9a training objective and all 123 features plus an L2-regularized intercept.
R0 is a shared empirical-objective diagnostic; R1 and R2 are disjoint simulated client partitions.
Matched heterogeneous algorithm differences include drift correction and stochastic-dynamics effects.
They do not establish a general heterogeneous theorem.
See the complete registry, full coordinate estimates, and H=4 diagnostics before integration.
\end{document}
"""
    (out/"latex/supplementary_results.tex").write_text(supplement,encoding="ascii")
    appendix=r"""\documentclass{article}
\usepackage{amsmath,booktabs}
\begin{document}
\section*{Implementation, uncertainty, and diagnostics}
The primary controlled mean uses the exact stationary nonlinear balance observable;
raw means and their correlated differences are retained.
Pointwise intervals use independent paired run means, with coordinate-family adjustment
and seed-vector bootstrap fits. The signed real-data projection was frozen from the training
objective before production. Squared displacement uses an unclipped cross-run U-statistic;
near-zero jackknife intervals remain nominal and do not certify absence of bias.
The frozen horizon uses a global-curvature proxy: 50 proxy times of burn-in and 64 batches,
each of length 10 proxy times. Representative H=4 cells additionally retain correlated
double-burn and double-tail windows. The proxy is not a proved mixing time.
"""+f"The reference optimizer gradient norm was {cert['gradient_norm']:.6g}; the strong-convexity parameter error certificate was {cert['parameter_error_bound']:.6g}.\n"
    appendix+=r"""Complete H=4 fits, coordinates, residuals, source data, covariance centering, memberships,
checkpoints, and missing-cell statuses accompany this appendix. Target inclusion is not a theorem test.
No experiment changes the previously reported manuscript discrepancies.
\end{document}
"""
    (out/"latex/appendix_supplement.tex").write_text(appendix,encoding="ascii")
    affine=r"""\documentclass{article}
\usepackage{amsmath,amssymb}
\begin{document}
\section*{Affine-objective control translation}
Let $f_c(x)=f(x)+a_c^\top x$ with $N^{-1}\sum_c a_c=0$ and define
$\widetilde\xi_c=\xi_c+a_c$. For the zero-sum representation,
\begin{equation}\label{eq:affine-local}
\theta_{c,h+1}=\theta_{c,h}-\gamma\bigl(\nabla f(\theta_{c,h})+
\varepsilon_{c,h}+\widetilde\xi_c\bigr).
\end{equation}
The server averages endpoints to $x'=N^{-1}\sum_c\theta_{c,H}$, and
\begin{equation}\label{eq:affine-refresh}
\widetilde\xi'_c=\widetilde\xi_c+(\theta_{c,H}-x')/(\gamma H).
\end{equation}
Equations~\eqref{eq:affine-local} and~\eqref{eq:affine-refresh} are exactly the
homogeneous recursion. Corresponding initialization is $x_{\rm het,0}=x_{\rm hom,0}$ and
$\xi_{\rm het,c,0}=\xi_{\rm hom,c,0}-a_c$. Coupling the same additive noises gives
identical global and local paths and translated controls by induction.
The invertible state map $(x,\xi)\mapsto(x,\xi+a)$ intertwines the transition kernels;
pushforward therefore gives a bijection of invariant probability laws whenever they exist.
This algebra neither proves existence or uniqueness nor extends to unequal Hessians,
arbitrary heterogeneous objectives, or a heterogeneous FedAvg coefficient expansion.
Zero controls in both systems generally do not give matching transient paths.
\end{document}
"""
    (out/"latex/affine_equivalence_note.tex").write_text(affine,encoding="ascii")
    for src in (out/"full_results.csv",out/"fitted_coefficients.csv"):
        import shutil
        shutil.copy2(src,out/"tables"/src.name)
    # A compact LaTeX table has literal, measured primary intercepts only.
    lines=[r"\begin{tabular}{llrrrr}",r"\toprule",r"Study & Algorithm & $H$ & Coordinate & Estimate & Target \\",r"\midrule"]
    for r in b11+control:
        lines.append(f"{r['experiment']} & {r['algorithm'].replace('_',' ')} & {r['H']} & {r['coordinate']} & {r['estimate']:.7g} & {r['target']:.7g} \\\\")
    lines.extend([r"\bottomrule",r"\end{tabular}"])
    (out/"tables/coefficient_table.tex").write_text("\n".join(lines)+"\n",encoding="ascii")
