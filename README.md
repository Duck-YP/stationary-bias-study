# Characterizing Client-Independent Stationary Bias for SCAFFOLD and FedAvg in Federated Learning

**Yi-Ping Tang and Guan-Ju Peng** · [Manuscript](manuscript/main.pdf) · [arXiv:2608.26765](https://arxiv.org/abs/2608.26765) · [Reproducibility matrix](docs/MANUSCRIPT_REPRODUCIBILITY_MATRIX.md)

This repository accompanies the revised, 40-page manuscript and provides scientific implementations, frozen configurations, compact numerical evidence, and saved-data reproduction tools. The arXiv record currently hosts an earlier version; an updated manuscript version will be uploaded separately. Use the bundled manuscript for the results documented here.

## Research questions and contributions

For a common strongly convex objective, additive noise and full participation, the paper identifies a shared leading stationary mean-bias contribution of order `gamma/N` and explicit, algorithm-dependent coefficients of order `gamma^2`. The remainder bound is uniform in the number of clients under the stated assumptions, with local-step count and dimension fixed.

Matched SCAFFOLD–FedAvg comparisons cancel the shared leading contribution and isolate the second-order contribution of persistent controls. The coefficient is expressed through curvature and noise contractions; it need not vanish as the client count grows. The paper also proves an exact translated-control relation for a specified class of affine objective shifts. These statements concern parameter displacement; they do not equate it with prediction loss or total mean-squared error.

| Paper location | What the evidence examines |
| --- | --- |
| Sections 6.2.1–6.2.3; Figures 1, 2 and 5 | Individual and matched coefficients, joint step/client grids, fixed-step client counts, and retained finite-grid differences. |
| Sections 6.2.4–6.2.6; Appendix C.3 | Five-dimensional noncommuting curvature/covariance, Cartesian grids, leading coefficients, local-step dependence, orthogonal equivariance and affine translation. |
| Section 6.2.7; Tables 4, 16 and 17 | Nontrivial contraction cancellation, signed covariance controls, and symmetric/asymmetric noise laws with matched covariance. |
| Section 6.3; Figure 3 and Tables 5, 21 | a9a logistic regression under a fixed total minibatch budget, shared and disjoint partitions, and step-size/local-step comparisons. |
| Sections 6.4–6.5; Figure 4 and Tables 6, 22 | Finite-tail temporal averaging, error decomposition and a post-hoc full-vector curvature–noise directional proxy. |

## Install

Use Python 3.12 or newer. Figure rendering additionally requires a TeX installation providing `latex`, `dvipng`, T1/Latin Modern fonts, and the manuscript packages. A manuscript build also needs `pdflatex` and BibTeX. Dependencies are declared in [pyproject.toml](pyproject.toml); [environment notes](docs/REPRODUCIBILITY_SCOPE.md#environments) distinguish the publication environment from recorded historical environments.

Windows PowerShell:

```powershell
git clone --config core.longpaths=true https://github.com/Duck-YP/stationary-bias-study.git
cd stationary-bias-study
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]" -r configs/environments/publication_20261018.requirements.lock
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```sh
git clone https://github.com/Duck-YP/stationary-bias-study.git
cd stationary-bias-study
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]' -r configs/environments/publication_20261018.requirements.lock
```

Use a short Windows checkout location near the drive root. For an existing checkout, run `git config core.longpaths true`; preserved historical directory names can exceed Git's default Windows path limit. This Git setting alone does not remove Python's path limit on every Windows installation: keep complete file paths below 260 characters unless Windows long-path support is enabled. Skip the clone/cd lines when already inside the repository. The following commands run from the repository root with the environment active. In PowerShell, invoking `.venv\Scripts\python.exe` directly also works without activation.

## Regenerate and verify saved artifacts

```sh
python -B scripts/regenerate_paper_figures.py --output ../paper-replay/figures
python -B scripts/compare_figure_replay.py --group all --replay ../paper-replay/figures --output ../paper-replay/figure-comparison.json
python -B scripts/regenerate_paper_tables.py --output ../paper-replay/tables
python -B scripts/run_representative_example.py --output ../paper-replay/example.json
python -B -m pytest -q -p no:cacheprovider
python -B scripts/validate_release.py
```

Use a new scratch output directory. Figure and table regeneration reads frozen outputs; it does not refit coefficients, resample intervals, or launch the production studies. The representative example executes bounded algorithm checks and is not evidence of stationary coefficient convergence. Consult the [table-by-table coverage matrix](docs/MANUSCRIPT_REPRODUCIBILITY_MATRIX.md), [figure provenance](docs/FIGURE_PROVENANCE.md), and [validation receipt](docs/VALIDATION_RECEIPT.md) for exact scope and executed outcomes. TeX font subset identifiers can change PDF bytes; numerical and rendered equivalence are reported separately from byte identity.

## Reproducibility and limitations

The repository supports artifact regeneration and bounded implementation checks. Full-study reproduction has a narrower, explicitly documented scope: some historical batch archives, full data/partition matrices, restart states, and four supplementary freeze-time source files are unavailable in this compact checkout. The [scope document](docs/REPRODUCIBILITY_SCOPE.md) and [archive/data register](docs/DATA_AND_ARCHIVES.md) identify these limitations.

Historical H=4 finite-grid differences, H=8 deviations and insufficient precision for individual mechanism coefficients are retained. Approximate sampling intervals exclude deterministic grid and burn-in error. The real-data analyses describe finite tails under state-dependent sampling noise; they do not certify stationarity or extend the additive-noise theorem. Negative sampling-corrected squared-mean estimates remain visible. Directional agreement does not identify the control prefactor.

## Repository guide

| Location | Contents |
| --- | --- |
| [manuscript/](manuscript/) | Final LaTeX, bibliography, 40-page PDF, and nine active vector panels. |
| [src/](src/) | Original coefficient implementations, supplementary algorithms, and the separate targeted-model snapshot. |
| [configs/](configs/) | Frozen designs, seed specifications, protocols, and historical environments. |
| [artifacts/canonical_paper_export/](artifacts/canonical_paper_export/) | Compact coefficients, mechanism results, real-data summaries and immutable figure inputs. Original lineage names are retained for traceability. |
| [scripts/](scripts/) | Saved-data figure/table regeneration, bounded example and release validation. |
| [tests/](tests/) | Bounded publication checks and separately identified archived tests. |
| [docs/](docs/) | [Method-to-code map](docs/METHOD_TO_CODE_MAP.md), [result provenance](docs/RESULT_PROVENANCE.md), [release manifest](docs/PUBLICATION_RELEASE_MANIFEST.md), and [file hashes](docs/SOURCE_MANIFEST.csv). |

## Citation and reuse

Please cite the revised manuscript with its existing arXiv identifier. The note below distinguishes the bundled revision from the older version currently served by arXiv. [CITATION.cff](CITATION.cff) supplies structured metadata.

```bibtex
@misc{tangpeng2026stationarybias,
  author = {Tang, Yi-Ping and Peng, Guan-Ju},
  title = {Characterizing Client-Independent Stationary Bias for SCAFFOLD and FedAvg in Federated Learning},
  year = {2026},
  eprint = {2608.26765},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2608.26765},
  note = {Revised manuscript accompanies the repository; the arXiv record currently hosts an earlier version}
}
```

No journal acceptance, publisher DOI, formal software release tag, or software license is asserted. Packaging version `0.0.0` is an installation placeholder. Dataset redistribution is addressed separately in [Data and archives](docs/DATA_AND_ARCHIVES.md).
