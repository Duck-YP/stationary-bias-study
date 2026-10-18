# Current publication synchronization and validation receipt

Validated on **2026-10-15** against the supplied integrated manuscript.
The prior receipt is retained verbatim at
`docs/figure_audit/VALIDATION_RECEIPT_20261009.md`.

## Current manuscript and imported evidence

- Supplied archive: `SCAFFOLD_Targeted_Mechanism_Integrated_20261015.zip`, SHA-256
  `10ec90589e0f1ba73926cea7d6b17e03e3885191a313af109f46acf398cf41cc`.
- Current `manuscript/main.pdf`: **40 pages**, SHA-256
  `1bea9883e8f828f3a4c7029ed26fdcced6808d3420470a09ccbcdd346232be1f`.
  Static TeX asset closure passed for 14 active TeX files and nine graphics.
  This verifies the supplied PDF and source assets; no new TeX compilation or
  final-font audit was performed.
- Publication-copy manifest: **508 files**, with all available local source
  hashes verified, including archive members. Eleven documented metadata
  variants preserve scientific values. The E4 pilot CSV changes only
  `source_path`; the two omissions are the expanded source ZIP and historical
  machine-local run commands.
- Targeted-copy manifest: **548 files**, comprising the complete 440-file review,
  86-file source package, 20-file independent audit and two supplied documents.
  All imported archive-member source hashes were independently compared with
  the supplied archives. Twenty-six metadata variants replace machine-local
  path strings only; numerical results and scientific kernels remain exact.
- E4 contains all 35 integrated files; E5 contains all 31. The source snapshots
  retain their provenance scope and original-layout dependencies.
- The separate workspace master manuscript remains unchanged: 252 files
  matched its pre-export hashes. The project README now links to this export.

## Checks executed during this update

- `python -B scripts/validate_release.py`: **PASS**, including final manifest
  closure after documentation changes. Original 339 exact-copy files, 69
  earlier production cells and all 1,656 algorithm-level rows remain intact.
- Targeted completeness: 24 configurations, 288 paired production runs, 3,456
  per-run scalar records, 36 primary summaries, all four estimator/grid families
  (144 summaries), and 5,184 finite-window identity rows. Unfavorable and
  precision-insufficient outcomes are retained.
- Targeted manuscript transcription: all 36 selections and **113 displayed
  numerical tokens** match their saved CSV entries and manuscript rows.
- E4/E5 checker: **1,507 checks**, **221,919 scalar comparisons**, zero failures;
  maximum absolute difference `1.7486012637846216e-15`. It uses saved models,
  vectors and inference arrays, with no original-batch reconstruction.
  Full receipt: `docs/manifests/CURRENT_E4_E5_SAVED_CHECK.json`.
- `python -B -m pytest -q -p no:cacheprovider`: **3 passed in 7.21 seconds**.
  These tests check release integrity and bounded coefficient/Lyapunov identities.
- Independent structured-file scan: all 349 Python files parse, 157 JSON files
  parse, and 311 NPZ containers pass CRC checks.
- Git-byte audit refreshed: 1,015 text files examined, 648 containing historical
  CRLF bytes; nine representative text-type filter/no-filter hashes match.
  No Git index writes, staging or commit were performed.

Observed environment: Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.1,
pytest 9.1.1, using already-installed workspace dependencies. A fresh combined
editable installation was not tested.

## Scope and closure

The complete manifest contains **1,431 files, 92,548,820 bytes**, excluding only
itself and this receipt; runtime caches are not part of the export. Source,
publication and targeted copies have separate provenance manifests. Current
manuscript identity is recorded in `docs/manifests/CURRENT_MANUSCRIPT_SYNC.json`.

Old 33-page manuscript, four-page gallery, seven-panel replay and 14-inclusion
font receipts remain historical. The supplied independent targeted audit is
also an imported review, not a newly executed full audit. These checks establish
artifact fidelity and saved-result correspondence, rather than theorem
correctness, stationarity or acceptance of scientific targets.

No production simulation, training, optimizer fitting, estimator refit,
bootstrap resampling or GitHub push was performed during synchronization.
