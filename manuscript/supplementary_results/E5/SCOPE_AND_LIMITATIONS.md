# Scope and limitations

## Proven result versus plug-in

The theoretical difference is gamma^2 B20_ctrl(H) + O_(H,d)(gamma^2/N + gamma^3). Its assumptions include a common homogeneous objective, full participation, bounded state-independent additive noise, fixed client covariance C in the prescribed joint limit, fixed d and H, and sufficiently small gamma. The remainder explicitly depends on H and d; the full bias/remainder is not H-independent.

R0 is homogeneous in empirical objective, with shared retained training rows, but its minibatch logistic noise is state-dependent. All 124 coordinates including the intercept have ridge coefficient 0.01. At the fixed reference, ideal with-replacement sampling gives C_ref=Sigma_ref/m, with no finite-population correction. The deterministic indexed SplitMix64/modulo implementation is not an i.i.d. mathematical oracle; modulo-row total variation under a uniform 64-bit key is about 1.37685e-17, and pseudorandom independence is a modeling assumption. The code/source audit records these separately from floating-point control drift.

When N changes under N*m=256, m and the client covariance change. Reference-point T and Sigma do not describe the entire state-dependent noise field. The contraction T_ref[Sigma_ref] differentiates curvature with Sigma_ref held fixed; differentiating trace(A(x) Sigma(x)) would add noise-field derivative terms and is a different quantity. Finite gamma, finite burn/tail, one dataset, 12 seeds, fixed d=124 and only H1/2/4 preclude theorem-level generalization. No heterogeneous real-data theorem is inferred. E1 theory-coefficient validation and E2 affine-heterogeneity exact relations remain separate historical evidence streams.

## Estimands

E5 Delta is the seed mean of each run's actual time-averaged SCAFFOLD model minus its matched FedAvg model. Its squared norm is not either algorithm's squared bias, and is not Delta MSE. E4 estimates U (sampling-corrected squared finite-tail mean), V (between-seed variance of time-averaged models), and total MSE separately. A single chronological checkpoint has a different variance. Full-vector effects and frozen-direction projections are both saved.

## Uncertainty

All resampling is at the 12-paired-seed level, conditionally on the saved dataset/protocol. Neither coordinates nor chronological batches are independent inference units. Scalar and vector-ball families are separately nominal 95%. Small-sample bootstrap and jackknife are sensitivities, not exact coverage guarantees. Nonlinear norm/cosine estimators have finite-sample bias, especially near zero/unit values. No proxy remainder, dataset uncertainty, stationarity error or publication-selection uncertainty is included.

## Retained unfavorable outcomes

- All six non-H1 K64 proxy amplitudes overpredict.
- H4/H2 prefactor ratio 3.5 is not supported by the matched finite-grid ratio; no fitted scale hides this.
- Short-window alignment can be substantially weaker.
- E4 has 0/144 passed temporal-equivalence gates and no certified crossover.
- Historical H4 target exclusions, H8 finite-grid discrepancy/exclusions and H1 long-horizon numerical issues are retained in `prior_e4/historical/`, `inputs/full_results.csv` and `inputs/per_run_estimates.csv`. They are not evaluated away by E5.
- The training-objective difference is tiny; held-out SCAFFOLD loss is slightly lower, not worse. No predictive harm or optimal policy follows.
- Only the two preexisting E4_v2 pilot seeds were run previously; the 48-seed E4_v2 extension remains unexecuted. E5 did not run it.

> This post-hoc analysis uses a reference-point plug-in coefficient on a single shared-objective logistic dataset with state-dependent minibatch noise and finite averaging windows. It is not a test or extension of the additive-noise stationary theorem, does not isolate its specific control coefficient from other finite-step and state-dependent-noise effects, and does not certify stationarity or bias-variance crossover. Its seed-resampling intervals do not cover proxy approximation/remainder or dataset uncertainty. No predictive harm, universal algorithm ranking, or optimal choice of H or step size is established.
