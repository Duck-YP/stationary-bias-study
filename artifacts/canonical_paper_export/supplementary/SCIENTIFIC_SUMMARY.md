# Scientific summary

1. E0/E2 implementation: the original 13 E0 test groups and the added checkpoint-file test pass. Tests include reference/production agreement, short H=1 paths with nonzero zero-sum controls, quadratic exact covariance for all H, noncommuting A/C, derivatives, rotation, keyed-noise covariance, and exact chunk-resume trajectories. E2 passes 24 affine-shift cells at 2000 rounds each; max control translation residual=1.64313e-14. However, the extended full-horizon real-data H1 audit finds float64 accumulation beyond strict 1e-10 tolerance in some original v1 runs. This numerical issue and the separate stable endpoint-increment audit are disclosed below; there is no blanket claim that every long identity check passes. A full-grid improved-arithmetic rerun has not been executed. E2zero transient diagnostics and deterministic fixed-point reports are separate evidence.

2. B11 independent intercepts: the following fits use all four gamma points, with no subtraction of B11 or shared fitted intercept. H=1 is boundary recursion consistency. Intercept contrasts and omitted-largest-gamma sensitivity are saved. The primary H=8 SCAFFOLD intercept differs from H=2 on both adjusted-coordinate contrasts. Removing the largest gamma moves the H=8 estimates toward the target but does not replace the primary result. Thus all-H compatibility is not supported on this finite grid; deterministic curvature/remainder remains an open explanation, rather than a refutation of the fixed-H asymptotic theorem. Compatibility is a finite-grid empirical question; CI target inclusion is not a proof.

- scaffold, H=1, coordinate=0: -0.024530843, nominal CI [-0.024959734, -0.024101952], target=-0.024459428.
- scaffold, H=1, coordinate=1: -0.030663554, nominal CI [-0.031199668, -0.030127439], target=-0.030574285.
- fedavg, H=1, coordinate=0: -0.024530843, nominal CI [-0.024959734, -0.024101952], target=-0.024459428.
- fedavg, H=1, coordinate=1: -0.030663554, nominal CI [-0.031199668, -0.030127439], target=-0.030574285.
- scaffold, H=2, coordinate=0: -0.024431673, nominal CI [-0.025068185, -0.023795161], target=-0.024459428.
- scaffold, H=2, coordinate=1: -0.030553633, nominal CI [-0.031349278, -0.029757988], target=-0.030574285.
- fedavg, H=2, coordinate=0: -0.02441281, nominal CI [-0.025051169, -0.023774451], target=-0.024459428.
- fedavg, H=2, coordinate=1: -0.030525461, nominal CI [-0.031323409, -0.029727513], target=-0.030574285.
- scaffold, H=4, coordinate=0: -0.025168847, nominal CI [-0.02595286, -0.024384835], target=-0.024459428.
- scaffold, H=4, coordinate=1: -0.031537194, nominal CI [-0.032517051, -0.030557337], target=-0.030574285.
- fedavg, H=4, coordinate=0: -0.024799163, nominal CI [-0.025574489, -0.024023836], target=-0.024459428.
- fedavg, H=4, coordinate=1: -0.03104375, nominal CI [-0.032012814, -0.030074685], target=-0.030574285.
- scaffold, H=8, coordinate=0: -0.028252126, nominal CI [-0.029045717, -0.027458536], target=-0.024459428.
- scaffold, H=8, coordinate=1: -0.035610381, nominal CI [-0.036602366, -0.034618397], target=-0.030574285.
- fedavg, H=8, coordinate=0: -0.025913033, nominal CI [-0.026711728, -0.025114337], target=-0.024459428.
- fedavg, H=8, coordinate=1: -0.032560214, nominal CI [-0.033558702, -0.031561726], target=-0.030574285.

