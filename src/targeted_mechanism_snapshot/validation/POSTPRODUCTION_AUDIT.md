# Independent post-production numerical audit

Completed 2026-10-14 after all 288 frozen production runs were available. This audit is read-only: it did not simulate, extend a horizon, modify a target, change a fit, or edit the manuscript.

**Numerical reconstruction passes. Scientific interpretation remains mixed at the reported resolution.** The primary family contains 26 `SUPPORTS_WITHIN_REPORTED_RESOLUTION` and 10 `INCONCLUSIVE_PRECISION` classifications. There are no primary intervals outside a declared zero-resolution band. That does not mean every exact asymptotic target is included: the positive-covariance symmetric matched difference in coordinate 2 excludes exact zero under the primary simultaneous bootstrap interval. The prespecified restricted grid also has three `DISCREPANCY_REQUIRES_AUDIT` classifications. Both observations are retained below.

## Independent numerical reconstruction

The audit read `PROTOCOL_FROZEN.json`, all original production `result.npz` files, and the result CSVs. It did not import or call `analyze.py`. Recalculation used NumPy least squares and explicit run-level variance/contrast formulas, with the frozen bootstrap seed and 4,000 draws.

All 24 configurations contain exactly the frozen 12 seeds, giving 288 runs and 18,432 sampling batches. Counts, horizons, N, gamma, rho, law flags, seed IDs and independently reconstructed SHA256 stream keys agree with the protocol. Every adjacent stored batch boundary agrees exactly, and each final endpoint agrees with the saved global state. All batches have their frozen equal length. Pilot and production seed sets are disjoint. The three simulation source hashes still match the frozen protocol.

Independent checks yielded:

| Quantity checked | Maximum absolute difference from supplied analysis |
|---|---:|
| Cell estimates and run-level SEs | 0 |
| Same-run temporal differences and SEs | 0 |
| Same-run raw-minus-balance differences and SEs | 0 |
| OLS estimates across both estimators and both grids | 1.99e−13 |
| Analytic independent-cell SEs | 2.85e−14 |
| Frozen bootstrap percentile limits | 0 |
| Approximate simultaneous interval endpoints | 1.71e−12 |
| Bonferroni-t sensitivity endpoints | 2.28e−13 |
| Normalized coefficients rebuilt from original NPZ batch means | 7.96e−13 |

The last few nonzero differences arise from operation order (`lstsq` versus pseudoinverse multiplication and weighted versus equal-batch averages); the maxima include very noisy, large raw normalized estimates. They are immaterial relative to all reported intervals.

Within each cell, the complete run vector was resampled together across algorithms and coordinates. Different conditions and grid cells use independent keyed streams; variance addition for cross-condition contrasts is therefore appropriate. Algorithm differences use same-run values, never independent-algorithm SEs. The 36-member family is correctly composed of 24 intercepts, six covariance-matched-law differences and six signed-covariance contrasts. The full and restricted grids remain separate. No null intercept, sign, or common law intercept was imposed.

## Exact-zero exclusion retained

For rho = +1/4 with symmetric noise, the matched SCAFFOLD-minus-FedAvg coordinate-2 full-grid intercept is:

- Estimate: −2.29282088e−5.
- Approximate simultaneous interval: [−4.23409007e−5, −3.51551692e−6], which **excludes exact zero**.
- Ordinary marginal t interval: [−3.77025462e−5, −8.15387135e−6], also excluding zero.
- Bonferroni-t sensitivity: [−5.13895969e−5, 5.53317927e−6], including zero.
- Prespecified restricted-grid estimate: −1.37192796e−5, with simultaneous interval [−3.56446894e−5, 8.20613032e−6], including zero.

The full-grid raw matched estimate is −2.32575273e−5 with simultaneous interval [−4.28884178e−5, −3.62663675e−6]. Thus switching from balance to raw would retain this small exclusion; estimator replacement is neither justified nor a resolution.

All these intervals lie well inside the predeclared practical band ±0.004375. The code's primary status therefore describes **resolution-band containment**, not exact equality or universal target inclusion. The scientific summary must state both facts. The exclusion is sensitive to the interval construction and the prespecified grid restriction; this audit does not declare it a theorem counterexample or prove a finite-grid explanation.

The corresponding six raw grid means of the balance-D second coordinate are approximately 1.922e−5, 5.720e−6, 4.614e−6 for N = 64, and −1.620e−6, −3.734e−6, −3.880e−6 for N = 128, listed in decreasing gamma order. The full-fit intercept extrapolates these values to gamma = 0 and 1/N = 0. Its mean-grid residual RMS is 2.98e−6; the restricted fit has one residual degree of freedom and RMS 2.40e−7. Neither smaller residual RMS nor target inclusion in the restricted fit licenses replacing the primary fit.

## Restricted-grid discrepancies retained

The omitted-largest-gamma sensitivity has 15 support, 18 inconclusive and three discrepancy classifications. The three discrepancies are:

| Comparison and coordinate | Restricted estimate | Approximate simultaneous interval | Target | Bonferroni-t interval |
|---|---:|---:|---:|---:|
| rho +1/4 symmetric, SCAFFOLD C1 | −0.0167517143 | [−0.0590708392, 0.0255674106] | −0.059375 | [−0.0791911556, 0.0456877269] |
| rho +1/4 symmetric, FedAvg C1 | 0.0051013679 | [−0.0372115885, 0.0474143243] | −0.0375 | [−0.0573312986, 0.0675340344] |
| rho-plus minus rho-minus, SCAFFOLD C1 | −0.0684005768 | [−0.1187292817, −0.0180718719] | −0.11875 | [−0.1425650136, 0.0057638600] |

