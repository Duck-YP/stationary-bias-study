# Table 18: Direct versus balance discrepancies

Status: **partial**. Section C.3.1, page 35.

Partial: saved per-run summaries supply coefficients and means, but not the original per-run combined-SE threshold. No uncertainty is recomputed. H=4,N=16,j=2 formats to -0.1080237 from the saved value; the paper displays -0.1080240, consistent with six-place rounding followed by a trailing zero, but no saved formatting rule establishes that history.

| H | N | Coordinate | Balance coefficient | Direct coefficient | Absolute mean difference | 3 x combined SE | Source seed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 16 | 2 | -0.0408082 | 0.924598 | 0.00377112 | UNAVAILABLE | 1108 |
| 2 | 48 | 1 | -0.0323449 | 3.070686 | 0.00134680 | UNAVAILABLE | 1103 |
| 4 | 16 | 2 | -0.1080237 | 0.841309 | 0.00370833 | UNAVAILABLE | 1108 |
| 4 | 48 | 1 | -0.0933450 | 2.615233 | 0.00117560 | UNAVAILABLE | 1103 |

Sources:

- `artifacts/canonical_paper_export/original/p3_multidimensional_fedavg_attribution/artifacts/formal/p3-d2-coefficient-primary/run_summary.csv`
