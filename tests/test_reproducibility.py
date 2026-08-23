import numpy as np

from stationary_bias.project_io import load_configs
from stationary_bias.simulation import RunSpec, build_run_matrix, matrix_audit, simulate_setting


def test_raw_batch_summaries_are_seed_reproducible() -> None:
    configs = load_configs()
    spec = RunSpec(
        experiment="smoke",
        control_name="",
        objective="nonlinear_main",
        noise="rademacher",
        H=2,
        N=4,
        gamma=0.05,
        seed=101,
        x0=-1.0,
    )
    override = {
        "burn_in_rounds": 10,
        "batch_length": 5,
        "min_batches": 4,
        "max_batches": 4,
        "extension_batches": 1,
    }
    first_runs, first_batches = simulate_setting(
        [spec], configs["base"], {"experiment": "test"}, protocol_override=override
    )
    second_runs, second_batches = simulate_setting(
        [spec], configs["base"], {"experiment": "test"}, protocol_override=override
    )
    assert first_batches == second_batches
    for column in (
        "b_direct",
        "se_direct",
        "b_balance",
        "se_balance",
        "C_direct",
        "C_balance",
        "control_sum_max_abs",
    ):
        assert first_runs[0][column] == second_runs[0][column]


def test_formal_run_matrix_has_required_unique_168_chains() -> None:
    audit = matrix_audit(build_run_matrix())
    assert audit["coefficient_convergence"] == 80
    assert audit["client_count_scaling"] == 40
    assert audit["negative_controls"] == 48
    assert audit["controls"] == {
        "no_stochastic_noise": 16,
        "no_nonlinear_conversion": 16,
        "h1_boundary_sanity": 16,
    }
    assert audit["total"] == 168
    assert audit["unique_run_keys"] == 168
    assert audit["all_unique"] is True
