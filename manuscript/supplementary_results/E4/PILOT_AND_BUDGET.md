# E4_v2 Pilot And Budget

Written after E4_v1 replay and before any new training. This is a separate,
data-informed extension, not a retroactive alteration of E4_v1.

## Why A Minimal Extension

All actual global-model averages are reconstructible. The gap is precision and
temporal interpretation, not missing averages: the primary SCAFFOLD point estimate
crosses at K=32 and64, but only K=64 has a positive simultaneous U-V lower bound.
The frozen temporal equivalence gates are not passed. This is not evidence of
nonstationarity, nor a scientific rejection of a bias floor.

## Prespecified Smallest Scope

Only R0 H=4,N=128,m=2,gamma=0.196078431372549. The frozen objective, reference,
data and unchanged v1 arithmetic are retained. Fresh paired pilot seeds30001,
30002 use burn25,600rounds (4x historical) and128 chronological batches of1,280
rounds (2x historical tail). Their R=2 output is a cost/numerical/temporal pilot,
not a powered significance study. No favorable seed selection or pooling.

## Cost Before Execution

Historical N128 pairs took median57.858seconds per88,320rounds. Each pilot has
189,440rounds, a2.145x ratio, giving124.1seconds perpair; two approximately4.14
minutes serial plus JIT, checkpoint compression and I/O. The execution cap is
600seconds for these two pilots, checked at deterministic chunk boundaries.
Unfinished work is checkpointed, not called a negative result.

The proposed separate production block is48 fresh pairs (31001..31048), burn
25,600 and1,024batches of1,280rounds. Perpair1,336,320rounds,15.130x historical:
about14.59minutes/pair or11.67hours serial; ideal four-worker2.92hours is only
a hardware-throughput bound, not a guaranteed walltime. Original engine full
control-history storage projects about6.55GB for48results, plus checkpoints.
Compact true global sums/counts/trace squares would be approximately106MB
uncompressed for all48; complete checkpoints remain local and cannot be replaced
by compact arrays for continuation.

The planning precision proxy scales the current primary first/last-half projected
halfwidth0.000646 by sqrt(12/48 *32/512), yielding about0.000081 versus the frozen
0.0001 equivalence margin. This is optimistic: autocorrelation, actual drift,
bootstrap critical values and hardware variability can invalidate the prediction.
It is not a power guarantee or a stationary certificate. This is the smallest
experimental *scope*, not a claim that the cost design is uniquely optimal.

## Execution And Resume

Freeze E4_v2 before pilots. Run only the two feasible pilots in this task. The
48-run production extension is PLANNED_NOT_EXECUTED, because its cost is much
larger than the bounded diagnostic step. Exact commands are in REPRODUCE.md.
All historical archives and manuscript files remain read-only. Any newly observed
numerical/control drift is retained; unchanged arithmetic does not resolve prior
H=1 full-horizon failures. No controlled E1 bridge is claimed as executed.
