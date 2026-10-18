# Publication validation receipt — 18 October 2026

These checks ran in a new isolated Python 3.12.14 environment on Windows with TeX Live 2024/pdfTeX 1.40.26. The resolved packages are in `configs/environments/publication_20261018.requirements.lock`. Historical experiment environments remain separate. No production campaign, coefficient refit or bootstrap rerun was performed.

## Executed commands

Commands ran from the repository root. Output names below are portable equivalents of the new external scratch directories used.

| Command | Executed result |
| --- | --- |
| `python -m pip install -e '.[dev]' -r configs/environments/figure_redraw.requirements.lock` | PASS in a fresh virtual environment; resolved versions captured in the publication lock. |
| `python -B scripts/regenerate_paper_figures.py --output ../paper-replay/figures` | PASS; five figures, nine panels and eleven frozen inputs. Calls the comparison command below. |
| `python -B scripts/compare_figure_replay.py --group all --replay ../paper-replay/figures --output ../paper-replay/figure-comparison.json` | PASS_RENDER_EQUIVALENT; CSV/PNG bytes, geometry, PDF operators, normalized fonts, page boxes and 216-dpi pixels match. Nine PDF byte differences remain. |
| `python -B scripts/regenerate_paper_tables.py --output ../paper-replay/tables` | PASS_WITH_DISCLOSED_GAPS; 21 data exports; fourteen decimal-result tables with 453 exact displayed decimal cells. |
| `python -B scripts/run_representative_example.py --output ../paper-replay/example.json` | PASS; nine check groups, at most three clients, two coordinates, four local steps and seventeen rounds per call. |
| `python -B manuscript/tools/check_saved_e4_e5.py --out ../paper-replay/saved-array-checks.json` | PASS; 1,507 checks and 221,919 scalar comparisons; maximum difference 1.75e-15. No training, resampling or missing-batch reconstruction. |
| `python -B -m pytest -q -p no:cacheprovider` | 15 passed in 8.02 seconds: three integrity/formula tests, nine mechanism tests and three table-generator tests. |
| `python -B scripts/validate_release.py` | PASS; hashes, file closure, frozen baseline, active exhibit mapping, result consistency, dependencies and manuscript repository URL. |
| `python -B scripts/audit_git_bytes.py` | PASS; nine representative Git filtered/unfiltered byte checks. Historical CRLF bytes are preserved. |

The bounded checks cover scalar/vector SCAFFOLD and FedAvg arithmetic, reference/compiled kernels, zero/nonzero control means, deterministic/quadratic boundaries, exact noise moments, Lyapunov/tensor formulas, affine translation, orthogonal equivariance and finite-window/resume identities. Finite-window residuals are at most 8.4e-18; indexed chunk/resume states are bitwise equal. These tiny runs do not establish stationary convergence.

Table tests exercise deterministic exports, unchanged inputs, unsafe-output rejection, changed saved values and inconsistent paired records. Table 18 only accepts the specifically documented missing-threshold/rounding differences; additional differences fail.

CITATION.cff passed the official CFF 1.2.0 JSON Schema using a separate tooling environment; see `manifests/CFF_SCHEMA_VALIDATION.json`. All fifty relative Markdown links in the landing page and top-level documents resolved. A credential scan found no secrets.

The complete staged `git diff --check` reports historical whitespace in 27 unchanged files (including literal patch context and blank EOF lines). Their pre-publication hashes match. The publication-maintenance-only check passes. `manifests/PUBLICATION_WHITESPACE.json` records this partial check explicitly; frozen source/manuscript bytes were not reformatted to silence it. Git checks recognize historical CRLF using `-c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`.

## Frozen evidence and disclosed gaps

`manifests/FROZEN_BASELINE_MANIFEST.csv` checks 1,277 retained scientific, configuration, manuscript and numerical files against the pre-publication baseline. All are unchanged. The 40-page manuscript SHA-256 remains `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`. Active TeX, nine panels, scientific implementations and saved results are preserved.

Seventeen internal prompts, unused drafts/roadmaps and duplicate historical PDFs are omitted with hashes/reasons in `manifests/PUBLICATION_SELECTION_OMISSIONS.csv`. No unfavorable scientific result was omitted.

The active paper has 22 numbered tables plus one inactive source table: seventeen computational/configuration tables are supported; Tables 8, 18, 19 and 20 are partial; Table 1 is an analytical literature comparison. Table 18 lacks four original per-run SE thresholds, and its H=4,N=16,j=2 balance coefficient differs by about 3.32e-7 at the displayed precision. Missing cells remain unavailable and the manuscript is unchanged. See [table details](TABLE_REGENERATION.md) and the [matrix](MANUSCRIPT_REPRODUCIBILITY_MATRIX.md).

Full-study reproduction remains partial because some original trajectories, batch/data/partition/restart inputs and four supplementary freeze-time source files are unavailable. Two archived audit scripts retain historical `/mnt/data` paths as provenance; they are not supported public execution entry points.

## Machine-readable and historical receipts

Current evidence is in `manifests/PUBLICATION_FIGURE_REPLAY.json`, `manifests/PUBLICATION_REPRESENTATIVE_CHECKS.json`, `manifests/PUBLICATION_SAVED_ARRAY_CHECKS.json`, `manifests/PUBLICATION_ENVIRONMENT.json` and `../artifacts/canonical_paper_export/tables/VALIDATION_RECEIPT.json`. `SOURCE_MANIFEST.csv` and `manifests/RELEASE_FILE_MANIFEST.csv` bind the current files; this receipt and the self-manifest are excluded from recursive hashing.

The October 18 layout directory retains the earlier clean 40-page build, all-page 120-dpi pixel/text comparison and final-font audit bound to the same manuscript hash. These are earlier completed checks, not a new TeX compilation or font measurement by the release validator. Older October 9/15 evidence retains its original scope.
