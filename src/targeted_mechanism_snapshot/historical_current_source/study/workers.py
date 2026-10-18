"""Independent processes; a run keeps the same keyed random stream at any job count."""
from pathlib import Path
from .engine import load_data,run_one

_CACHE=None


def initialize(out):
    global _CACHE
    _CACHE=load_data(Path(out))


def execute(task):
    cell,seed,out,resume,deadline,memory=task
    Z,y,ref=_CACHE
    complete=run_one(cell,seed,"production",cell["schedule"],Path(out),Z,y,ref,resume,deadline,memory)
    return cell["id"],seed,complete
