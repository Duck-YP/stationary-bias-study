# Export Reproduction

Export tools support explicit --workspace and --export-dir so they can be run from SOURCE_REVIEW.
Use a NEW independent output directory outside supplementary_study; do not overwrite the delivered export.
Requires the preserved original full ZIP and source.zip under the original workspace.

```powershell
python SOURCE_REVIEW/tools/inventory.py --workspace . --export-dir ./review_exports/NEW_EXPORT
python SOURCE_REVIEW/tools/export_review.py build --workspace . --export-dir ./review_exports/NEW_EXPORT
python SOURCE_REVIEW/tools/export_review.py finalize --workspace . --export-dir ./review_exports/NEW_EXPORT
python SOURCE_REVIEW/tools/export_review.py integrity --workspace . --export-dir ./review_exports/NEW_EXPORT
```

Build copies the invoked tools and available export log into NEW_EXPORT automatically.
Run analysis-only replay against
NEW_EXPORT/qa_extraction with output NEW_EXPORT/qa_extraction/analysis_replay; then finalize and
integrity again to include its certificate. Existing packages are never used as recursive inputs.
