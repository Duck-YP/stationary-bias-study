import numpy as np

from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.algorithm import (
    VectorFedAvgRoundResult,
    fedavg_round_many_vector,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_simulation import (
    _paired_rows,
    covariance_from_p3_config,
    load_matched_smoke_config,
    objective_from_p3_config,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.paired_algorithm import (
    indexed_noise_block,
    indexed_noise_vector,
    paired_round_many_vector,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.theory import (
    matched_vector_theory_targets,
)
from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import (
    scaffold_round_many_vector,
)


def _setting():
    config = load_matched_smoke_config()
    return objective_from_p3_config(config), covariance_from_p3_config(config)


def test_indexed_crn_is_exact_order_independent_and_seed_specific() -> None:
    _, covariance = _setting()
    first = indexed_noise_vector(2101, 7, 3, 1, covariance)
    _ = indexed_noise_vector(9999, 100, 0, 0, covariance)
    second = indexed_noise_vector(2101, 7, 3, 1, covariance)
    different = indexed_noise_vector(2102, 7, 3, 1, covariance)
    assert np.array_equal(first, second)
    assert not np.array_equal(first, different)
    block = indexed_noise_block(
        [2101], round_start=7, rounds=1, H=2, N=4, covariance=covariance
    )
    assert np.array_equal(block[0, 0, 1, 3], first)


def test_pair_uses_same_initial_state_shared_noise_and_separate_state() -> None:
    objective, covariance = _setting()
    initial = np.array([[0.2, -0.1]])
    x_scaffold = initial.copy()
    x_fedavg = initial.copy()
    xi = np.zeros((1, 4, 2))
    first_noise = indexed_noise_block(
        [2301], round_start=0, rounds=1, H=2, N=4, covariance=covariance
    )[:, 0]
    first = paired_round_many_vector(
        x_scaffold,
        xi,
        x_fedavg,
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=first_noise,
    )
    assert np.array_equal(x_scaffold, x_fedavg)
    assert isinstance(first.fedavg, VectorFedAvgRoundResult)
    assert not hasattr(first.fedavg, "xi_new")
    assert hasattr(first.scaffold, "xi_new")
    assert np.max(np.abs(np.sum(first.scaffold.xi_new, axis=1))) <= 1.0e-10
    assert first.crn_integrity.all()

    second_noise = indexed_noise_block(
        [2301], round_start=1, rounds=1, H=2, N=4, covariance=covariance
    )[:, 0]
    second = paired_round_many_vector(
        first.scaffold.x_new,
        first.scaffold.xi_new,
        first.fedavg.x_new,
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=second_noise,
    )
    assert not np.array_equal(second.scaffold.x_new, second.fedavg.x_new)


def test_explicit_fresh_noise_is_bitwise_unchanged_by_both_vector_kernels() -> None:
    objective, _ = _setting()
    fresh_noise = np.array(
        [
            [
                [[0.25, -0.5], [-0.75, 1.0]],
                [[-0.125, 0.375], [0.625, -0.875]],
            ]
        ],
        dtype=np.float64,
    )
    original = fresh_noise.copy()
    original_bytes = original.tobytes(order="C")
    x = np.array([[0.2, -0.1]])

    scaffold_round_many_vector(
        x,
        np.zeros((1, 2, 2)),
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=fresh_noise,
    )
    np.testing.assert_array_equal(fresh_noise, original)
    assert fresh_noise.tobytes(order="C") == original_bytes

    fedavg_round_many_vector(
        x,
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=fresh_noise,
    )
    np.testing.assert_array_equal(fresh_noise, original)
    assert fresh_noise.tobytes(order="C") == original_bytes

    paired = paired_round_many_vector(
        x,
        np.zeros((1, 2, 2)),
        x.copy(),
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=fresh_noise,
    )
    np.testing.assert_array_equal(fresh_noise, original)
    assert fresh_noise.tobytes(order="C") == original_bytes
    assert paired.crn_integrity.all()


def test_paired_primary_difference_and_cancellation_form_agree() -> None:
    objective, covariance = _setting()
    targets = matched_vector_theory_targets(objective, covariance, 2)
    fedavg_balance = np.array([[0.01, -0.02]])
    scaffold_balance = fedavg_balance + 0.05**2 * np.array([[-0.01, -0.02]])
    rows = _paired_rows(
        seeds=[2301],
        H=2,
        N=4,
        gamma=0.05,
        scaffold_balance=scaffold_balance,
        fedavg_balance=fedavg_balance,
        scaffold_direct=scaffold_balance,
        fedavg_direct=fedavg_balance,
        B11_d=targets.B11_d,
        B20_ctrl=targets.B20_ctrl,
    )
    assert len(rows) == 2
    assert all(
        np.isclose(
            row["paired_primary_difference"],
            row["paired_cancellation_difference"],
            rtol=5.0e-13,
            atol=5.0e-14,
        )
        for row in rows
    )


def test_theory_reproduces_all_matched_targets_and_difference_identity() -> None:
    objective, covariance = _setting()
    expected = {
        2: (
            [-0.032002677596805, -0.040003346996006],
            [-0.0480040163952075, -0.0600050204940090],
            [-0.0160013387984025, -0.0200016734980030],
        ),
        4: (
            [-0.096008032790415, -0.120010040988019],
            [-0.152012718584824, -0.190015898231030],
            [-0.0560046857944088, -0.0700058572430111],
        ),
    }
    for H, values in expected.items():
        targets = matched_vector_theory_targets(objective, covariance, H)
        assert np.allclose(targets.B20_FA, values[0], atol=1.0e-14, rtol=0.0)
        assert np.allclose(targets.B20_SCAF, values[1], atol=1.0e-14, rtol=0.0)
        assert np.allclose(targets.B20_ctrl, values[2], atol=1.0e-14, rtol=0.0)
        assert np.allclose(targets.B20_SCAF - targets.B20_FA, targets.B20_ctrl)
