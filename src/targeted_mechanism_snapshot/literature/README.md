# Literature deliverables

The final local manuscript remains unchanged. This directory contains:

- `NOVELTY_COMPARISON.md`: bounded four-paper comparison, direct mathematical implications, source caveats, and unresolved questions.
- `proposed_related_work.patch`: unapplied unified diff for the current manuscript's related-work section and bibliography.
- `proposed_related_work_insert.tex` and `proposed_glasgow2022sharp.bib`: review snippets; not standalone documents.
- `SOURCE_EVIDENCE.json`: exact source URLs/versions, PDF hashes, page anchors, local baseline hashes and access gaps.
- `build_literature_deliverables.py`: regenerates the patch/snippets/metadata from the current baseline and saved sources. It does not edit the manuscript.
- `VALIDATION.json`: baseline-preservation and patch-applicability check results.

Run from `.`:

```powershell
python targeted_closure_20261014/literature/build_literature_deliverables.py
git apply --check --ignore-space-change targeted_closure_20261014/literature/proposed_related_work.patch
```

The second command checks the proposal; it does not apply it. A changed baseline must be reviewed before regenerating or applying a patch. No standalone LaTeX document was created and the manuscript was not recompiled.

The `sources/` directory is local audit evidence: downloaded primary PDFs, extracted text, and rendered formula pages. It contains seven editions of the four required papers, **not seven distinct papers**. Keep these bulky evidence files local; the compact review package should include the report, snippets, patch, manifest and validation record. For independent retrieval, use the exact PDF URLs in `SOURCE_EVIDENCE.json` and compare SHA-256 hashes. The DDB publisher final edition was not obtained; the available author editions are labeled explicitly.

The three source-formula caveats are recorded to prevent transcription errors, not as a claim that the current manuscript is incorrect. They do not replace the separate implementation and scientific-result audits.
