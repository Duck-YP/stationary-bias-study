# Table 7: Controlled experimental settings

Status: **supported**. Section C.1.1, page 28.

tab:num-controlled-settings; all seven numerical designs. Joint-path N and gamma lists are paired in source order; supplementary unique sets summarize Cartesian designs. Supplementary dimension is derived from saved coordinate indices, not imported from manuscript prose.

| comparison | dimension | H | client counts N | step sizes gamma | runs per configuration |
| --- | --- | --- | --- | --- | --- |
| Primary joint grid | 2 | [2, 4] | [12, 16, 24, 32, 48] | ["1/12", "1/16", "1/24", "1/32", "1/48"] | 8 |
| Smaller-step joint grid | 2 | [4] | [64, 96, 128, 192] | ["1/64", "1/96", "1/128", "1/192"] | 8 |
| Fixed-step client count | 2 | [2] | [8, 16, 32, 64, 128] | ["1/24"] | 8 |
| Five-dimensional | 5 | [2, 4] | [32, 48, 64, 96, 128] | ["1/32", "1/48", "1/64", "1/96", "1/128"] | 8 |
| Leading coefficient | 2 | [1, 2, 4, 8] | [32] | ["1/64", "1/128", "1/256", "1/512"] | 12 |
| Cartesian control coefficient | 2 | [2, 4, 8] | [32, 64, 128] | ["1/128", "1/256", "1/512"] | 12 |
| Contraction/noise law | 2 | [4] | [64, 128] | ["1/512", "1/1024", "1/2048"] | 12 |

Sources:

- `configs/original/p2_multidimensional_validation/configs/d2_coefficient_primary.yaml`
- `configs/original/p2_multidimensional_validation/configs/d2_h4_small_step_confirmation.yaml`
- `configs/original/p2_multidimensional_validation/configs/d2_fixed_gamma_largeN_plateau.yaml`
- `configs/original/p2_multidimensional_validation/configs/d5_controlled_validation.yaml`
- `configs/supplementary/PROTOCOL_FROZEN.json`
- `manuscript/supplementary_results/fitted_coefficients.csv`
- `artifacts/canonical_paper_export/targeted_mechanism/PROTOCOL_FROZEN.json`
- `artifacts/canonical_paper_export/targeted_mechanism/certificate/independent_model_checks.json`
