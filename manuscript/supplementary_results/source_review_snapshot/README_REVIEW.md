# Source Review

supplementary_study/ is the actual uncommitted current source, including both kernels, tests,
analysis, plots, scheduler and CLI. delivered_source_snapshot/ preserves the prior delivered ZIP.
available_frozen_source/ contains only obtainable exact freeze-hash matches; see status CSV.
legacy_repository/ includes obtainable legacy code/configs, with short workstream IDs for Windows;
it is separate historical context, NOT imported by the supplementary implementation.
LEGACY_SOURCE_PATH_MAP.csv maps shortened folders back to original import paths if needed.
No dependency environments, datasets, git objects, original result ZIPs or credentials are included.

Install the versions in supplementary_study/requirements.lock into a separate Python environment.
With all review ZIPs extracted into BUNDLE and a fresh output folder NEW_OUTPUT:

```powershell
python SOURCE_REVIEW/tools/replay_review.py --bundle BUNDLE --output NEW_OUTPUT
python SOURCE_REVIEW/tools/restore_aliases.py --bundle BUNDLE
```

Replay calls only existing analysis/plot functions, never CLI training. It checks batch/per-run
means, primary statistics, paired covariance/contrasts, all E1 fits and figures; input reports
remain unchanged. Full data-dependent report reconstruction and LaTeX compilation are not
claimed. See EXPORT_QA.md for executed checks and residual limitations.