Each target lies just beyond the approximate simultaneous lower bound, while each Bonferroni-t interval includes it. The first two restricted intervals also fail to resolve the individual algorithm's expected negative sign. The full-grid individual-algorithm intervals do resolve the corresponding signs. These sensitivity results are limitations of the observed coefficient resolution and extrapolation; they must remain visible and cannot be described as universally stable recovery. All primary nonzero matched-D targets are included in their approximate simultaneous intervals.

## Required diagnostic sequence for unexpected results

| Check | Evidence inspected and result | Remaining limitation |
|---|---|---|
| Derivatives and analytical targets | `certificate/independent_model_checks.json` and `MODEL_CERTIFICATE.md`: scalar objective differentiated independently; A = diag(1,2), nonzero third tensor, T[C0] = 0, B11(null) = (−0.0125,0), all signed targets and coordinate-2 zeros checked. Reference target disagreement ≤1.39e−17. | These checks verify the specified construction; they do not reprove the manuscript's coefficient theorem. |
| Covariance and noise laws | Exact support enumeration verifies zero means and C_rho, with asymmetric third moment 1/sqrt(2) and fourth moment 3/2 versus 0 and 1. The production code uses the analytical diagonal square root and fresh indexed blocks, with no batch recentering/rescaling. | Finite samples need not match exact moments; indexed pseudorandom independence remains a simulation assumption. Cross-law finite-N dependence may include gamma²/N. |
| Active compiled path | Frozen `targeted/kernels.py`, `targeted/model.py` and `targeted/workflow.py` hashes match. Workflow explicitly calls `trigonometric_chunk`, which calls the trigonometric `explicit_round`; it does not use the historical hardcoded logcosh kernel. Independent nonzero-state round checks had state error ≤1.12e−16 and control error ≤1.14e−13. Indexed-path checks cover both noise laws, with active scalar-path error ≤9.25e−15. | Passing finite numerical tests is not an exhaustive proof for all states or all horizons. |
| Timing and observations | New batches retain their true start/end states, post-round raw means, nonlinear balance means, eta means and accumulated round-recursion residuals. Every stored adjacent boundary and final state matches. Equal batch lengths justify means of batch means. | Only finite sampling windows are observed. |
| Paired telescoping and arithmetic | All primary/first-half/last-half identities are available. Published maximum residual after accounting for recorded round arithmetic is 1.34e−20, or 6.89e−12 on the normalized coefficient scale. Independent weighted reconstruction gives 1.28e−20. Maximum observed control mean is 4.58e−14; largest stored per-round ideal-recursion residual is 2.51e−16. Pre/post identities and preservation of deliberately nonzero control means were independently tested; no projection is used. | Identity agreement establishes alignment and arithmetic consistency, not stationarity or an asymptotic coefficient. No material identity failure was found to explain the 2.3e−5 fitted second-coordinate shift. |
| Burn-in and temporal diagnostics | Fixed 50*tau burn and 64 batches of 10*tau were preserved for all runs. Same-run first/last 32-batch comparisons are present. Among 48 cell-coordinate comparisons per observable, balance SCAFFOLD and FedAvg each have four ordinary nominal temporal exclusions; matched D has zero. Raw algorithms each have two; raw matched D has zero. | These are unadjusted diagnostic counts, not a family test. The nominal exclusions are retained; absence of a matched-D exclusion is not a mixing certificate. No burn-in extension was authorized or performed. |
| Finite-grid fit and uncertainty | Independently reproduced all full/restricted OLS fits, 36 contrasts and frozen bootstrap intervals. Primary design has six cells and three regressors; restricted design has four cells and three regressors. Design condition numbers are about 1642 and 4096. Both use two N levels and unconstrained (1,gamma,1/N) fits. | Two N levels do not identify an N-rate. Deterministic remainder and burn-in error are outside the sampling intervals. The restricted sign/target changes remain unresolved; no fit was selected by target inclusion. |

The existing 14 old unit tests passed before and after the isolated new path was added; all six new unit tests passed, and the independent model/kernel checks passed. This review found no concrete implementation error requiring a new simulation or code correction. The checks narrow possible explanations but do not establish that every observed displacement is merely finite-grid remainder.

## Cost, completion and permissible claims

All 288 frozen production runs completed at a measured 1.262283 kernel CPU-hours. The existing 16 pilots add 0.043759 CPU-hours, for 1.306042 CPU-hours total, within the six-hour cap. This is measured simulation CPU, not a sum of parallel wall-clock times. No failed condition or unfavorable result was dropped.

The matched coefficient null is separated from the two active controls at the reported resolution, and the primary nonzero matched-D signs and scales are recovered. The matched covariance-law differences are contained in their practical resolution bands. Individual-algorithm null/law coordinate-1 intervals are too wide for the requested resolution; the additional coordinate-2 and restricted-grid limitations above remain. Neither a null result nor successful telescoping establishes stationarity or exact coefficient equality.

Only this audit report was written during the post-production QA. No result CSV, frozen protocol, source kernel, manuscript, or Git remote was changed.
