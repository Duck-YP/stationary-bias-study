# Rotation-equivariance report, d=2

## Classification

EMPIRICAL / NUMERICAL SANITY

## Source provenance

- Source commit: `85e97fa34e23084410c148b63d814c75d92dbc1e`
- Source dirty at run start: `False`
- Config SHA-256: `d82bf75525e66a7ea4d1da1e484f5c40633ca0d26745c5e5a4096a6fa01944fa`
- Protocol SHA-256: `9360e34f2963b1c3ca6fae12c443195c55d0086bb55a2b50dd006af894c39301`

## Frozen transformation

```text
[[ 0.8660254037844386 -0.5               ]
 [ 0.5                 0.8660254037844386]]
```

## Matrix and seeds

- Matrix: `p2-d2-rotation-invariance`
- Pairs: 16
- Seeds: 1101, 1102, 1103, 1104
- Communication rounds: 200

## Theory gates

| Gate | H | Residual | Threshold | Pass |
|---|---:|---:|---:|:---:|
| R0 |  | 1.570092e-16 | 1.000000e-14 | True |
| R1 |  | 5.474255e-16 | 1.000000e-13 | True |
| R2 |  | 5.694968e-16 | 1.000000e-13 | True |
| R3 |  | 3.554448e-16 | 1.000000e-13 | True |
| R4 |  | 2.597223e-16 | 1.000000e-12 | True |
| R5 |  | 4.514582e-16 | 1.000000e-12 | True |
| R6 | 2 | 4.824185e-16 | 1.000000e-12 | True |
| R6 | 4 | 2.063081e-16 | 1.000000e-12 | True |

## Pathwise residuals

| Pair | H | N | Seed | r_x | r_xi | r_qbar | r_max | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N16__g0p0625000000__seed1101 | 2 | 16 | 1101 | 2.477185e-15 | 2.678413e-15 | 5.377643e-17 | 2.678413e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N16__g0p0625000000__seed1102 | 2 | 16 | 1102 | 1.242062e-15 | 1.887379e-15 | 5.363413e-17 | 1.887379e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N16__g0p0625000000__seed1103 | 2 | 16 | 1103 | 1.693090e-15 | 2.442491e-15 | 5.421011e-17 | 2.442491e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N16__g0p0625000000__seed1104 | 2 | 16 | 1104 | 2.130240e-15 | 2.442491e-15 | 5.361380e-17 | 2.442491e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N64__g0p0156250000__seed1101 | 2 | 64 | 1101 | 1.149081e-14 | 1.576517e-14 | 5.366801e-17 | 1.576517e-14 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N64__g0p0156250000__seed1102 | 2 | 64 | 1102 | 7.320533e-15 | 1.476597e-14 | 5.370189e-17 | 1.476597e-14 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N64__g0p0156250000__seed1103 | 2 | 64 | 1103 | 9.183626e-15 | 1.199041e-14 | 5.363413e-17 | 1.199041e-14 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H2__N64__g0p0156250000__seed1104 | 2 | 64 | 1104 | 2.813721e-15 | 7.993606e-15 | 2.764716e-17 | 7.993606e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N16__g0p0625000000__seed1101 | 4 | 16 | 1101 | 6.696033e-16 | 9.992007e-16 | 2.732189e-17 | 9.992007e-16 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N16__g0p0625000000__seed1102 | 4 | 16 | 1102 | 6.140921e-16 | 8.604228e-16 | 5.358669e-17 | 8.604228e-16 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N16__g0p0625000000__seed1103 | 4 | 16 | 1103 | 6.349088e-16 | 9.992007e-16 | 2.775558e-17 | 9.992007e-16 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N16__g0p0625000000__seed1104 | 4 | 16 | 1104 | 8.049117e-16 | 1.332268e-15 | 5.353248e-17 | 1.332268e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N64__g0p0156250000__seed1101 | 4 | 64 | 1101 | 3.040970e-15 | 5.606626e-15 | 5.393906e-17 | 5.606626e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N64__g0p0156250000__seed1102 | 4 | 64 | 1102 | 6.279699e-16 | 2.720046e-15 | 5.355959e-17 | 2.720046e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N64__g0p0156250000__seed1103 | 4 | 64 | 1103 | 1.630640e-15 | 3.774758e-15 | 2.737610e-17 | 3.774758e-15 | True |
| p2__phase-rotation__matrix-p2-d2-rotation-invariance__H4__N64__g0p0156250000__seed1104 | 4 | 64 | 1104 | 4.116499e-15 | 4.329870e-15 | 5.361930e-17 | 4.329870e-15 | True |

## Global pathwise gate

- max r_x: `1.149081e-14`
- max r_xi: `1.576517e-14`
- max r_qbar: `5.421011e-17`
- Theory gates pass: `True`
- Every pathwise pair passes: `True`

## Optional estimator diagnostics

No optional estimator-equivariance diagnostic was recorded.

## Interpretation boundary

The numerical result checks implementation and representation consistency under the
pre-registered 30-degree transformation. It is not a new proof, an independent
coefficient validation, a universal coordinate-invariance result, or evidence about
another noise law, d=5, or heterogeneity.
