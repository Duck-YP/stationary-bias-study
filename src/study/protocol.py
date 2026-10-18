import json
import time
from pathlib import Path
import numpy as np
from .data import save_json,sha,partition,partition_diagnostics,sparse_logistic
from .model import theory


def source_hashes(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted((root/"study").glob("*.py"))} | {"run.py":sha(root/"run.py"),"requirements.lock":sha(root/"requirements.lock")}


def verify_frozen(root,out,conf):
    actual=source_hashes(root)
    # Analysis/report edits do not change training. Kernel/model/data/engine edits do.
    for file in ("study/kernels.py","study/model.py","study/data.py","study/engine.py"):
        if actual[file]!=conf["source_hashes"][file]:
            raise RuntimeError(f"Frozen production source changed: {file}; preserve old results and explicitly version a new protocol")
    assert sha(out/"data/training_csr.npz")==conf["objective_hash"]
    assert sha(out/"reference_optimizers.npz")==conf["reference_hash"]


def freeze(root,out,design,Z,y,ref):
    path=out/"PROTOCOL_FROZEN.json"
    if path.exists():
        print("Existing protocol preserved; use a distinct version for extensions")
        return
    pilots=json.loads((out/"diagnostics/pilot_summary.json").read_text())
    if not all(r["finite"] and r["max_relative_zero_sum"]<1e-10 for r in pilots["runs"]):
        raise RuntimeError("Pilot numerical implementation gate failed; do not freeze")
    assert json.loads((out/"diagnostics/E2_gate.json").read_text())["status"]=="PASSED"
    predicted={}
    for fam in ("E1","E3"):
        rps=[r["rounds_per_second"] for r in pilots["runs"] if r["cell"]["family"]==fam]
        predicted[fam]=float(np.median(rps))
    specs=[]; metadata=[]
    for c in design:
        c=dict(c)
        mu=theory(c["H"])["mu"] if c["family"]=="E1" else .01
        tau=int(np.ceil(1/(mu*c["gamma"]*c["H"])))
        representative=(c["family"]=="E1" and c["H"]==4 and c["N"]==64 and c["gamma"]==1/256) or (
            c["family"]=="E3" and c["regime"]=="R2" and c["N"]==32 and c["H"]==4 and c["gamma"]==float(ref["gamma_base"])/4)
        c["schedule"]=dict(tau0=tau,burn=50*tau,batch_length=10*tau,batches=133 if representative else 64,primary_batches=64,
                           sensitivity="primary first64; burn2x batches5:69; tail2x first128; combined batches5:133" if representative else "none")
        c["estimated_single_run_seconds"]=float((c["schedule"]["burn"]+c["schedule"]["batches"]*c["schedule"]["batch_length"])/predicted[c["family"]])
        if c["family"]=="E1":
            c["gamma_over_gamma_imp"]=c["gamma"]/theory(c["H"])["gamma_imp"]
        else:
            mem=partition(y,c["N"],c["regime"],c["partition_seed"])
            dest=out/"diagnostics"/(c["id"]+"_partition.npz")
            # Each configuration retains memberships and full centered covariance matrices.
            diagnostic=partition_diagnostics(Z,y,ref["x_ref"],ref["A_ref"],mem,c["m"],dest)
            metadata.append(dict(cell_id=c["id"],regime=c["regime"],partition_seed=c["partition_seed"],**diagnostic))
            print("PARTITION",c["id"],"G",diagnostic["G"],"Vbar",diagnostic["Vbar_trace"],flush=True)
        specs.append(c)
    write_info=dict(version="independent-supplement-v1",frozen_date="2026-10-09",source_hashes=source_hashes(root),
        brief_sha256=sha(root/"brief/CODEX_PROMPT.md"),objective_hash=sha(out/"data/training_csr.npz"),
        reference_hash=sha(out/"reference_optimizers.npz"),production_seeds=list(range(20001,20013)),pilot_seeds=list(range(10001,10005)),
        data_seed=20261009,partition_seeds=[4101,4102,4103],cells=specs,optional_gamma_1024_extension_enabled=False,
        E3_shadow_enabled=False,E3_primary_estimator="direct mean; no pilot-validated shadow process",
        E1_primary_estimator="exact nonlinear balance, raw mean cross-check",
        E1a_primary_fit="separate algorithm/H linear intercept against gamma; all four points; no B11 subtraction",
        E1a_secondary_fit="omit largest gamma nested window",
        E1b_primary_fit="separate H coordinate OLS [1,gamma,1/N], all Cartesian points",
        E1b_secondary_fit="omit largest gamma or omit N=32, explicitly nested sensitivity",
        E1b_contrast="beta0(H4)-3.5*beta0(H2); exact kappa(4)/kappa(2)=3.5",
        resampling="independent paired seed vectors as bootstrap units; all cells resampled together; 2000 bootstrap draws seed=61009",
        ci="pointwise nominal Student-t 95%; coordinate families Bonferroni; bootstrap fits; no deterministic error coverage",
        multiplicity={"E1a_intercepts_coordinates":16,"E1b_intercepts_coordinates":6,"E3_signed_projections":sum(c["family"]=="E3" for c in specs)*3},
        E3_projection=ref["direction"],E3_projection_scope="objective-derived descriptive direction; not homogeneous additive theorem target",
        precision_targets={"E1_B11_absolute_coordinate_halfwidth":.005,"E1_control_relative_direction_halfwidth":.10,"E3_signed_projection_absolute_halfwidth":1e-4},
        stationarity="paired run first-half/last-half contrasts; adjusted nominal CI; representative2x burn/tail; absence of significance is not a mixing certificate",
        U_statistic="unclipped cross-run squared displacement, jackknife-t CI; near-zero inference unresolved; Gaussian quadratic zero-bias calibration",
        pilot= dict(cells=pilots["pilot_cells"],runs=pilots["completed_runs"],median_rounds_per_second=predicted,
            horizon_rationale="baseline global-curvature proxy retained; pilot too short to justify reducing 50*tau burn or 64*10*tau tail"),
        run_budget_rule="fixed horizons; wall-clock checkpoints preserve status RESOURCE_LIMITED, never scientific rejection",
        estimated_cpu_hours=sum(c["estimated_single_run_seconds"]*12 for c in specs)/3600)
    save_json(path,write_info); save_json(out/"configs/production_v1.json",write_info)
    from .engine import write_csv
    write_csv(out/"tables/partition_diagnostics.csv",metadata)
    print("FROZEN",len(specs),"cells",write_info["estimated_cpu_hours"],"predicted serial CPU hours",flush=True)
