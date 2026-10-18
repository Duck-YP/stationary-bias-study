# V2 synchronization and validation receipt

Validated on **2026-10-18**, version `20261018_V2`.

## Source synchronization

The source is `Characterizing_Client_Independent_Stationary_Bias_for_SCAFFOLD_and_FedAvg_in_Federated_Learning_V2.zip`, SHA-256
`bf0ddf18830e323bdabb57e12effb959d21d8c9f76f93fc3b2d68df16f9f8f70`.
All 251 supplied manuscript files match the local master byte-for-byte:
12 TeX files updated, 239 files unchanged, no new files. The existing generated
`main.bbl` is retained and documented separately; it is absent from V2 and
`references.bib` is unchanged. Existing manuscript and release files were backed up.

The public copy has 508 publication-manifest entries with eleven documented
metadata variants and two omissions. All scientific source and data are copied
from their stated sources; no new manuscript wording or scientific analysis was
authored during this sync. The three embedded targeted archives have the same
hashes as the previously imported materials and were not reimported.

## Supplied PDF is an older build

The V2 archive contains the same 40-page `main.pdf` as the October 15 delivery,
SHA-256 `1bea9883e8f828f3a4c7029ed26fdcced6808d3420470a09ccbcdd346232be1f`.
It does not reflect the revised TeX: the PDF still includes Discussion, while
V2 disables that input, and its main-results wording differs. The PDF is
preserved exactly as supplied. **No V2 compilation or source/PDF correspondence
validation is claimed.**

The V2 active source graph contains 13 TeX files and nine graphics; all referenced
assets exist. The prior synchronization and validation receipts are preserved in
`docs/manifests/ARCHIVED_MANUSCRIPT_SYNC_20261015.json` and
`docs/figure_audit/VALIDATION_RECEIPT_20261015.md`. Imported revision notes and
older build/font receipts retain their historical scope.

## Checks performed

- Complete release validator: **PASS**, covering 1,433 manifest files and
  92,560,151 bytes. The manifest excludes itself and this receipt; runtime caches
  are excluded. All 508 publication source hashes were checked.
- Existing bounded tests: **3 passed in 8.30 seconds**.
- Targeted transcription: all 36 selections and 113 displayed numerical tokens
  match saved results. Completeness checks retain all 24 configurations, 288
  paired production runs, 36 primary summaries and four estimator/grid families,
  including unfavorable and precision-insufficient results.
- Git-byte audit: 1,017 text files examined, 651 with CRLF; nine representative
  filter/no-filter comparisons passed without Git index writes.

The earlier E4/E5 saved-data check is retained as a historical receipt; it was not
rerun because those files are unchanged. These checks establish file fidelity,
saved-result correspondence and source asset closure, not the correctness of
new prose/proofs or correspondence of the supplied older PDF to V2 source.

No experiment, fitting, bootstrap resampling, LaTeX build, commit or GitHub push
was performed during this synchronization.
