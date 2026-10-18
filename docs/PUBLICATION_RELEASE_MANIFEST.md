# Publication release manifest

This repository preserves the finalized manuscript and frozen scientific evidence while adding portable publication entry points and audit documentation. The destination is [Duck-YP/stationary-bias-study](https://github.com/Duck-YP/stationary-bias-study), exactly as stated in the manuscript. Repository visibility is preserved; documentation and source availability do not imply anonymous access. The publication report records the actual branch, pushed commit and remote verification.

## Included scientific material

- The final 40-page manuscript, active LaTeX/bibliography, nine vector panels and numerical sidecars.
- Original scalar, 2D and 5D coefficient implementations; independent supplementary implementations; and the separate targeted-model reference/compiled path.
- Frozen protocols, recorded seeds, partitions specifications, schedules, historical environments and source recovery records.
- Compact original, independent-grid, affine and logistic results, including unfavorable or imprecise outcomes.
- Temporal-averaging and full-vector proxy saved arrays, intervals, protocols, diagnostic sensitivities and source snapshots.
- Targeted cancellation/noise-law model certificates, all 24 cells, twelve production pairs per cell, 36 primary summaries, full/restricted-grid results and 32 auxiliary figures.
- Saved-data figure/table entry points, bounded implementation example, meaningful tests, release integrity checks and per-exhibit reproducibility status.

The authoritative manuscript SHA-256 is `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. Scientific source, numerical outputs, final figures and manuscript are frozen during this publication task. No full experimental campaign, coefficient refit or bootstrap rerun is performed.

## Inventory and checksums

| Record | Purpose |
| --- | --- |
| [SOURCE_MANIFEST.csv](SOURCE_MANIFEST.csv) | Current publication files and SHA-256 inventory. |
| `manifests/EXACT_COPY_MANIFEST.csv` | Original scientific source/result copies and source hashes. |
| `manifests/PUBLICATION_COPY_MANIFEST.csv` | Manuscript/publication copies and source hashes. |
| `manifests/TARGETED_COPY_MANIFEST.csv` | Imported targeted source/evidence members and documented exported variants. |
| `manifests/PUBLIC_METADATA_VARIANTS.csv` | Public metadata adaptations with original/exported hashes. |
| `manifests/COMPACT_OMISSIONS.csv`, `PUBLICATION_OMISSIONS.csv` | Earlier compact/privacy omissions. |
| `manifests/PUBLICATION_SELECTION_OMISSIONS.csv` | Publication cleanup of internal prompts, duplicate drafts and unrelated roadmap notes, with hashes and reasons. |
| [Data and archives](DATA_AND_ARCHIVES.md) | Raw archive identities, roles, retained derivatives and access limitations. |
| [Reproducibility matrix](MANUSCRIPT_REPRODUCIBILITY_MATRIX.md) | Figure, table and numerical-claim mapping and supported/partial/archival status. |
| [Validation receipt](VALIDATION_RECEIPT.md) | Commands actually executed and their bounded outcomes. |

Current manifests distinguish public files from imported historical receipts. Their declared exclusions avoid self-referential hashes and mutable validation records. `.gitattributes` preserves archived bytes across checkout.

## Intentional exclusions and limits

Raw datasets/partition matrices, large trajectories, redundant batch/bootstrap archives, checkpoints, environments, caches, credentials, private launch commands, unrelated future-work roadmaps, internal task prompts and duplicate manuscript drafts are omitted. Reference design files and scientific source required to interpret evidence remain. Exclusion is based on scope, privacy or compactness, never target inclusion or favorable outcomes.

No software license, journal acceptance, publisher DOI, GitHub release version or formal release tag is invented. Packaging version `0.0.0` is an installation placeholder. The authors will update arXiv:2608.26765 separately; its current record still contains an earlier manuscript.

Publication organization was informed by [PhysicalSupportConfidenceSets](https://github.com/GJPengAtNchu/PhysicalSupportConfidenceSets); no scientific implementation or findings from that unrelated project are imported.
