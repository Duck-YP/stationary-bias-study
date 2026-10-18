# Current figure/layout audit — 18 October 2026

The current manuscript is `../../../manuscript/main.pdf`, 40 pages, SHA-256
`81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`.
Use `../../FIGURE_REPRODUCTION.md` for the portable release commands.

## Authoring evidence

`BUILD_REPORT.json`, `FINAL_PDF_FONT_AUDIT.json`, `NUMERIC_INVARIANCE.json`,
`ARTIST_GEOMETRY_CHECKS.json`, `VECTOR_DRAWING_BOUNDS.json` and
`INDEPENDENT_QA_REVIEW.md` preserve the completed local presentation audit.
Its numerical checks, 40-page inspection and nine-panel typography measurements
apply to the exact current PDF hash.

The duplicate historical PDFs `BASELINE_main.pdf` (41-page unchanged V2 build)
and `SUPPLIED_OLDER_main.pdf` (stale PDF from the V2 attachment) are omitted
from this publication checkout. `BASELINE_BUILD_REPORT.json` and
`BASELINE_PDF_FONT_AUDIT.json` retain their dated audit evidence. Their hashes
and the packaging decisions appear in `../../manifests/PUBLICATION_SELECTION_OMISSIONS.csv`.

`BEFORE_AFTER.pdf` contains the five figure groups, five matched figure-page
comparisons and every remaining changed page. `COMPARISON_SOURCE_INDEX.json`
retains the original local-handoff path labels as provenance, not executable
release paths. Those labels do not require the full original directory tree.
`COMPARISON_QA.json` records its coverage and visual checks.

`SOURCE_HASH_GUARD.json`, `CHANGE_MANIFEST.json` and `FIGURE_LAYOUT_REVISION.patch`
describe the earlier layout task before this separately authorized export sync.
In particular, their statement that the release tree was unchanged refers to
that earlier task. Original source-guard replay requires the complete local
baseline, including files intentionally omitted from this compact export.
Full-page raster review sets and intermediate layout trials remain local.

## Public-path reproduction

`FIGURE_REPLAY.json` records a new isolated replay using only public figure
inputs and copied plotting code. It checks all nine CSV sidecars, both
provenance records, historical geometry records, PNG bytes/pixels, PDF operators,
media boxes, normalized font names and 216-dpi rendered pixels. PDF byte
differences caused by metadata or font subset names are reported separately.

`PUBLIC_BUILD_REPORT.json` records a new clean build from the public manuscript.
`RECOMPILE_COMPARE.json` compares that build against the distributed PDF:
all 40 rendered pages at 120 dpi and extracted text match, while PDF hashes can
differ through build metadata.

The existing Python/TeX environment was reused. This is a saved-data and clean
document reproduction check, not a fresh environment installation or a rerun
of experiments, fitting or resampling. The aggregate current validation receipt
is `../../VALIDATION_RECEIPT.md`; prior receipts remain dated historical evidence.
