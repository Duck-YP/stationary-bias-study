import numpy as np

from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
from stationary_bias.core.algorithms.scaffold import scaffold_round


def test_one_round_matches_hand_formula() -> None:
    x = 0.2
    xi = np.array([0.1, -0.1])
    gamma = 0.05
    H = 2
    epsilon = np.array([[1.0, -1.0], [-1.0, 1.0]])

    theta = np.array([x, x], dtype=np.float64)
    expected_qbar = []
    for h in range(H):
        expected_qbar.append(float(np.mean(MAIN_OBJECTIVE.grad(theta) - theta)))
        theta = theta - gamma * (MAIN_OBJECTIVE.grad(theta) + xi + epsilon[h])
    expected_x = float(np.mean(theta))
    expected_xi = xi + (theta - expected_x) / (gamma * H)

    result = scaffold_round(
        x,
        xi,
        gamma=gamma,
        H=H,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    np.testing.assert_allclose(result.theta_final, theta, rtol=0.0, atol=1.0e-15)
    assert result.x_new == expected_x
    np.testing.assert_allclose(result.xi_new, expected_xi, rtol=0.0, atol=1.0e-15)
    np.testing.assert_allclose(result.qbar, expected_qbar, rtol=0.0, atol=1.0e-15)
