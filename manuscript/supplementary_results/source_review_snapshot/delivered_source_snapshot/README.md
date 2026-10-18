# Independent supplementary SCAFFOLD/FedAvg study

This directory is independent of the cloned repository's existing workstreams. It implements the 2026-10-09 attached brief from zero, without importing historical simulation kernels or artifacts. The manuscript and historical H=4 evidence are preserved.

Python 3.12, NumPy/SciPy and Numba float64 CPU kernels are used. `run.py` loads locally isolated dependencies from `.deps` when present. Install the locked dependencies with `python -m pip install --target supplementary_study/.deps -r supplementary_study/requirements.lock`.

The frozen design contains 34 controlled E1 cells and 35 a9a E3 cells (including H=1 controls and partition sensitivities), 12 independent paired production seeds per cell. E1a/E1b overlap is deduplicated. Seven independent pilot cells use four different seeds. E2 has 24 affine matched-initialization cells, each 2000 rounds, plus a separate zero-control transient diagnostic. Figures and tables are rebuilt from stored summaries rather than rerunning simulations.

Run `python supplementary_study/run.py --suite E0`, then the explicit commands in `results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF/RUN_COMMANDS.md`. A finite wall budget causes cooperative checkpointing, not a scientific rejection. Check `EXPERIMENT_REGISTRY.csv` for actual completion and inference statuses.

The returned handoff and source ZIPs are under `supplementary_study/results/`. New source/data/preprocessing/protocol identities and seed lists are saved. Exact-coordinate checks, coefficient fits and real-data implications have distinct scientific scopes.
