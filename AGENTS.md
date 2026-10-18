# Maintenance rules

The scientific baseline is the finalized 40-page manuscript in `manuscript/main.pdf` and its frozen inputs. Its SHA-256 is `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. The current arXiv record is an earlier version and does not replace this baseline.

- Preserve objectives, noise laws, algorithm updates, control semantics, configurations, seeds, partitions, estimators, windows, fits, confidence families and theoretical targets. Do not tune to target inclusion or remove unfavorable outcomes.
- Separate maintenance from new scientific work. Do not start full simulations, optimizer campaigns, bootstrap campaigns or unrelated workstreams as part of documentation or publication maintenance.
- The supplementary compiled controlled kernel embeds its objective. The targeted nonquadratic model has a separate reference/compiled execution path. A model-module edit alone cannot establish kernel equivalence.
- Keep manuscript and numerical artifacts unchanged during packaging. Use scratch output directories for regeneration and compare against canonical inputs. Preserve precision and record any justified metadata-only path adaptation with both original and exported hashes.
- Distinguish artifact regeneration, representative execution, full-study reproduction and archival provenance. Disclose missing historical files; never invent seeds, source versions or execution receipts.
- Read `docs/MANUSCRIPT_REPRODUCIBILITY_MATRIX.md` before changing a supported entry point. Run the affected bounded tests, `scripts/validate_release.py`, and `git diff --check`. Record commands actually executed and their outcomes.
- Keep public paths repository-relative. Exclude secrets, local credentials, environments, caches, raw private archives and duplicate drafts. Follow `.gitattributes` so archived bytes are not changed by newline conversion.
- Preserve Git history and the manuscript's repository URL. Do not force-push, change visibility, create a new license or release tag, or update arXiv as an incidental maintenance action.

Routine documentation corrections, portable wrappers and relevant checks can proceed within an authorized maintenance task. Scientific changes require a separate scientific task and a distinct evidence record.