3. Control H dependence: the full Cartesian gamma x 1/N grid is fitted separately for H. H=2 and H=4 primary intercepts are close to objective-derived targets; the H4-minus-3.5-H2 adjusted contrast contains zero in both coordinates. H=8 has a small resolved nominal primary target gap that shrinks in the smaller-gamma window; Monte Carlo error alone does not explain all finite-grid displacement. The following intercepts and all H=4 residuals are retained. kappa(4)/kappa(2)=3.5 is exact algebra; the difference contrast and nested-window sensitivity remain descriptive. A nonzero target gap can reflect deterministic finite-grid remainder, implementation/theory questions, or finite precision and must not be relabeled to obtain target inclusion.

- matched_algorithm_difference, H=2, coordinate=0: -0.015995458, nominal CI [-0.016011586, -0.01597933], target=-0.016001339.
- matched_algorithm_difference, H=2, coordinate=1: -0.019994077, nominal CI [-0.020014218, -0.019973937], target=-0.020001673.
- matched_algorithm_difference, H=4, coordinate=0: -0.055952256, nominal CI [-0.056011095, -0.055893418], target=-0.056004686.
- matched_algorithm_difference, H=4, coordinate=1: -0.069936561, nominal CI [-0.070009986, -0.069863136], target=-0.070005857.
- matched_algorithm_difference, H=8, coordinate=0: -0.13962104, nominal CI [-0.13983973, -0.13940235], target=-0.14001171.
- matched_algorithm_difference, H=8, coordinate=1: -0.17449119, nominal CI [-0.17476345, -0.17421894], target=-0.17501464.

4. Real-data fixed-budget implications: both algorithms use 256 example gradients per local-step level. R0 reference aggregate covariance is invariant across allocations. R1/R2 centered aggregate covariance changes with partition/N, as the measured partition table shows. Conditional-on-partition inference is separate from seed4102/4103 sensitivity. Values below are direct finite-tail means; U-statistic, matched differences, and uncertainty are in full_results.csv.

- R0 N=8 scaffold: projection=0.0003185 [0.000184964,0.000452035], variance=0.00235106, MSE=0.00235114, held-out log loss=0.424981.
- R0 N=8 fedavg: projection=0.000256556 [0.000122917,0.000390194], variance=0.00235088, MSE=0.00235093, held-out log loss=0.424983.
- R0 N=32 scaffold: projection=0.000956707 [0.000786136,0.00112728], variance=0.00236205, MSE=0.0023629, held-out log loss=0.424961.
- R0 N=32 fedavg: projection=0.000685051 [0.000514414,0.000855687], variance=0.00236135, MSE=0.00236175, held-out log loss=0.42497.
- R0 N=128 scaffold: projection=0.00343217 [0.00326185,0.0036025], variance=0.00236269, MSE=0.00237445, held-out log loss=0.424889.
- R0 N=128 fedavg: projection=0.00232894 [0.00215974,0.00249815], variance=0.00236009, MSE=0.00236548, held-out log loss=0.424922.
- R1 N=8 scaffold: projection=0.000340629 [0.000213218,0.00046804], variance=0.0023457, MSE=0.00234577, held-out log loss=0.424978.
- R1 N=8 fedavg: projection=0.00026804 [0.000140249,0.00039583], variance=0.00234527, MSE=0.00234535, held-out log loss=0.424981.
- R1 N=32 scaffold: projection=0.000880445 [0.000638315,0.00112257], variance=0.00236538, MSE=0.00236612, held-out log loss=0.424963.
- R1 N=32 fedavg: projection=0.000472472 [0.000229759,0.000715186], variance=0.0023639, MSE=0.00236431, held-out log loss=0.424977.
- R1 N=128 scaffold: projection=0.0035535 [0.00339264,0.00371435], variance=0.00235178, MSE=0.00236422, held-out log loss=0.424884.
- R1 N=128 fedavg: projection=0.00199407 [0.00182971,0.00215843], variance=0.00234622, MSE=0.00235073, held-out log loss=0.424936.
- R2 N=8 scaffold: projection=0.000242938 [5.03633e-05,0.000435513], variance=0.00225247, MSE=0.00225263, held-out log loss=0.424984.
- R2 N=8 fedavg: projection=-0.0392976 [-0.0394909,-0.0391044], variance=0.00215886, MSE=0.00567907, held-out log loss=0.426589.
- R2 N=32 scaffold: projection=0.00035198 [0.000143092,0.000560868], variance=0.00221774, MSE=0.00221801, held-out log loss=0.424981.
- R2 N=32 fedavg: projection=-0.0558914 [-0.0560964,-0.0556864], variance=0.00208774, MSE=0.00906664, held-out log loss=0.427274.
- R2 N=128 scaffold: projection=0.00125578 [0.00109555,0.00141601], variance=0.00219401, MSE=0.00219561, held-out log loss=0.424956.
- R2 N=128 fedavg: projection=-0.0620267 [-0.0621818,-0.0618715], variance=0.00204808, MSE=0.0107951, held-out log loss=0.427548.

