# Scientific Summary

**Decision: INCONCLUSIVE for a certified stationary practical effect in the tested setting.**

**Final classification: INCONCLUSIVE_PRECISION_OR_STATIONARITY.**

Model averaging clearly changes the *parameter-error* interpretation of the old
R0 results. It does not yet establish a stationary error floor or predictive harm.
No manuscript was edited, no historical output was replaced, and no favorable
configuration/window/seed was selected after seeing results.

## What Was Actually Executed

E4_v1 reused all9 frozen R0 production configurations and12 paired seeds per
configuration, reconstructing1,512 individual within-run time-averaged models
over K=1,2,4,8,16,32,64. Each model's frozen train objective and held-out logloss
was evaluated. Primary setting: H=4,N=128,m=2,gamma=0.196078431372549.
K=1 already averages1,280 global rounds; K=64 averages81,920 rounds, ending at
round88,320 after burn6,400. Neither is a single raw checkpoint.

E4_v2 separately froze and executed two fresh paired diagnostic pilots, seeds
30001,30002, each189,440rounds with4x historical burn and2x tail. All128 batches
completed. They are unpowered R=2 pilots, not pooled into E4_v1 and not a completed
48-seed production extension. The planned48-run extension remains NOT_EXECUTED.

## Averaging Reduces Variance; Bias Is No Longer A Tiny MSE Fraction

At primary K=64, simultaneous95% primary-family intervals are:

| Quantity | SCAFFOLD | FedAvg |
|---|---:|---:|
| Signed squared-bias U |1.17637e-5 [1.00517e-5,1.34757e-5]|5.38584e-6 [4.12501e-6,6.64667e-6]|
| Averaged-model variance V |5.50288e-6 [4.43541e-6,6.57035e-6]|5.49197e-6 [4.43129e-6,6.55265e-6]|
| Total averaged-model MSE |1.72666e-5 [1.53826e-5,1.91506e-5]|1.08778e-5 [9.45895e-6,1.22967e-5]|
| Signed U/MSE share |68.13% [62.56%,73.70%]|49.51% [41.13%,57.89%]|

Between-run variance falls approximately57-fold from K=1 to64 for both algorithms;
the simultaneous variance-change intervals exclude zero. This reduction was
measured, not imposed as1/K. Raw-checkpoint variance remains a separate reference
near0.00236. The old raw-checkpoint MSE bias shares0.50%/0.23% cannot be used as
the averaged-model shares. MSE=U+V holds to numerical precision and negative U
estimates, including FedAvg at K=1, are retained without clipping.

The10% parameter-MSE benchmark is exceeded by the primary K=64 share intervals.
It is a researcher-chosen materiality reference, not a universal loss threshold,
stationarity certificate, or sufficient condition for practical predictive harm.

## No Certified Crossover

SCAFFOLD has a **descriptive** U>=V crossover at K=32 and64. Only K=64 has a
positive simultaneous U-V lower bound, also surviving the Bonferroni jackknife
sensitivity. K=32's lower bounds include zero. Thus the required two-consecutive-K
uncertainty criterion fails even before temporal stability is considered.
FedAvg has no descriptive crossover on this grid.

All144 prespecified temporal equivalence gates fail. For primary SCAFFOLD's
first/last32 comparison, mean drift norm is0.0013633 and its simultaneous upper
bound0.0054372, above the frozen0.001 margin. The projected drift interval is
[-0.0005438,0.0007484], not contained in the frozen +/-0.0001 margin. This does
**not** establish nonstationarity: stochastic precision can explain the failure.
There is no distinct equal-length64-batch anchor; K=64 inherits the32-batch gate.
Consequently both algorithms are labeled **NO_CERTIFIED_CROSSOVER** and all
estimates are **post-burn-in finite-tail**, not certified stationary quantities.

## SCAFFOLD-FedAvg Differences And Actual Loss Effects

At K=64 the paired SCAFFOLD-minus-FedAvg differences are:

| Estimand | Estimate | Simultaneous95% interval |
|---|---:|---:|
| Frozen mean projection |0.00110323|[0.00109264,0.00111382]|
| Squared-bias difference |6.37787e-6|[5.84789e-6,6.90785e-6]|
| Averaged variance difference |1.09082e-8|[-3.57958e-8,5.76122e-8]|
| **Total MSE difference** |6.38878e-6|[5.82987e-6,6.94769e-6]|
| Train-objective gap difference |3.64095e-7|[3.35523e-7,3.92667e-7]|
| **Held-out logloss difference** |-3.26925e-5|[-3.30779e-5,-3.23071e-5]|

SCAFFOLD's parameter MSE is about58.7% higher relative to FedAvg at this averaged
window, primarily associated with squared mean displacement, not a resolved
variance difference. The cross correction is essential:
Delta U=2 C_U+U_delta=2*(2.57965e-6)+1.21856e-6.
The squared mean difference alone is not Delta U or Delta MSE.

The train objective penalties are very small in absolute scale: mean gaps
7.24676e-7 and3.60581e-7 versus f(x_ref)=0.4758413. Conversely SCAFFOLD has a
slightly **better** test logloss0.4248891 versus0.4249218, with a difference only
about0.00769% of the reference test loss0.4249899. Statistical detectability under
paired streams is not evidence of consequential prediction harm. The test set is
fixed; these seed intervals do not cover population/test-sampling uncertainty.

## Controls, Scope And Remaining Work

All secondary allocation and diagnostic cells remain in the tables. At K=64,
N=32 SCAFFOLD/FedAvg point shares are14.97%/7.77%; N=8 shares1.61%/0.97%.
Their squared-bias intervals have weak/zero-bias identification and their
temporal gates fail. They were not dropped because results were less favorable.

R0 uses shared empirical objectives, full participation, convex regularized
logistic regression and state-dependent minibatch noise. This is implication
evidence, not a generic heterogeneous theorem or isolation of the homogeneous
gamma^2 control coefficient: **CONTROL_COEFFICIENT_NOT_ISOLATED_IN_REAL_DATA**.
No E1 bridge was run. The leading B11's fixed-H independence does not apply to
all bias terms or the H-dependent remainder. Historical H=4 exclusions, H=8
finite-grid discrepancies and original long-horizon H=1 arithmetic issues are
preserved in historical inputs and explicitly remain unresolved.

The new pilots show finite models over their complete horizons and control
zero-sum residuals up to6.50e-11, without changing arithmetic. Their R=2 results
cannot settle significance or stationarity. Pre-run extension cost was11.67hours
serial; actual pilot throughput revises that planning proxy to about5.93hours,
not a guarantee. Full production and its separate inference are not claimed as
completed. See PILOT_AND_BUDGET.md, MISSING_ITEMS.md and REPRODUCE.md.

**Bottom line:** averaging makes systematic finite-tail mean displacement a
substantial share of parameter error in the primary setting. Evidence is not yet
sufficient to call it a certified stationary, operationally harmful error floor.
Larger parameter error here does not translate into worse held-out prediction.
