# Independent analysis review

Status: **PASS_FOR_FROZEN_DESCRIPTIVE_ANALYSIS**, with the inferential and
forecast limitations below. This review examined source and completed pilot
diagnostics before production results were analyzed. It did not inspect
production effects or change simulation settings, data, objective, targets,
windows, hypotheses or the master manuscript.

Reviewed files: `analyze.py`, `PROTOCOL_FROZEN.json`, `forecast.py`, and the
summary/indexing conventions in `targeted/workflow.py`. This review also ran
synthetic-data checks with arbitrary, non-target intercepts and independently
recomputed covariance-based standard errors. The previously reported source
hash for `analyze.py` in the initial review was
`0620caaccbc414c1d3340b8573a8cc4d5b36647e8a0307e0c2c8bfa21f2f8f26`.
Two pre-analysis robustness/interpretation corrections were requested and
verified in the revised source: input-schema/key/count/endpoint assertions,
and a distinction between practical-band resolution and exact-zero exclusion.
They do not alter estimands, fits, intervals or the frozen simulation.

Reviewed SHA-256 values after those corrections:

| File | SHA-256 |
| --- | --- |
| `analyze.py` | `11751f6cb45e8e5d63da6b13d6865c286a200eceec828ad433c3ad94588c9572` |
| `forecast.py` | `bc1c0f8f6ddcda8bff3faaa6895aefafab017d521fe9bf1363ccdbbde18208ea` |
| `PROTOCOL_FROZEN.json` | `450b187da1f91f939745f3c42e8d579c66b70deb048bf2de3ba718e860e69618` |
| `targeted/workflow.py` | `d7c70a4ac1c81733fb46e28320f3039d648cf4d4aa810ea92f6df0f5fadd50eb` |

## Estimands, normalization and family

The normalization is correct: C^A=(b^A-(gamma/N)B11)/gamma², while the paired
D=(b^S-b^F)/gamma² is formed directly from the same run. B11 cancels from D
and from same-covariance law contrasts. Both coordinates are retained.

The family contains exactly 36 scalar summaries, in the stated ordering:
24 condition × observable × coordinate intercepts, six symmetric-minus-
asymmetric law contrasts at rho=+1/4, and six rho-plus-minus-rho-minus
contrasts. The signed contrast is ordered plus minus minus; its coordinate-1
target is negative for all three observables. An array-label test independently
verified the mapping and ordering, without referring to fitted outcomes.

Fits are separate, unconstrained, unweighted OLS on (1,gamma,1/N). The full
grid has six cells per condition; the named sensitivity retains the four
cells that omit gamma=1/512. Neither null values, sign symmetry nor common-law
intercepts are imposed. The four-cell sensitivity has only one residual
degree of freedom; its fitted value remains descriptive. Two N levels do
not establish an N-rate, and the actual finite-grid remainder need not be
linear in gamma and 1/N.

Synthetic run vectors with arbitrary intercepts, slopes and correlated
algorithm components recover the known intercepts to maximum absolute error
1.12e-16 (full) and 1.67e-16 (restricted). These checks confirm calculation,
not the adequacy of the linear descriptive model for the scientific data.

## Independent units, resampling and covariance

The run is the independent sampling unit. The bootstrap resamples all six
algorithm/difference/coordinate components together within a cell and uses
fresh resampling indices for each distinct cell. Consequently it preserves
the strong SCAFFOLD/FedAvg covariance and the algebraic dependence of their
difference; it does not count batches or coordinates as independent runs.

The key includes phase, condition, N, exact gamma representation and seed.
All 288 production and 16 pilot keys were verified distinct (304 unique
keys). This supports the declared pseudorandom-stream design: coincident seed
labels across cells do not create paired cross-cell observations. Under that
design, variances add for cross-law and signed-covariance contrasts.

For each scalar intercept, the analytic variance is sum_cell(w_cell² s_cell²/12).
For D, s_cell² is calculated from the actual paired difference, not from an
independent-algorithm approximation. An independent calculation from the
full six-dimensional within-cell covariance matrices agreed with every
reported family standard error to maximum error 4.17e-17.

The same fixed bootstrap seed and cell ordering give the same resampling
indices for raw and balance full-grid fits. Temporal and raw-minus-balance
diagnostics are formed as same-run differences before their run-level standard
errors are calculated; this also preserves their covariance. The restricted
grid is a separate sensitivity, not a jointly calibrated additional primary
family. The 36-way interval claim applies to the primary balance/full-grid
family, not simultaneously to all raw and sensitivity results combined.

