from dataclasses import fields

import numpy as np

from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.algorithm import (
    VectorFedAvgRoundResult,
    fedavg_round_many_vector,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.simulation import (
    FROZEN_B11_D,
    FROZEN_B20_FA,
    FROZEN_C,
    load_smoke_config,
    objective_from_config,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.theory import (
    fedavg_vector_theory_targets,
    normalize_fedavg_bias,
)
from stationary_bias.workstreams.p2_multidimensional_validation.noise import (
    covariance_cholesky,
    generate_vector_noise_block,
)


def test_vector_fedavg_one_step_recurrence_and_server_average() -> None:
    objective = objective_from_config(load_smoke_config())
    x = np.array([[0.2, -0.1], [-0.4, 0.3]])
    noise = np.array(
        [
            [[[[0.3, -0.2], [-0.1, 0.4]]]],
            [[[[0.2, 0.1], [-0.4, -0.3]]]],
        ]
    ).reshape(2, 1, 2, 2)
    gamma = 0.05
    theta0 = np.repeat(x[:, None, :], 2, axis=1)
    expected = theta0 - gamma * (objective.grad(theta0) + noise[:, 0])
    result = fedavg_round_many_vector(
        x, gamma=gamma, H=1, objective=objective, epsilon_steps=noise
    )
    np.testing.assert_allclose(result.theta_final, expected, rtol=0.0, atol=1e-15)
    np.testing.assert_allclose(result.x_new, np.mean(expected, axis=1), rtol=0.0, atol=1e-15)
    assert result.qbar.shape == (2, 1, 2)


def test_vector_fedavg_multistep_recurrence_is_exact() -> None:
    objective = objective_from_config(load_smoke_config())
    x = np.array([[0.25, -0.15]])
    noise = np.array(
        [[[[0.2, -0.1], [-0.3, 0.4]], [[-0.1, 0.3], [0.4, -0.2]], [[0.0, 0.2], [-0.2, 0.0]]]]
    )
    theta = np.repeat(x[:, None, :], 2, axis=1)
    expected_qbar = []
    for h in range(3):
        expected_qbar.append(np.mean(objective.q(theta), axis=1))
        theta = theta - 0.04 * (objective.grad(theta) + noise[:, h])
    result = fedavg_round_many_vector(
        x, gamma=0.04, H=3, objective=objective, epsilon_steps=noise
    )
    np.testing.assert_allclose(result.theta_final, theta, rtol=0.0, atol=1e-15)
    np.testing.assert_allclose(result.qbar, np.stack(expected_qbar, axis=1), rtol=0.0, atol=1e-15)
    np.testing.assert_allclose(result.x_new, np.mean(theta, axis=1), rtol=0.0, atol=1e-15)


def test_fedavg_result_has_no_control_state() -> None:
    names = {item.name for item in fields(VectorFedAvgRoundResult)}
    assert names == {"x_new", "qbar", "theta_final"}
    assert not any("control" in name or "xi" in name for name in names)


def test_explicit_noise_and_seeded_noise_are_reproducible() -> None:
    objective = objective_from_config(load_smoke_config())
    rngs1 = [np.random.default_rng(77), np.random.default_rng(88)]
    rngs2 = [np.random.default_rng(77), np.random.default_rng(88)]
    noise1 = generate_vector_noise_block(rngs1, FROZEN_C, rounds=2, H=2, N=3)
    noise2 = generate_vector_noise_block(rngs2, FROZEN_C, rounds=2, H=2, N=3)
    np.testing.assert_array_equal(noise1, noise2)
    x = np.zeros((2, 2))
    first = fedavg_round_many_vector(
        x, gamma=0.05, H=2, objective=objective, epsilon_steps=noise1[:, 0]
    )
    second = fedavg_round_many_vector(
        x, gamma=0.05, H=2, objective=objective, epsilon_steps=noise2[:, 0]
    )
    np.testing.assert_array_equal(first.x_new, second.x_new)
    np.testing.assert_array_equal(first.qbar, second.qbar)


def test_cholesky_rademacher_covariance_matches_frozen_C_exactly() -> None:
    signs = np.array([[-1.0, -1.0], [-1.0, 1.0], [1.0, -1.0], [1.0, 1.0]])
    samples = signs @ covariance_cholesky(FROZEN_C).T
    observed = samples.T @ samples / len(samples)
    np.testing.assert_allclose(observed, FROZEN_C, rtol=0.0, atol=1e-15)


def test_theory_is_calculated_and_matches_frozen_regressions() -> None:
    objective = objective_from_config(load_smoke_config())
    expected_S = np.array(
        [[0.413009404388715, 0.021943573667712], [0.021943573667712, 0.345611285266458]]
    )
    for H in (2, 4):
        targets = fedavg_vector_theory_targets(objective, FROZEN_C, H)
        np.testing.assert_allclose(
            objective.A @ targets.S_C + targets.S_C @ objective.A,
            FROZEN_C,
            rtol=0.0,
            atol=1e-14,
        )
        np.testing.assert_allclose(targets.S_C, expected_S, rtol=0.0, atol=1e-14)
        np.testing.assert_allclose(targets.B11_d, FROZEN_B11_D, rtol=0.0, atol=1e-14)
        np.testing.assert_allclose(targets.B20_FA, FROZEN_B20_FA[H], rtol=0.0, atol=1e-14)


def test_normalization_uses_intrinsic_B11_sign_and_preserves_coordinates() -> None:
    gamma = 0.1
    N = 5
    coefficient = np.array([-0.03, 0.07])
    bias = (gamma / N) * FROZEN_B11_D + gamma**2 * coefficient
    observed = normalize_fedavg_bias(
        bias, gamma=gamma, N=N, B11_d=FROZEN_B11_D
    )
    np.testing.assert_allclose(observed, coefficient, rtol=0.0, atol=2e-16)
    flipped = (bias + (gamma / N) * FROZEN_B11_D) / gamma**2
    assert not np.allclose(observed, flipped)
