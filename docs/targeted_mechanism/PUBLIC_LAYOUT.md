# Public layout of the supplied targeted materials

The integrated manuscript supplied three nested archives and two Markdown files.
The archives are expanded here with their complete internal file sets:

| Supplied archive | Public destination | Files |
| --- | --- | ---: |
| `TARGETED_MECHANISM_REVIEW.zip` | `artifacts/canonical_paper_export/targeted_mechanism/` | 440 |
| `SOURCE_TARGETED_MECHANISM.zip` | `src/targeted_mechanism_snapshot/` | 86 |
| `SCAFFOLD_Targeted_Mechanism_Independent_Audit_20261015.zip` | `docs/targeted_mechanism/independent_audit/` | 20 |

Paths in this table are relative to the release root. The supplied README and
independent review are retained in this directory. Their archive references and
original commands describe the supplied handoff, rather than executable public
entry points. Historical statements about manuscript integration keep their
original date and scope.

`docs/manifests/TARGETED_IMPORT.json` records archive hashes. The accompanying
`TARGETED_COPY_MANIFEST.csv` records every exported file, its source member,
original hash, public hash and any metadata-only path change. Internal package
manifests remain unchanged and identify the original bytes; use the outer copy
manifest when checking documented public variants. Both package manifests are
preserved separately, as are the source-only historical implementation files.

The review includes 16 pilot and 288 production run summaries, all 36 primary
scalar summaries, all 144 full/restricted-grid and balance/raw summaries,
temporal diagnostics, costs, certificates and 32 saved figures. The production
orchestrator originally uses `local/production/`; the review stores compact
outputs under `run_summaries/production/`. No path substitution here claims that
the snapshot is a turnkey production workflow.

The numerical authority for the targeted manuscript tables is
`artifacts/canonical_paper_export/targeted_mechanism/results/primary_family_36.csv`.
The archived independent review rounds one first-coordinate paired estimate as
`0.02187859`; the saved value is approximately `0.021878584526`, which rounds to
`0.02187858` at eight decimal places. The current manuscript uses the latter.
The archived review is preserved verbatim rather than silently corrected.

For bounded verification, run `python scripts/validate_release.py` from the
release root. It checks the saved evidence and manuscript transcription without
simulation, fitting or bootstrap resampling. The imported independent audit
receipts are distinguished from those current checks.
