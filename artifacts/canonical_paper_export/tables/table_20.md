# Table 20: Real-data settings

Status: **partial**. Section C.4.1, page 37.

tab:num-real-settings; normalized source-backed protocol inventory, not verbatim manuscript layout. Not covered: sampling-with-replacement rule and L_sample/base-step formula are not structured fields in the selected protocols (actual gamma values are saved); the label conversion to {0,1}, equal-client weighting, random-IID and two-label-shards construction are not regenerated from regime identifiers alone; the prose distinction between one primary and two alternative partitions is not inferred solely from the saved partition-seed set

| study / component | saved field / derivation | value |
| --- | --- | --- |
| Training data and preprocessing | retained_count | 32512 |
| Training data and preprocessing | excluded_count | 49 |
| Training data and preprocessing | subset_seed | 20261009 |
| Training data and preprocessing | preprocessing | row / max(1,l2 norm), then intercept=1; lambda=.01 on all 124 coordinates |
| a9a | dataset validation | {"rows": 32561, "declared_features": 123, "observed_max_feature": 123, "unique_features": 123, "labels": [-1, 1], "parameters": 124} |
| a9a.t | dataset validation | {"rows": 16281, "declared_features": 123, "observed_max_feature": 122, "unique_features": 122, "labels": [-1, 1], "parameters": 124} |
| Objective | regularization and evaluation metadata | {"lambda": 0.01, "all_124_coordinates_regularized": true, "train": "frozen retained32512 uniform rows", "test": "frozen a9a.t16281 rows with same row normalization and intercept", "evaluate": "each individual run model Y, not mean checkpoint losses", "prediction_claim": "no claim of consequential predictive harm from parameter share alone; report absolute and baseline-relative test change"} |
| Training | independent paired runs per configuration | 12 |
| Client-objective configurations | regime | ["R0", "R1", "R2"] |
| Client-objective configurations | partition_seed | [0, 4101, 4102, 4103] |
| Fixed-budget shared allocations | N,m,H,gamma and N*m | [{"N": 8, "m": 32, "H": 4, "gamma": 0.196078431372549, "N*m": 256}, {"N": 32, "m": 8, "H": 4, "gamma": 0.196078431372549, "N*m": 256}, {"N": 128, "m": 2, "H": 4, "gamma": 0.196078431372549, "N*m": 256}] |
| Additional shared-objective runs | all shared configuration metadata | [{"id": "E3_R0_p0_H4_N8_g0.196078431373", "H": 4, "N": 8, "m": 32, "gamma": 0.196078431372549, "roles": ["allocation"]}, {"id": "E3_R0_p0_H4_N32_g0.196078431373", "H": 4, "N": 32, "m": 8, "gamma": 0.196078431372549, "roles": ["allocation"]}, {"id": "E3_R0_p0_H4_N128_g0.196078431373", "H": 4, "N": 128, "m": 2, "gamma": 0.196078431372549, "roles": ["allocation"]}, {"id": "E3_R0_p0_H4_N32_g0.0980392156863", "H": 4, "N": 32, "m": 8, "gamma": 0.0980392156862745, "roles": ["policy"]}, {"id": "E3_R0_p0_H4_N32_g0.0490196078431", "H": 4, "N": 32, "m": 8, "gamma": 0.04901960784313725, "roles": ["policy"]}, {"id": "E3_R0_p0_H2_N32_g0.196078431373", "H": 2, "N": 32, "m": 8, "gamma": 0.196078431372549, "roles": ["policy"]}, {"id": "E3_R0_p0_H1_N8_g0.196078431373", "H": 1, "N": 8, "m": 32, "gamma": 0.196078431372549, "roles": ["negative_control"]}, {"id": "E3_R0_p0_H1_N32_g0.196078431373", "H": 1, "N": 32, "m": 8, "gamma": 0.196078431372549, "roles": ["negative_control"]}, {"id": "E3_R0_p0_H1_N128_g0.196078431373", "H": 1, "N": 128, "m": 2, "gamma": 0.196078431372549, "roles": ["negative_control"]}] |
| Additional shared-objective runs | shared configuration count | 9 |
| Averaging windows | K | [1, 2, 4, 8, 16, 32, 64] |
| Averaging windows | primary_cell | E3_R0_p0_H4_N128_g0.196078431373 |
| Averaging windows | same_end_batch | 64 |
| Averaging windows | algorithms | ["SCAFFOLD", "FedAvg"] |
| Primary averaging horizon | saved schedule | {"tau0": 128, "burn": 6400, "batch_length": 1280, "batches": 64, "primary_batches": 64, "sensitivity": "none"} |
| Primary averaging horizon | derived horizon and example-gradient evaluations per algorithm | {"longest_window_rounds": 81920, "end_round": 88320, "example_gradient_evaluations_per_algorithm": 90439680} |
| Longer-run pilots | pilot count and frozen schedule | {"pilot_runs": 2, "burn": 25600, "batch_length": 1280, "batches": 128, "primary_batches": 128, "total_rounds": 189440} |

Sources:

- `manuscript/supplementary_results/DATA_MANIFEST.json`
- `manuscript/supplementary_results/E4/E4_v1_PROTOCOL_FROZEN.json`
- `configs/supplementary/PROTOCOL_FROZEN.json`
- `manuscript/supplementary_results/E4/E4_v2_PROTOCOL_FROZEN.json`
