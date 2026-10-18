"""Standalone supplementary study entry point; no imported legacy kernels."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT))
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

if __name__ == "__main__":
    import json
    import time
    logdir=ROOT/"results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF/logs"
    logdir.mkdir(parents=True,exist_ok=True)
    record=dict(start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),argv=sys.argv,python=sys.executable)
    log=(logdir/("command_"+str(time.time_ns())+".json"))
    log.write_text(json.dumps(record,indent=2),encoding="utf-8")
    from study.cli import main
    try:
        main()
    except BaseException as error:
        record.update(outcome="PROCESS_ERROR",error=repr(error))
        raise
    else:
        record["outcome"]="RETURNED; scientific/execution status is in the registry"
    finally:
        record["end_utc"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        log.write_text(json.dumps(record,indent=2),encoding="utf-8")
