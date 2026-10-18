# Reproducibility scope

The baseline is the bundled 40-page manuscript, not the older version currently available at arXiv:2608.26765. The [matrix](MANUSCRIPT_REPRODUCIBILITY_MATRIX.md) records each exhibit separately. A saved-artifact replay does not establish full-study reproduction or stationarity.

## Four distinct levels

| Level | Supported route | Limits |
| --- | --- | --- |
| Artifact regeneration | `scripts/regenerate_paper_figures.py` reads frozen values for all five figures/nine panels. `scripts/regenerate_paper_tables.py` reconstructs source-backed entries and reports per-table coverage. | No coefficient refitting, new bootstrap intervals, training or PDF digitization. Table coverage is partial; unresolved historical entries remain disclosed rather than silently replaced. |
| Representative executable checks | `scripts/run_representative_example.py`, bounded pytest checks and `scripts/validate_release.py` exercise implementation identities, canonical consistency and integrity. | Short runs test arithmetic and structure; they do not reproduce production precision or establish stationary convergence. |
| Full-study reproduction | Scientific source, historical environments, frozen protocols, seeds and compact outputs are retained. | Partial: raw batches/trajectories, full data and partition matrices, restart states and some freeze-time sources are outside the compact checkout. Historical orchestrators can require their original layouts. No production campaign is rerun for publication. |
| Archival provenance | Copy/variant/omission manifests, archive hashes, original audit receipts and recovered-source records document historical work. | Imported receipts are labeled as earlier evidence. Missing files and unavailable public archives are disclosed, not reconstructed or claimed downloadable. |

## Bounded commands

From an installed checkout with TeX available for rendering, use a new output directory:

```sh
python -B scripts/regenerate_paper_figures.py --output ../paper-replay/figures
python -B scripts/compare_figure_replay.py --group all --replay ../paper-replay/figures --output ../paper-replay/figure-comparison.json
python -B scripts/regenerate_paper_tables.py --output ../paper-replay/tables
python -B scripts/run_representative_example.py --output ../paper-replay/example.json
python -B -m pytest -q -p no:cacheprovider
python -B scripts/validate_release.py
python -B manuscript/tools/check_saved_e4_e5.py --out ../paper-replay/saved-array-checks.json
```

The [validation receipt](VALIDATION_RECEIPT.md) records executed commands and outcomes. These commands do not invoke long-running study orchestrators. The saved-array checker reconstructs algebraic quantities from bundled averaged models/vectors; optional original-batch reconstruction is outside this route.

For a manuscript build, make a scratch copy of `manuscript/`, change into it, and run `pdflatex -interaction=nonstopmode -halt-on-error main.tex`, `bibtex main`, and the same `pdflatex` command twice more. A different TeX installation may change PDF metadata/font subsets; compare content and rendered output rather than assuming a hash-identical build.

## Environments

`pyproject.toml` declares publication dependencies for Python 3.12 or newer. `configs/environments/publication_20261018.requirements.lock` records the fresh publication installation; use it with `pip install -e '.[dev]' -r configs/environments/publication_20261018.requirements.lock`. Figure rendering uses TeX-backed text and Latin Modern/T1 fonts; a full TeX Live installation provides the required executables and packages. The original completed layout build used TeX Live 2024/pdfTeX 1.40.26. Exact versions and fresh-environment outcomes for publication checks are recorded in the validation receipt.

`configs/environments/` contains recorded original, supplementary and figure-redraw locks. These describe separate historical workflows, not a guarantee that all historical workflows replay in one combined environment. The figure-layout environment recorded Python 3.12.14, NumPy 2.5.3 and Matplotlib 3.11.2. Preserve `.gitattributes` when checking out archived files so newline conversion does not invalidate hashes.

## Historical execution limits

The independent supplementary registry contains 69 cells (34 controlled and 35 logistic), each with twelve production seeds. The targeted contraction/noise study is separate: 24 cells and twelve paired runs per cell. Temporal averaging uses nine shared-objective configurations and twelve paired runs, giving 1,512 model outputs over seven windows. Overlapping windows share a trajectory and are not independent replicates.

Four supplementary freeze-time files remain unavailable: `study/analysis.py`, `study/cli.py`, `study/tests.py` and `run.py`. Eight of twelve frozen source files were recovered exactly. Delivered later analysis/reporting versions are retained and identified; the legacy import commit does not establish a verified supplementary production commit. See `manuscript/supplementary_results/source_review_snapshot/FROZEN_SOURCE_AVAILABILITY.csv`.

The targeted production orchestrator originally uses `local/production/`, whereas the compact review stores `run_summaries/production/`. Source availability does not provide a turnkey restart environment. The imported independent audit also used separately extracted source/review inputs. See [Data and archives](DATA_AND_ARCHIVES.md) for exact archive names, hashes and unavailable prerequisites.

## Scientific limitations preserved

- The theorem fixes local-step count and dimension. The full bias and remainder can depend on local-step count.
- Historical H=4 finite-grid differences and H=8 deviations remain; intervals account for sampling uncertainty rather than deterministic grid or burn-in error.
- Targeted paired cancellation/noise-law comparisons use a prespecified fitted-coefficient resolution band. Individual-algorithm first-coordinate precision is weaker; restricted-grid target exclusions and the paired second-coordinate exact-zero exclusion remain. Two client-count levels do not establish a general client-count rate.
- Affine translation requires the specified perturbations, corresponding initial controls and matched noise. Orthogonal arithmetic checks do not certify mixing.
- a9a analyses describe one dataset and finite tails under state-dependent sampling noise. Negative corrected squared-mean estimates, temporal sensitivity and failed equivalence/crossover criteria remain visible. The two later pilots do not represent the proposed 48-seed extension, which was not run.
- Directional agreement with the post-hoc proxy does not identify the persistent-control prefactor, establish an exact real-data coefficient or imply predictive harm.

Missing starting states and individual noise statistics prevent reconstructing every historical direct–balance identity. Available endpoint checks and failure to reject temporal differences do not certify stationarity.
