# Table 19: Structural consistency settings

Status: **partial**. Section C.3.2, page 36.

tab:num-structural-settings; normalized source-backed protocol inventory, not verbatim manuscript layout. Not covered: affine gamma is absent from E2_exact_checks.csv; affine offset construction a_c=+/-rho*u, translated initialization and matched-noise semantics are not fields in the selected structured affine evidence

| study / component | saved field / derivation | value |
| --- | --- | --- |
| Orthogonal rotation | coordinate_transform | {"dimension": 2, "angle": "pi / 6", "angle_degrees": 30, "angle_radians": 0.5235987755982988, "Q": [[0.8660254037844386, -0.5], [0.5, 0.8660254037844386]], "convention": {"forward": "y = Q @ x", "inverse": "x = Q.T @ y", "objective_identity": "f_rot(y) = f(Q.T @ y)", "gradient_identity": "grad_f_rot(y) = Q @ grad_f(Q.T @ y)"}, "orthogonality_identity": "Q.T @ Q = I"} |
| Orthogonal rotation | paired_matrix | {"dimension": 2, "communication_rounds": 200, "H_values": [2, 4], "settings": [{"N": 16, "gamma_numerator": 1, "gamma_denominator": 16}, {"N": 64, "gamma_numerator": 1, "gamma_denominator": 64}], "seeds": [1101, 1102, 1103, 1104], "paired_run_count": 16, "systems_per_pair": ["original", "rotated"], "pair_definition": "one original-coordinate run and one rotated-coordinate run with matched noise blocks"} |
| Orthogonal rotation | noise_coupling | {"original_construction": "epsilon = cholesky(C) @ z", "base_coordinates": "independent Rademacher", "generate_original_epsilon_once": true, "rotated_construction": "epsilon_rot = Q @ epsilon", "covariance_identity": "Cov(epsilon_rot) = Q @ C @ Q.T = C_rot", "same_realization_across_each_pair": ["seed", "communication_round", "local_step", "client"], "independently_generate_from_C_rot": "forbidden", "fresh_rotated_draw": "forbidden", "rationale": "Rademacher noise is not rotationally invariant"} |
| Orthogonal rotation | initialization | {"x0": [0.2, -0.1], "x0_rot_construction": "x0_rot = Q @ x0", "x0_rot": [0.223205080756888, 0.013397459621556], "xi_by_client": "zero", "xi_rot_by_client": "zero"} |
| Affine translation | N values | [8, 32] |
| Affine translation | H values | [2, 4, 8] |
| Affine translation | rho values | [0.0, 0.25, 0.5, 1.0] |
| Affine translation | rounds values | [2000] |
| Affine translation | saved configuration count | 24 |

Sources:

- `configs/original/p2_multidimensional_validation/configs/d2_rotation_invariance.yaml`
- `manuscript/supplementary_results/tables/E2_exact_checks.csv`
