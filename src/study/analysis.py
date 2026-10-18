import csv
import json
import math
import shutil
import zipfile
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from .data import save_json,sha,sparse_logistic,read_libsvm
from .engine import write_csv,ALGORITHMS,load_data
from .model import theory


def iact_proxy(series):
    x=np.asarray(series)-np.mean(series)
    if x@x==0: return 1.
    result=1.
    for lag in range(1,min(len(x)//2,32)):
        rho=float(x[:-lag]@x[lag:]/(x@x))
        if rho<=0: break
        result+=2*rho
    return result


def interval(values,family=1):
    a=np.array(values,dtype=float); n=len(a)
    mean=a.mean(0)
    if n<2: return mean,np.full_like(mean,np.nan),np.full_like(mean,np.nan),np.full_like(mean,np.nan)
    se=a.std(0,ddof=1)/np.sqrt(n)
    hw=student_t.ppf(1-.05/(2*family),n-1)*se
    return mean,mean-hw,mean+hw,hw


def ustat(B):
    n=len(B)
    if n<2: return float("nan"),float("nan"),float("nan")
    def stat(a):
        r=len(a)
        return float((a.sum(0)@a.sum(0)-np.sum(a*a))/(r*(r-1)))
    u=stat(B)
    if n<3:return u,float("nan"),float("nan")
    leave=np.array([stat(np.delete(B,k,axis=0)) for k in range(n)])
    se=np.sqrt((n-1)/n*np.sum((leave-leave.mean())**2))
    hw=student_t.ppf(.975,n-1)*se
    return u,u-hw,u+hw


def analyze(root,out):
    # Implemented below with production-only inference and transparent missing cells.
    from .report import build_report
    return build_report(root,out)


def package(root,out):
    from .protocol import source_hashes
    manifest=source_hashes(root)
    manifest.update({p.relative_to(root).as_posix():sha(p) for p in sorted((root/"brief").glob("*")) if p.is_file()})
    manifest["README.md"]=sha(root/"README.md")
    manifest["Run-Study.ps1"]=sha(root/"Run-Study.ps1")
    manifest["configs/production_v1.json"]=sha(out/"PROTOCOL_FROZEN.json")
    save_json(out/"SOURCE_MANIFEST.json",dict(files=manifest,source_scope="independent supplementary implementation; legacy repository code not imported",
         imported_repository_base_commit="7f6de2c",post_freeze_changes="scheduler concurrency, logging, reporting, and additional tests; frozen numerical kernels/model/data/engine unchanged"))
    raw={p.relative_to(out).as_posix():sha(p) for p in sorted((out/"raw").rglob("*")) if p.is_file()}
    save_json(out/"raw_manifest.json",raw)
    evidence={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name!="ARTIFACT_MANIFEST.json" and not p.name.startswith("command_")}
    save_json(out/"ARTIFACT_MANIFEST.json",evidence)
    handoff=root/"results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF.zip"
    with zipfile.ZipFile(handoff,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(out.rglob("*")):
            if p.is_file(): z.write(p,"SUPPLEMENTARY_EXPERIMENTS_HANDOFF/"+p.relative_to(out).as_posix())
        for p in (root/"data").glob("a9a*"):
            z.write(p,"SUPPLEMENTARY_EXPERIMENTS_HANDOFF/data/source/"+p.name)
    source=root/"results/source.zip"
    with zipfile.ZipFile(source,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file():continue
            rel=p.relative_to(root)
            if rel.parts[0] in (".deps",".mplconfig","results","data") or "__pycache__" in rel.parts: continue
            z.write(p,"supplementary_study/"+rel.as_posix())
        z.write(out/"PROTOCOL_FROZEN.json","supplementary_study/configs/production_v1.json")
    with zipfile.ZipFile(handoff) as z: assert z.testzip() is None
    with zipfile.ZipFile(source) as z: assert z.testzip() is None
    print("PACKAGED",handoff,sha(handoff),source,sha(source),flush=True)
