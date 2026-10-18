import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .engine import write_csv,ALGORITHMS
from .model import theory
from .data import sha,save_json

COLORS={"scaffold":"#0072B2","fedavg":"#009E73"}


def figures(out,conf,full,fitrows):
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"pdf.fonttype":42,"svg.fonttype":"none"})
    captions=[]
    def save(fig,name,rows,caption,main=True):
        dest=out/("figures/main_candidates" if main else "figures/appendix_candidates")
        csvpath=out/"figure_data"/(name+".csv")
        write_csv(csvpath,rows)
        fig.tight_layout()
        for suffix in ("pdf","svg","png"):
            fig.savefig(dest/(name+"."+suffix),dpi=200,bbox_inches="tight")
        plt.close(fig)
        captions.append(dict(figure=name,caption=caption,source_csv=csvpath.relative_to(out).as_posix(),
            source_sha256=sha(csvpath),config_id=conf["version"],script="study/figures.py",command="python supplementary_study/run.py --suite analysis",
            run_mapping="source cell_id / fit names map to registry and per_run_estimates.csv; fits retain exact seed/cell lists in diagnostics",
            config_sha256=sha(out/"PROTOCOL_FROZEN.json")))
    fig,ax=plt.subplots(figsize=(6,3.2));e2rows=[]
    for H in (2,4,8):
        source=out/f"diagnostics/E2_N32_H{H}_rho1.0.npz"
        arr=np.load(source)["residuals"]
        positive=arr[:,3]>0
        ax.semilogy(arr[positive,0],arr[positive,3],label=f"H={H}")
        for row in arr:
            e2rows.append(dict(cell_id=f"E2_N32_H{H}_rho1.0",round=int(row[0]),global_residual=row[1],local_residual=row[2],control_residual=row[3],
                              raw_source=source.relative_to(out).as_posix(),raw_sha256=sha(source)))
    ax.set(xlabel="Round",ylabel="Absolute translated-control residual",title="Affine matched-initialization check, N=32, rho=1");ax.legend(fontsize=8)
    save(fig,"E2_affine_path_residuals",e2rows,"Representative maximal-shift affine checks use corresponding initial controls and identical additive noises, 2000 rounds per H. These are exact-structure floating-point residuals, not iid statistical observations or a general heterogeneous theorem. Full 24-cell residual arrays and table are retained.",False)
    zero_source=out/"diagnostics/E2_zero_seed10001.npz"
    if zero_source.exists():
        zz=np.load(zero_source);res=zz["global_residual_path"]
        fig,ax=plt.subplots(figsize=(6,3.2));ax.semilogy(np.arange(1,len(res)+1),res)
        ax.axvline(int(zz["burn"]),color="black",ls="--",label="prespecified burn-in")
        ax.set(xlabel="Round",ylabel="Global path difference norm",title="Zero initial controls: N=32, H=4, rho=1");ax.legend(fontsize=8)
        rows=[dict(cell_id="E2_zero_initialization",seed=10001,round=k+1,global_difference=res[k],raw_source=zero_source.relative_to(out).as_posix()) for k in range(len(res))]
        save(fig,"E2_zero_initialization_transient",rows,"Both systems start with zero controls, so their transients need not match. The same-noise coupling's observed late compatibility is an additional finite-run diagnostic, not a machine-precision requirement on independent stationary sample means. All four diagnostic seeds are saved separately.",False)
    b11=[r for r in fitrows if r["experiment"]=="E1a" and r["window"]=="primary" and r["term"]==0]
    if b11:
        fig,axes=plt.subplots(1,2,figsize=(8,3.2))
        for j,ax in enumerate(axes):
            for algorithm in ALGORITHMS:
                rr=sorted([r for r in b11 if r["coordinate"]==j and r["algorithm"]==algorithm],key=lambda r:r["H"])
                if not rr:continue
                ax.errorbar([r["H"]+(-.08 if algorithm=="scaffold" else .08) for r in rr],[r["estimate"] for r in rr],
                    yerr=[[r["estimate"]-r["ci_lower"] for r in rr],[r["ci_upper"]-r["estimate"] for r in rr]],
                    fmt="o-",color=COLORS[algorithm],label=algorithm,capsize=3)
            ax.axhline(theory(2)["B11"][j],color="black",ls="--",label="theoretical B11")
            ax.set(xlabel="Local steps H",ylabel=f"Independent intercept, coordinate {j+1}",xticks=[1,2,4,8])
        axes[0].legend(fontsize=8)
        save(fig,"E1_leading_intercepts",b11,"Independent linear intercepts of (N/gamma) times balance mean at N=32. All four gamma points used separately for each algorithm/H; no B11 subtraction. Bars are nominal run-seed Monte Carlo 95% intervals, not deterministic remainder bounds. H=1 is boundary consistency.")
    control=[r for r in fitrows if r["experiment"]=="E1b" and r["window"]=="primary" and r["term"]==0]
    if control:
        fig,axes=plt.subplots(1,2,figsize=(8,3.2))
        grid=np.linspace(0,1.15,100)
        for j,ax in enumerate(axes):
            rr=sorted([r for r in control if r["coordinate"]==j],key=lambda r:r["H"])
            ax.errorbar([theory(r["H"])["kappa"] for r in rr],[r["estimate"] for r in rr],
                yerr=[[r["estimate"]-r["ci_lower"] for r in rr],[r["ci_upper"]-r["estimate"] for r in rr]],fmt="o",capsize=3,color="#0072B2",label="finite-grid intercept")
            ax.plot(grid,grid*theory(2)["Z_target"][j],"k--",label="controlled target")
            for r in rr:ax.annotate(f"H={r['H']}",(theory(r["H"])["kappa"],r["estimate"]),xytext=(5,5),textcoords="offset points",fontsize=8)
            ax.set(xlabel="kappa(H)",ylabel=f"Control intercept, coordinate {j+1}")
        axes[0].legend(fontsize=8)
        save(fig,"E1_control_kappa",control,"Separate-H OLS intercepts from the complete Cartesian [1,gamma,1/N] grid. Target line is objective-derived; noisy fitted ratios are not imposed. H=4 is retained regardless of discrepancy. Monte Carlo bars do not cover finite-grid remainder.")
    pairs=[r for r in full if r["family"]=="E1" and r["algorithm"]=="matched_difference" and r["H"]>=2 and r["runs"]]
    if pairs:
        fig,axes=plt.subplots(1,3,figsize=(10,3.2))
        colors={32:"#0072B2",64:"#D55E00",128:"#009E73"}
        markers={32:"o",64:"s",128:"^"}
        projected=np.linalg.norm(theory(2)["Z_target"])
        for H,ax in zip((2,4,8),axes):
            for N in (32,64,128):
                rr=sorted([r for r in pairs if r["H"]==H and r["N"]==N and "E1b" in r["roles"]],key=lambda r:r["gamma"])
                if not rr:continue
                k=theory(H)["kappa"]
                ax.errorbar([r["gamma"] for r in rr],[r["signed_projection"]/k for r in rr],
                    yerr=[[(r["signed_projection"]-r["ci_lower"])/k for r in rr],[(r["ci_upper"]-r["signed_projection"])/k for r in rr]],fmt=markers[N]+"-",color=colors[N],label=f"N={N}",capsize=2)
            ax.axhline(projected,color="black",ls="--")
            ax.set(title=f"H={H}",xlabel="Local step size gamma",ylabel="Normalized control projection")
        axes[0].legend(fontsize=8)
        save(fig,"E1_normalized_control_grid",pairs,"Matched balance-mean D divided by kappa(H), projected onto the fixed theoretical direction. Primary Cartesian points shown by N; the horizontal line is -A^{-1}T[C] projected onto itself after normalization. Pointwise seed CIs only. No selection by target inclusion.",False)
        h4=[r for r in pairs if r["H"]==4]
        fig,axes=plt.subplots(1,2,figsize=(8,3.2))
        for N in (32,64,128):
            rr=sorted([r for r in h4 if r["N"]==N],key=lambda r:r["gamma"])
            for j,ax in enumerate(axes):
                if not rr:continue
                ax.errorbar([r["gamma"] for r in rr],[r[f"D_{j}"] for r in rr],
                    yerr=[[r[f"D_{j}"]-r[f"D_{j}_ci_lower"] for r in rr],[r[f"D_{j}_ci_upper"]-r[f"D_{j}"] for r in rr]],fmt=markers[N]+"-",color=colors[N],label=f"N={N}",capsize=2)
                ax.axhline(theory(4)["B20_ctrl"][j],color="black",ls="--")
                ax.set(xlabel="Local step size gamma",ylabel=f"H=4 scaled difference, coordinate {j+1}")
        axes[0].legend(fontsize=8)
        save(fig,"E1_H4_complete_diagnostic",h4,"Every completed H=4 point, including the E1a-only largest gamma, is preserved. The finite-gamma/finite-N displacement and sample uncertainty are shown separately from the target. All primary and nested-window fits are retained in diagnostics.",False)
        fig,ax=plt.subplots(figsize=(6,3.2))
        for H in (2,4,8):
            rr=sorted([r for r in pairs if r["H"]==H and r["N"]==128],key=lambda r:r["gamma"])
            ax.plot([r["gamma"] for r in rr],[r["perpendicular_residual"] for r in rr],"o-",label=f"H={H}")
        ax.axhline(0,color="black",ls="--");ax.set(xlabel="Local step size gamma",ylabel="Perpendicular scaled residual, N=128");ax.legend()
        save(fig,"E1_perpendicular_residuals",pairs,"Perpendicular residuals to the fixed controlled theoretical direction, using all available N=128 cells. Norm-only collapse is not used to hide directional error.",False)
    e3=[r for r in full if r["family"]=="E3" and r["algorithm"] in ALGORITHMS and "allocation" in r["roles"] and r["runs"]]
    for metric,title,error in (("signed_projection","Signed mean displacement",("ci_lower","ci_upper")),
                               ("bias_squared_U","Unclipped squared-bias U-statistic",("bias_squared_ci_lower","bias_squared_ci_upper")),
                               ("raw_variance_trace","Raw parameter variance trace",("raw_variance_trace_ci_lower","raw_variance_trace_ci_upper")),
                               ("total_parameter_MSE","Raw parameter MSE",("total_parameter_MSE_ci_lower","total_parameter_MSE_ci_upper")),
                               ("heldout_log_loss","Per-run averaged-model test log loss",("heldout_log_loss_ci_lower","heldout_log_loss_ci_upper"))):
        if not e3:break
        fig,axes=plt.subplots(1,3,figsize=(10,3.2))
        for regime,ax in zip(("R0","R1","R2"),axes):
            for algorithm in ALGORITHMS:
                rr=sorted([r for r in e3 if r["regime"]==regime and r["algorithm"]==algorithm],key=lambda r:r["N"])
                if not rr:continue
                errs=None
                if error:
                    errs=np.array([[r[metric]-r[error[0]] for r in rr],[r[error[1]]-r[metric] for r in rr]])
                ax.errorbar([r["N"] for r in rr],[r[metric] for r in rr],yerr=errs,fmt="o-",color=COLORS[algorithm],label=algorithm,capsize=3)
            if metric in ("signed_projection","bias_squared_U"):ax.axhline(0,color="black",lw=.8,ls="--")
            ax.set(title=regime,xlabel="Clients N; local batch m=256/N",ylabel=title,xscale="log",xticks=[8,32,128],xticklabels=["8","32","128"])
        axes[0].legend(fontsize=8)
        save(fig,"E3_allocation_"+metric,e3,"a9a fixed total sampling budget B=256 per local-step level, H=4, frozen gamma_base. R0 replicates one empirical objective; R1 is disjoint IID and R2 is simulated label-skew. R1/R2 reference aggregate covariance is measured and can change with N. "+("Squared-bias jackknife-t intervals are nominal and unresolved near zero; negative estimates are not clipped." if metric=="bias_squared_U" else "Direct finite-tail estimates; nominal seed intervals where shown. Parameter variance/MSE uses raw trajectories. Per-run test losses evaluate each run's own averaged model, not a pooled deployable checkpoint."))
    policy=[r for r in full if r["family"]=="E3" and r["algorithm"] in ALGORITHMS and r["N"]==32 and r["partition_seed"] in (0,4101) and r["H"] in (2,4) and r["runs"]]
    if policy:
        for metric,title in (("signed_projection","Signed mean displacement"),("mean_model_training_objective_gap","Mean-model training objective gap"),("heldout_log_loss","Per-run test log loss")):
            fig,axes=plt.subplots(1,3,figsize=(10,3.2))
            base=float(conf["cells"][next(i for i,c in enumerate(conf["cells"]) if c["family"]=="E3")]["gamma"])
            specs=[(4,base,"H4, g"),(4,base/2,"H4, g/2"),(4,base/4,"H4, g/4"),(2,base,"H2, g")]
            for regime,ax in zip(("R0","R1","R2"),axes):
                for algorithm in ALGORITHMS:
                    rr=[next((r for r in policy if r["regime"]==regime and r["algorithm"]==algorithm and r["H"]==H and r["gamma"]==g),None) for H,g,_ in specs]
                    pts=[(i,r) for i,r in enumerate(rr) if r is not None]
                    if pts:ax.plot([i+(-.06 if algorithm=="scaffold" else .06) for i,r in pts],[r[metric] for i,r in pts],"o-",color=COLORS[algorithm],label=algorithm)
                ax.set(title=regime,xticks=list(range(4)),xticklabels=[s[2] for s in specs],ylabel=title)
                ax.tick_params(axis="x",labelrotation=20)
            axes[0].legend(fontsize=8)
            save(fig,"E3_policy_"+metric,policy,"Fixed N=32,m=8 update-policy comparison. Gamma and H vary separately; no imposed gamma-squared scaling or preferred ranking. Full seed intervals/contrasts are in the source tables. Horizons differ according to the frozen global-curvature proxy, so this is not a fixed-cost efficiency claim.")
    save_json(out/"figures/captions_and_provenance.json",captions)
    (out/"figures/CAPTIONS.md").write_text("# Figure captions\n\n"+"\n\n".join(f"## {r['figure']}\n\n{r['caption']}\n\nSource: {r['source_csv']}; config: {r['config_id']}; command: {r['command']}." for r in captions),encoding="utf-8")
