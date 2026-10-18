import argparse
import contextlib
import io
import json
import os
import platform
import sys
import time
from pathlib import Path
import numpy as np
from .data import prepare,save_json,sha
from .engine import e2,load_data,cells,run_one,write_csv
from .model import theory

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF"


def environment():
    import importlib.metadata as md
    import psutil
    packages={p:md.version(p) for p in ("numpy","scipy","numba","llvmlite","matplotlib","pytest","psutil","threadpoolctl")}
    text=json.dumps(dict(python=sys.version,executable=sys.executable,platform=platform.platform(),cpu_count=os.cpu_count(),
         cpu=platform.processor(),memory_gb=psutil.virtual_memory().total/1024**3,
         free_disk_gb=psutil.disk_usage(str(ROOT)).free/1024**3,packages=packages,
         backend="Numba float64 CPU; no fastmath; BLAS threads=1; no GPU used"),indent=2)
    (OUT/"ENVIRONMENT.txt").write_text(text,encoding="utf-8")
    (ROOT/"requirements.lock").write_text("\n".join(f"{p}=={v}" for p,v in packages.items())+"\n",encoding="ascii")
    return text


def tests():
    import pytest
    capture=io.StringIO()
    with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
        tempbase=OUT/"tests/tmp"/str(time.time_ns())
        tempbase.parent.mkdir(parents=True,exist_ok=True)
        status=pytest.main([str(ROOT/"study/tests.py"),"-v","--tb=short","-o","addopts=","-o","testpaths=","-p","no:cacheprovider","--basetemp",str(tempbase)])
    text=capture.getvalue()
    stamp=time.strftime("%Y%m%d_%H%M%S")
    (OUT/"tests"/f"test_report_{stamp}.txt").write_text(text,encoding="utf-8")
    (OUT/"tests/test_report.txt").write_text(text,encoding="utf-8")
    print(text,flush=True)
    save_json(OUT/"tests/gate.json",dict(status="PASSED" if status==0 else "FAILED",report_sha256=sha(OUT/"tests/test_report.txt")))
    if status: raise SystemExit(status)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--suite",choices=["E0","data","E2","E2zero","deterministic","roundoff","pilot","freeze","E1","E3","analysis","package","all"],default="E0")
    parser.add_argument("--config",type=Path)
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--max-wall-hours",type=float,default=float("inf"))
    parser.add_argument("--max-memory-gb",type=float,default=4.)
    parser.add_argument("--jobs",type=int,default=1)
    parser.add_argument("--dry-run",action="store_true")
    parser.add_argument("--production",action="store_true")
    args=parser.parse_args()
    for folder in ("data","diagnostics","configs","logs","tests","tables","latex","raw","figures/main_candidates","figures/appendix_candidates","figure_data"):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    if args.jobs<1 or args.jobs>(os.cpu_count() or 1):
        raise SystemExit("--jobs must be between 1 and logical CPU count")
    if args.dry_run:
        print("DRY RUN: no simulation, optimizer, or test execution")
        if (OUT/"PROTOCOL_FROZEN.json").exists():
            conf=json.loads((OUT/"PROTOCOL_FROZEN.json").read_text())
            print(json.dumps(conf,indent=2))
        return
    if args.suite=="E0":
        print(environment()); tests(); return
    if args.suite=="data":
        import urllib.request
        from datetime import datetime,timezone,timedelta
        acquisitions=[]
        (ROOT/"data").mkdir(exist_ok=True)
        for name in ("a9a","a9a.t"):
            target=ROOT/"data"/name
            if not target.exists():
                url="https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/"+name
                try:
                    with urllib.request.urlopen(url,timeout=60) as response, target.open("wb") as file:
                        import shutil
                        shutil.copyfileobj(response,file)
                except Exception as error:
                    save_json(OUT/"logs/data_unavailable.json",dict(url=url,error=str(error),execution_status="DATA_UNAVAILABLE"))
                    raise
                acquisitions.append(dict(url=url,sha256=sha(target),acquired_date=datetime.now(timezone(timedelta(hours=8))).date().isoformat()))
        if acquisitions:save_json(OUT/"logs/reproduction_data_acquisitions.json",acquisitions)
        print(prepare(ROOT,OUT/"data"));
        for name in ("DATA_MANIFEST.json","reference_optimizers.npz","optimizer_certificates.json"):
            import shutil
            shutil.copy2(OUT/"data"/name,OUT/name)
        return
    if args.suite=="E2":
        require_gate(); e2(OUT); return
    if args.suite=="E2zero":
        require_gate()
        from .checks import zero_initialization
        zero_initialization(OUT)
        return
    if args.suite=="deterministic":
        require_gate()
        from .checks import deterministic_baselines
        deterministic_baselines(OUT)
        return
    if args.suite=="roundoff":
        from .accuracy import roundoff_audit
        roundoff_audit(OUT)
        return
    if args.suite in ("analysis","package"):
        from .analysis import analyze,package
        analyze(ROOT,OUT)
        if args.suite=="package": package(ROOT,OUT)
        return
    if args.suite=="all":
        raise SystemExit("Use explicit stage commands in RUN_COMMANDS.md; no hidden stage transitions.")
    require_gate()
    Z,y,ref=load_data(OUT)
    design=cells(float(ref["gamma_base"]))
    deadline=time.monotonic()+args.max_wall_hours*3600
    if args.suite=="pilot":
        pilot=[c for c in design if (c["family"]=="E1" and c["N"]==32 and c["H"] in (2,4,8) and c["gamma"]==1/128) or
               (c["family"]=="E3" and c["N"]==32 and c["partition_seed"] in (0,4101) and c["H"]==4 and (c["gamma"]==float(ref["gamma_base"]) or (c["regime"]=="R2" and c["gamma"]==float(ref["gamma_base"])/4)))]
        summaries=[]
        for c in pilot:
            mu=theory(c["H"])["mu"] if c["family"]=="E1" else .01
            tau=int(np.ceil(1/(mu*c["gamma"]*c["H"])))
            schedule=dict(tau0=tau,burn=10*tau,batch_length=2*tau,batches=16,scope="engineering pilot; not stationary production inference")
            for seed in range(10001,10005):
                print("PILOT",c["id"],seed,schedule,flush=True)
                complete=run_one(c,seed,"pilot",schedule,OUT,Z,y,ref,args.resume,deadline,args.max_memory_gb)
                if not complete: print("CHECKPOINT",c["id"],seed,flush=True); return
                r=dict(np.load(OUT/"raw/pilot"/c["id"]/f"seed_{seed}/result.npz"))
                direction=np.array(theory(4)["B11"]) if c["family"]=="E1" else ref["direction"]
                direction/=np.linalg.norm(direction)
                bm=r["batch_means"] @ direction
                from .analysis import iact_proxy
                rho=[iact_proxy(bm[:,a]) for a in (0,1)]
                summaries.append(dict(cell=c,seed=seed,schedule=schedule,rounds=int(r["rounds"]),elapsed=float(r["elapsed"]),
                    rounds_per_second=float(r["rounds"])/float(r["elapsed"]),batch_projection_iact_proxy=rho,
                    max_zero_sum=float(r["max_zero_sum"]),max_relative_zero_sum=float(r["max_relative_zero_sum"]),
                    finite=bool(np.isfinite(r["mean"]).all()),raw_mean=r["raw_mean"],primary_mean=r["mean"]))
        save_json(OUT/"diagnostics/pilot_summary.json",dict(pilot_cells=len(pilot),completed_runs=len(summaries),runs=summaries,
            test_set_used=False,production_seeds_disjoint=True))
        return
    if args.suite=="freeze":
        from .protocol import freeze
        freeze(ROOT,OUT,design,Z,y,ref); return
    if not args.production:
        raise SystemExit("Production execution requires --production and a frozen protocol")
    conf=json.loads((args.config or OUT/"PROTOCOL_FROZEN.json").read_text())
    from .protocol import verify_frozen
    verify_frozen(ROOT,OUT,conf)
    chosen=[c for c in conf["cells"] if c["family"]==args.suite]
    # Run main contrasts before controls/sensitivities, as specified by the brief.
    chosen.sort(key=lambda c: ("partition_sensitivity" in c["roles"],"negative_control" in c["roles"]))
    if args.jobs>1:
        from concurrent.futures import ProcessPoolExecutor,as_completed
        from .workers import initialize,execute
        tasks=[(c,seed,str(OUT),args.resume,deadline,args.max_memory_gb/args.jobs) for c in chosen for seed in conf["production_seeds"]
               if not (OUT/"raw/production"/c["id"]/f"seed_{seed}/result.npz").exists()]
        with ProcessPoolExecutor(max_workers=args.jobs,initializer=initialize,initargs=(str(OUT),)) as pool:
            futures=[pool.submit(execute,task) for task in tasks]
            for future in as_completed(futures):
                id,seed,complete=future.result()
                print("COMPLETED" if complete else "CHECKPOINT",id,seed,flush=True)
                if not complete:
                    for pending in futures: pending.cancel()
                    return
        return
    for cell in chosen:
        if cell["family"]!=args.suite: continue
        for seed in conf["production_seeds"]:
            print("PRODUCTION",cell["id"],seed,flush=True)
            complete=run_one(cell,seed,"production",cell["schedule"],OUT,Z,y,ref,args.resume,deadline,args.max_memory_gb)
            if not complete: print("CHECKPOINT",cell["id"],seed,flush=True); return


def require_gate():
    gate=json.loads((OUT/"tests/gate.json").read_text())
    if gate["status"]!="PASSED": raise SystemExit("E0 gate not passed")
