from dataclasses import fields

import numpy as np

from stationary_bias.workstreams.p1_matched_fedavg.fedavg import (
    BatchedFedAvgRoundResult,
    FedAvgRoundResult,
    fedavg_round,
    fedavg_round_many,
)
from stationary_bias.core.models.objectives import MAIN_OBJECTIVE


def test_fedavg_one_round_matches_hand_formula() -> None:
    x = 0.2
    gamma = 0.05
    H = 2
    epsilon = np.array([[1.0, -1.0], [-1.0, 1.0]])
    theta = np.full(2, x, dtype=np.float64)
    expected_qbar = []
    for h in range(H):
        expected_qbar.append(float(np.mean(MAIN_OBJECTIVE.q(theta))))
        theta = theta - gamma * (MAIN_OBJECTIVE.grad(theta) + epsilon[h])

    result = fedavg_round(
        x,
        gamma=gamma,
        H=H,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    assert result.x_new == float(np.mean(theta))
    np.testing.assert_allclose(result.theta_final, theta, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(result.qbar, expected_qbar, rtol=0.0, atol=1.0e-15)


def test_fedavg_h1_exact_update() -> None:
    x = -0.3
    gamma = 0.07
    epsilon = np.array([[1.0, -1.0, 1.0]])
    result = fedavg_round(
        x,
        gamma=gamma,
        H=1,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    expected_theta = x - gamma * (MAIN_OBJECTIVE.grad(x) + epsilon[0])
    np.testing.assert_allclose(result.theta_final, expected_theta, rtol=0.0, atol=1.0e-15)
    assert result.x_new == float(np.mean(expected_theta))


def test_fedavg_zero_noise_equilibrium_is_exact() -> None:
    x = 0.0
    epsilon = np.zeros((4, 8))
    for _ in range(100):
        result = fedavg_round(
            x,
            gamma=0.1,
            H=4,
            objective=MAIN_OBJECTIVE,
            epsilon_steps=epsilon,
        )
        x = result.x_new
    assert x == 0.0
    np.testing.assert_array_equal(result.theta_final, np.zeros(8))


def test_fedavg_same_explicit_noise_is_deterministic() -> None:
    epsilon = np.array(
        [[[1.0, -1.0], [-1.0, 1.0]], [[-1.0, -1.0], [1.0, 1.0]]]
    )
    kwargs = {
        "gamma": 0.05,
        "H": 2,
        "objective": MAIN_OBJECTIVE,
        "epsilon_steps": epsilon,
    }
    first = fedavg_round_many(np.array([0.2, -0.4]), **kwargs)
    second = fedavg_round_many(np.array([0.2, -0.4]), **kwargs)
    np.testing.assert_array_equal(first.x_new, second.x_new)
    np.testing.assert_array_equal(first.qbar, second.qbar)
    np.testing.assert_array_equal(first.theta_final, second.theta_final)


def test_fedavg_result_state_has_no_control_or_xi() -> None:
    scalar_fields = {item.name for item in fields(FedAvgRoundResult)}
    batched_fields = {item.name for item in fields(BatchedFedAvgRoundResult)}
    for names in (scalar_fields, batched_fields):
        assert "xi" not in names
        assert "xi_new" not in names
        assert not any("control" in name for name in names)


def test_fedavg_vectorized_and_scalar_rounds_agree() -> None:
    x = np.array([0.2, -0.4])
    epsilon = np.array(
        [[[1.0, -1.0], [-1.0, 1.0]], [[-1.0, -1.0], [1.0, 1.0]]]
    )
    batched = fedavg_round_many(
        x,
        gamma=0.05,
        H=2,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    scalar = [
        fedavg_round(
            float(x[index]),
            gamma=0.05,
            H=2,
            objective=MAIN_OBJECTIVE,
            epsilon_steps=epsilon[index],
        )
        for index in range(x.size)
    ]
    np.testing.assert_allclose(
        batched.x_new, [item.x_new for item in scalar], rtol=0.0, atol=1.0e-15
    )
    np.testing.assert_allclose(
        batched.qbar, [item.qbar for item in scalar], rtol=0.0, atol=1.0e-15
    )
    np.testing.assert_allclose(
        batched.theta_final,
        [item.theta_final for item in scalar],
        rtol=0.0,
        atol=1.0e-15,
    )
