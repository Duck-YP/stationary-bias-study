# Regenerating tables from saved evidence

Run from the repository root after installing the documented environment:

```text
python scripts/regenerate_paper_tables.py --output ../regenerated_tables
```

The output directory must be new or empty and outside the repository. The command reads saved CSV, JSON, YAML and the historical report/formatter used for one display convention. It performs fixed row selection, consistency checks, rational arithmetic, counting, scaling and formatting. It does not simulate trajectories, fit regressions, bootstrap, modify the manuscript or select rows by target inclusion.

The active 40-page paper has **22 numbered tables**. A 23rd table environment, `tab:F-artifacts`, is in `manuscript/appendix/D_reproducibility.tex`, which `main.tex` does not input. It is recorded as an inactive archive table with no current number or page. The numbering catalog is bound to the finalized PDF SHA-256 `81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c`.

| Coverage | Tables | What the command establishes |
| --- | --- | --- |
| Supported numerical results | 2–6, 11–17, 21–22 | Fourteen tables; 453 decimal cells match the manuscript's displayed values and precision. Values are regenerated from saved results before the manuscript is read for comparison. |
| Supported exact symbolic values | 10 | Two noise laws from the exact independent certificate; rational marginal probabilities and symbolic third/fourth moments. `sqrt(2)/2` is retained rather than replaced by a decimal. |
| Supported configuration inventories | 7, 9 | Frozen design and inference fields, with explicit counts where needed. Normalized metadata exports, rather than verbatim prose or page layout. |
| Partial | 8, 18, 19, 20 | Available fields are exported; absent fields and display differences are explicit. Details below. |
| Analytical literature | 1 | Asymptotic/theorem comparison, not a computational table. Requires checking the cited mathematical statements. |
| Inactive archive | `tab:F-artifacts` | Preserved source-only table; not represented as a result in the current paper. |

Every one of the 21 active computational/configuration tables receives CSV, Markdown and plain LaTeX data exports. These are deliberately not replacement manuscript layouts. Long protocol records are normalized into field/value rows, with all saved cell schedules retained. The exports include unfavorable, restricted-grid and zero-crossing results, including the three Table 17 discrepancies. Fixed selectors in the source modules define the table populations; no significance or target-inclusion filter is introduced.

`coverage.json` and `coverage.csv` cover all 23 source table environments. `coverage.json` records the current table/section/page, exact input paths, output paths, coverage notes, missing fields and available source-row selectors. The catalog also identifies all five figures and nine panels; figure rendering remains the separate figure command. `VALIDATION_RECEIPT.json` records input/code hashes, output hashes, numerical display checks, scope and author-attention items. `README.md` summarizes the generated package. Outputs are deterministic: no date, machine path or random seed is newly generated.

The release retains this generated package under `artifacts/canonical_paper_export/tables/`. To reproduce it, run the command above into an external directory and compare the output bytes or receipt hashes.

## Data generation and validation are separate

The builders are in `scripts/table_regeneration/`: `historical_tables.py`, `recent_tables.py`, and `config_tables.py`. They do not read manuscript tables to obtain numerical cells. Exact paths, saved selectors, interval fields, scales and display precision are encoded in these modules; recent/configuration exports additionally record row indices or JSON keys in `coverage.json`.

Only after generation does the command read the relevant manuscript TeX for validation. For the fourteen numerical tables it compares the complete **multiset of decimal display strings**, including duplicate cells and trailing zeros, inside each table body. This check validates displayed numbers and precision; it does not independently prove row association or the underlying scientific estimator. Fixed source selectors and the retained scientific provenance supply those associations. Protocol prose and exact symbolic expressions are not claimed to pass this decimal-string comparison.

Table 14 has a historical precision convention: saved CI endpoints first use the original report formatter's nine significant digits and then display ten decimal places. The command checks that the formatter in `src/stationary_bias/workstreams/p2_multidimensional_validation/formal_analysis.py` is present and that each endpoint appears in the saved `docs/original/p2_multidimensional_validation/artifacts/formal/p2-d5-controlled-validation/p2_d5_controlled_validation_report.md`. Intercepts and targets come directly from the full-precision fit CSV. The convention explains the six otherwise different last digits without reading replacement values from the manuscript.

The E4 table uses saved simultaneous intervals and saved paired contrasts. Its duplicated paired fields must agree across algorithm records. Historical fit files repeat the same intercept at multiple settings; the generator verifies equality before selecting a record. Missing, ambiguous or inconsistent saved rows stop the command. Unexpected numerical display mismatches produce a failing receipt and a nonzero exit code.

Table 18's validation exception is limited to the four specifically audited missing thresholds and its one documented rounding discrepancy. Any additional changed decimal cell fails, including in this partial table. The allowlisted printed thresholds are validation expectations only; they are never inserted into generated cells or used to reconstruct uncertainty.

## Remaining gaps and author attention

- **Table 8:** frozen schedules and original minimum/maximum batch policies are exported. The supplementary/targeted heuristic ceiling formulas are not structured formula fields in these sources, and a planned original policy does not establish every realized stopping batch.
- **Table 18:** the four saved failing per-run comparisons supply the direct and balance coefficients and unnormalized mean differences. The compact per-run summary does not preserve the individual combined-standard-error thresholds. Those four cells are `UNAVAILABLE`, never zero or an estimate from unrelated setting-level uncertainty. For `H=4,N=16,j=2`, the saved balance coefficient is `-0.10802366831450083`, which displays as `-0.1080237` at seven decimals. The paper displays `-0.1080240`, a difference of about `3.32e-7`. Six-decimal rounding followed by a trailing zero would explain it, but no saved formatting rule establishes that history. The generator keeps the saved value and reports the discrepancy. This is a display-precision limitation, not evidence of a changed scientific result.
- **Table 19:** rotation configuration and all 24 affine-check records are preserved. The selected affine CSV does not contain its gamma, offset construction or translated-initialization/matched-noise semantics; those prose settings require the retained scientific source rather than being inferred from numeric check rows.
- **Table 20:** dataset/preprocessing, objective, configurations, windows, operation counts and pilot schedules are exported. Regime labels alone do not establish the label conversion, sampling-with-replacement, equal-client weighting, IID/two-shard construction, base-step formula or primary-versus-alternative partition semantics. Those descriptions are linked to source in the manuscript matrix.

The normal result is `PASS_WITH_DISCLOSED_GAPS`, not a claim that every printed cell has been reconstructed. The four partial tables remain partial even when all exact decimal checks pass. Missing historical per-run uncertainty is not repaired by a new simulation, refit or bootstrap.

Bounded tests can be run with:

```text
python -m pytest -q tests/bounded/test_table_regeneration.py
```

They check deterministic exports and read-only inputs, retain the disclosed gaps, reject unsafe output destinations, and verify that a changed saved value or broken paired record is detected. See [the manuscript reproducibility matrix](MANUSCRIPT_REPRODUCIBILITY_MATRIX.md) for each figure, table and major numerical claim.
