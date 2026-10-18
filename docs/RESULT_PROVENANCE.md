# Result provenance

## Scientific authority

The authority is the finalized 18 October 2026 figure/layout revision of the supplied V2 manuscript: `manuscript/main.pdf`, 40 pages, SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. It has five numbered figures comprising nine panels and 22 active numbered tables. An unused appendix file contains another table environment and is not part of the active paper.

The V2 source archive is identified in `docs/manifests/CURRENT_MANUSCRIPT_SYNC.json`. Its supplied PDF was older than those sources; the final layout was based on a clean 41-page compilation of V2, then compiled to 40 pages. Publication packaging preserves the finalized manuscript, final panels and scientific values. arXiv:2608.26765 currently serves an earlier version and is not used to select the new numerical evidence.

## Independent evidence generations

Here `canonical/` abbreviates `artifacts/canonical_paper_export/`.

| Manuscript evidence | Lineage and retained scope |
| --- | --- |
| Individual/matched coefficient experiments; Figures 1, 2, 5; Tables 2, 11–14, 18 | Original workstreams based on repository commit `7f6de2cea1f20db958163af0c4e020ae57ff2b65`. Source remains under `src/stationary_bias/`; compact results under `canonical/original/`. Primary H=4 differences, smaller-step diagnostics and negative controls remain distinct. |
| Independent Cartesian-grid, affine and logistic studies; Tables 3, 5, 15, 19–21; Figure 3 | Earlier integrated supplementary study, source under `src/study/`, results under `canonical/supplementary/`. The frozen registry retains 69 cells and twelve production seeds per cell. Exact recovered freeze-time source is distinguished from later delivered analysis/reporting source. |
| Temporal averaging; Section 6.4, Figure 4, Table 22 | `manuscript/supplementary_results/E4/`: nine shared-objective configurations, twelve paired seeds and seven windows, yielding 1,512 averaged model outputs. Saved arrays, intervals, protocols and source are retained. Two later pilots are separate; the planned 48-seed extension was not executed. |
| Directional proxy; Section 6.5, Table 6, Appendix C.4.4 | `manuscript/supplementary_results/E5/`: saved vectors, all-cell/window summaries, alternative directions and sensitivities, with the post-hoc specification. This analysis uses saved temporal-averaging outputs rather than new training. |
| Contraction/noise-law mechanisms; Section 6.2.7, Tables 4, 10, 16, 17 | Imported `TARGETED_MECHANISM_REVIEW.zip` under `canonical/targeted_mechanism/`: 16 pilot and 288 production paired runs across 24 cells, frozen design, model/kernel certificates, all primary/sensitivity outputs and 32 auxiliary figures. |
| Separate targeted implementation and review | `SOURCE_TARGETED_MECHANISM.zip` under `src/targeted_mechanism_snapshot/`; supplied independent review/audit under `docs/targeted_mechanism/`. Their historical receipts are not claimed as newly executed production or audit runs. |

The targeted primary tables select `canonical/targeted_mechanism/results/primary_family_36.csv`; all 36 scalar selections and restricted-grid/window sensitivities remain available. The imported independent audit reports 18,576 scalar comparisons at its recorded tolerances. It required an original extraction layout and raw batches; retaining that receipt does not imply a complete public replay.

## Copies, variants and omissions

The manifests under `docs/manifests/` distinguish original exact copies, publication copies, targeted copies, documented metadata variants and omissions. `PUBLICATION_SELECTION_OMISSIONS.csv` records the publication cleanup with hashes and reasons. `docs/SOURCE_MANIFEST.csv` describes the current publication file inventory. Historical hashes embedded in imported records retain their original scope, while the current outer manifests identify public bytes.

Machine-local metadata paths were normalized during earlier export; original and exported hashes identify those variants. The pilot run-manifest adaptation changes its `source_path` metadata only. Numerical CSV/NPZ values, configurations, seeds, fits and confidence families are not changed. Internal authoring prompts, unrelated future-roadmap notes and duplicate drafts are omitted from the publication tree; scientific design/reference checks are retained.

Large datasets, partition matrices, raw batch/bootstrap archives and checkpoints are outside the compact checkout. [Data and archives](DATA_AND_ARCHIVES.md) records names, checksums, scientific roles, retained derivatives and public availability. Some freeze-time source and initial-state/noise statistics were never recovered. These limitations are explicit in the [scope document](REPRODUCIBILITY_SCOPE.md), rather than filled with invented implementations.

## Presentation and table fidelity

The final figure renderers read frozen outputs and saved fits. All nine numerical sidecars remain byte-identical to the clean V2 baseline. [Figure provenance](FIGURE_PROVENANCE.md) records row selection, exact columns and display transformations.

The table generator reconstructs values from saved scientific outputs and preserves the paper. Its per-table comparison record identifies support and discrepancies; unresolved Table 18 historical reconstruction is not silently corrected. Consult the [matrix](MANUSCRIPT_REPRODUCIBILITY_MATRIX.md) and current [validation receipt](VALIDATION_RECEIPT.md). Active computational exhibits are distinguished from analytic/protocol tables.

Older manuscript-page counts, font audits, and replay counts in dated receipts describe their own versions. The final layout audit is tied to the exact PDF hash above; the current publication checks are reported separately. Numerical consistency demonstrates correspondence to saved evidence, not stationary convergence or an independent proof of the analytical results.