5. Reducing gamma and reducing H: tables/E3_policy_allocation_contrasts.csv retains signed contrasts against the fixed N=32,H=4 baseline. No gamma^2 scaling or algorithm ranking is imposed. Mean-model training gap differs from held-out loss and from stationary expected raw-checkpoint loss. Finite-tail per-run average-model evaluation is not a free pooled checkpoint.

6. Accuracy and limitations: reference gradient norm=1.25292e-16, absolute parameter certificate=1.25292e-14, independent optimizer distance=8.42829e-15. Completed production=69/69 cells (828/828 paired runs). Monte Carlo precision flags, raw/balance paired differences, batch autocorrelation proxies, first/last-half contrasts and correlated 2x burn/tail sensitivities are saved. Nominal CIs do not cover remainder, burn-in, or optimizer error. Resource limits are recorded independently of inference.

7. Integration: the limited affine state translation and directly measured implementation/empirical results are eligible for review. General heterogeneous coefficient theorems, whole-bias H independence, theorem certification by CI inclusion, universal algorithm ranking, and interpreting unresolved precision as no practical effect are unsupported. Candidate figures/LaTeX drafts are supplementary material; no original H=4 discrepancies were replaced. The built-in LaTeX compiler returned a platform-directory failure, so source compilation is unverified (diagnostics/latex_compilation.json); Matplotlib figure PDF/SVG/PNG files were generated successfully.

Observed interpretation: on R0, the frozen signed mean displacement increases from N=8 to N=128 under fixed total minibatch budget, while raw variance stays near 0.00235. The held-out log loss can improve even as parameter displacement increases, so these estimands are not interchangeable. In R2, the large FedAvg mean displacement includes deterministic label-heterogeneity drift: the independently solved N=32,H=4 deterministic FedAvg point is about 0.08365 from x_ref. Its stochastic algorithm difference cannot be called a pure control-noise coefficient. Reducing gamma and H changes these measured quantities differently; full numeric policy contrasts remain primary. These descriptions are conditional on this objective and frozen partitions, with precision flags preserved.

Extended long-run accuracy audit: 48 of 132 stored H1 within-configuration/cross-allocation checks exceed the absolute 1e-10 comparison used in that additional audit. The original 14 short-path E0 checks and E2 affine checks still pass; no tolerance has been relaxed. Measured maximum within-algorithm H1 vector discrepancy is about 7.54e-10, with scale-normalized discrepancy about 1.86e-10, so a 1e-10 scale-aware bound also does not cover every long run. These are float64 accumulation diagnostics, not scientific counterexamples or trajectories that diverged. The affected configurations are explicitly flagged by numerical_identity_status in the registry/results. Their execution is complete; machine-precision identity validation is not claimed. A separately implemented endpoint-increment kernel is tested in diagnostics/stable_arithmetic_roundoff_audit.csv with the same indices/horizons and no control projection. It does not replace frozen v1 results or fits, and no full-grid stable-kernel production rerun has been performed. A future v2 protocol must preserve v1 artifacts, use explicit source hashes and new independent seeds if new sampling is added.