The fixed 4,000-draw bootstrap satisfies the requested draw count. The maximum
absolute standardized bootstrap error provides an **approximate** simultaneous
interval using plug-in bootstrap standard deviations. It is not an exact
small-sample confidence certificate or a full bootstrap-t calculation with
replicate-specific standard errors. Ordinary percentile/t intervals and the
36-way Bonferroni-t sensitivity are retained. With 12 runs per cell, the df=11
t sensitivity is a cautious nominal choice rather than a finite-sample
distribution-free guarantee. None of these sampling intervals includes burn-in
error or deterministic finite-grid remainder.

## Windows, endpoints and data validation

Every frozen sampling batch has equal length, so the unweighted mean of batch
means equals the round-weighted window mean. The revised loader asserts the
frozen 64×27 schema, finite values, prescribed batch and total counts, seed/N/
gamma/rho/law metadata, deterministic key, exact adjacency of batch endpoints,
and equality of the last endpoint to the saved final state. A complete family
requires all 12 runs in each cell. Incomplete/resource-limited production must
be reported explicitly rather than analyzed as a silently reduced family.

The recorded raw state is post-round. The code correctly evaluates

`B*(mean_post-mean_balance)-mean_eta+P^H*(end-start)/T-mean_recursion_residual`.

For algorithm differences, subtracting the two expressions cancels the same
noise eta exactly and retains the difference of endpoint and arithmetic/control
residual terms. The paired residual is not treated as two independent noisy
estimates. Its coefficient-scale version divides by B and gamma².

Primary/first-half/last-half windows retain their own endpoints. First-versus-
last comparisons use the difference within each of the same 12 runs. This
is a temporal diagnostic; a wide or zero-including interval does not establish
stationarity. On all 16 completed pilot files, batch endpoint continuity was
exact, and the maximum post-round identity residual across the three windows
was 5.06e-21. No production outcomes were needed for this verification.

## Interpretation of resolution and discrepancy

The revised zero-target classification correctly treats the prespecified band
separately from zero inclusion:

- Entire interval inside ±margin: `SUPPORTS_WITHIN_REPORTED_RESOLUTION` means
  a fitted-coefficient resolution statement only. An interval may exclude
  exact zero while remaining inside this practical band. The separate
  `exact_target_sampling_exclusion` and `zero_excluded` flags preserve that
  fact; it must not be described as proof of exact zero or exact invariance.
- Entire interval outside the band: `DISCREPANCY_REQUIRES_AUDIT`, without
  treating a descriptive finite-grid estimate as a theorem counterexample.
- Crossing a band edge or being too wide: `INCONCLUSIVE_PRECISION`, with the
  numeric estimate and width retained.

Nonzero controls additionally require their sign to be resolved and their
target to lie in the interval for the support status. A target-excluding
control is a reason to audit arithmetic, timing, transient behavior and grid
dependence; it is not automatically a scientific rejection. Target inclusion
alone is not validation. These statuses summarize reported resolution and
diagnostic needs rather than superseding the numerical tables.

## Pilot and cost forecast limits

The CPU forecast uses measured new-kernel pilot timings, all four conditions,
linear-in-N scaling and a 25% engineering reserve. Its 1.840844 CPU-hour
projection is below the six-hour cap. It retains the proposed schedule rather
than dropping any condition. Actual measured CPU time and resource decisions
must still be reported at completion; a forecast is not a measured cost.

The precision forecast estimates a six-component run covariance from just
four independent pilot runs per condition. Omitting B11 from these pilot
vectors does not affect covariance because it is a fixed shift within each
condition. The extrapolation factor `max(1,64/N * gamma_pilot/gamma)` is a
heuristic variance-scaling model with a floor. Calling it conservative does
not prove an upper variance bound across the grid. The reported lag-one
batch correlations are also noisy diagnostics, not mixing-time estimates or
proofs of independent batches.

The saved precision table forecasts the 24 base intercepts. It does not
explicitly forecast the 12 law/signed contrasts or estimate their simultaneous
bootstrap critical value. Under the declared cross-condition independence,
a contrast's forecast SE would be sqrt(SE_left²+SE_right²), but those values
would remain noisy forecasts. This limited forecast scope is not evidence
that either mechanism will resolve. Do not rerun `forecast.py` during or after
production merely to augment the table: its main function also overwrites
the frozen protocol. Any supplemental forecast must be labeled and preserve
the original freeze and schedule.

No numerical or interpretation issue identified here requires changing the
frozen simulation. All scientific conclusions remain contingent on complete
reported results, the original sensitivity and the stated uncertainty limits.
