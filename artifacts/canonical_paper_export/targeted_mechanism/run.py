import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
deps=ROOT.parent/'supplementary_study/.deps'
if deps.exists(): sys.path.insert(0,str(deps))
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[name]='1'
os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'local/numba_cache'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'local/mplconfig'))
if __name__=='__main__':
    from targeted.workflow import main
    main()
