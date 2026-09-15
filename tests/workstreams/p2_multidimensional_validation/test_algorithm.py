import numpy as np

from stationary_bias.core.algorithms.scaffold import scaffold_round_many
from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import (
    scaffold_round_many_vector,
)
from stationary_bias.workstreams.p2_multidimensional_validation.noise import (
    CONTROLLED_COVARIANCE,
    generate_vector_noise_block,
)
from stationary_bias.workstreams.p2_multidimensional_validation.objective import (
    RankOneVectorObjective,
    controlled_objective,
)


def test_d2_one_round_matches_hand_recursion() -> None:
    objective = controlled_objective()
    x = np.array([[0.2, -0.1], [-0.3, 0.4]])
    xi = np.array(
        [
            [[0.1, -0.2], [-0.1, 0.2]],
            [[0.05, 0.1], [-0.05, -0.1]],
        ]
    )
    noise = np.array(
        [
            [[[0.4, -0.3], [-0.2, 0.1]], [[-0.1, 0.2], [0.3, -0.4]]],
            [[[-0.2, 0.4], [0.1, -0.3]], [[0.3, 0.2], [-0.4, -0.1]]],
        ]
    )
    gamma = 0.05
    H = 2
    theta = np.repeat(x[:, None, :], 2, axis=1)
    expected_qbar = np.empty((2, H, 2))
    for h in range(H):
        expected_qbar[:, h, :] = np.mean(objective.q(theta), axis=1)
        theta = theta - gamma * (objective.grad(theta) + xi + noise[:, h])
    expected_x = np.mean(theta, axis=1)
    expected_xi = xi + (theta - expected_x[:, None, :]) / (gamma * H)

    result = scaffold_round_many_vector(
        x,
        xi,
        gamma=gamma,
        H=H,
        objective=objective,
        epsilon_steps=noise,
    )
    np.testing.assert_allclose(result.theta_final, theta, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(result.x_new, expected_x, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(result.xi_new, expected_xi, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(result.qbar, expected_qbar, rtol=0.0, atol=1.0e-15)
    assert result.x_new.shape == (2, 2)
    assert result.xi_new.shape == (2, 2, 2)


def test_vector_zero_sum_control_invariant_over_random_rounds() -> None:
    objective = controlled_objective()
    x = np.array([[0.4, -0.2], [-0.1, 0.3]])
    xi = np.zeros((2, 7, 2))
    rngs = [np.random.default_rng(811), np.random.default_rng(812)]
    maximum = 0.0
    for _ in range(200):
        noise = generate_vector_noise_block(
            rngs, CONTROLLED_COVARIANCE, rounds=1, H=3, N=7
        )[:, 0]
        result = scaffold_round_many_vector(
            x,
            xi,
            gamma=0.04,
            H=3,
            objective=objective,
            epsilon_steps=noise,
        )
        x, xi = result.x_new, result.xi_new
        maximum = max(maximum, float(np.max(np.abs(np.sum(xi, axis=1)))))
    assert maximum <= 1.0e-10


def test_vector_zero_noise_equilibrium_is_exact() -> None:
    objective = controlled_objective()
    x = np.zeros((2, 2))
    xi = np.zeros((2, 4, 2))
    noise = np.zeros((2, 3, 4, 2))
    for _ in range(20):
        result = scaffold_round_many_vector(
            x,
            xi,
            gamma=0.05,
            H=3,
            objective=objective,
            epsilon_steps=noise,
        )
        x, xi = result.x_new, result.xi_new
    np.testing.assert_array_equal(x, np.zeros((2, 2)))
    np.testing.assert_array_equal(xi, np.zeros((2, 4, 2)))


def test_d1_vector_kernel_matches_frozen_scalar_kernel() -> None:
    objective = RankOneVectorObjective(np.array([[1.0]]), np.array([1.0]), 0.5)
    x = np.array([0.2, -0.4])
    xi = np.array([[0.1, -0.1], [-0.2, 0.2]])
    noise = np.array(
        [[[1.0, -1.0], [-1.0, 1.0]], [[-1.0, -1.0], [1.0, 1.0]]]
    )
    scalar = scaffold_round_many(
        x,
        xi,
        gamma=0.05,
        H=2,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=noise,
    )
    vector = scaffold_round_many_vector(
        x[:, None],
        xi[:, :, None],
        gamma=0.05,
        H=2,
        objective=objective,
        epsilon_steps=noise[:, :, :, None],
    )
    np.testing.assert_allclose(vector.x_new[:, 0], scalar.x_new, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(vector.xi_new[:, :, 0], scalar.xi_new, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(vector.qbar[:, :, 0], scalar.qbar, rtol=0.0, atol=1.0e-15)


def test_vector_noise_factor_reproducibility_and_covariance() -> None:
    first = generate_vector_noise_block(
        [np.random.default_rng(813)],
        CONTROLLED_COVARIANCE,
        rounds=1,
        H=1,
        N=20_000,
    )
    second = generate_vector_noise_block(
        [np.random.default_rng(813)],
        CONTROLLED_COVARIANCE,
        rounds=1,
        H=1,
        N=20_000,
    )
    np.testing.assert_array_equal(first, second)
    factor = np.linalg.cholesky(CONTROLLED_COVARIANCE)
    np.testing.assert_allclose(
        factor @ factor.T, CONTROLLED_COVARIANCE, rtol=0.0, atol=1.0e-15
    )
    empirical = np.cov(first.reshape(-1, 2), rowvar=False, bias=True)
    np.testing.assert_allclose(empirical, CONTROLLED_COVARIANCE, rtol=0.0, atol=0.025)
