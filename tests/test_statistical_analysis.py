import numpy as np

from stationary_bias.statistical_analysis import balance_round_value
from stationary_bias.objectives import MAIN_OBJECTIVE
from stationary_bias.scaffold_algorithm import scaffold_round
from stationary_bias.theoretical_bias import geometric_sum


def test_mean_balance_uses_pre_update_local_states() -> None:
    x = 0.4
    xi = np.array([0.2, -0.2])
    gamma = 0.07
    H = 3
    epsilon = np.array([[1.0, -1.0], [-1.0, -1.0], [1.0, 1.0]])
    theta = np.full(2, x)
    pre_qbars = []
    post_qbars = []
    for h in range(H):
        pre_qbars.append(float(np.mean(MAIN_OBJECTIVE.q(theta))))
        theta = theta - gamma * (MAIN_OBJECTIVE.grad(theta) + xi + epsilon[h])
        post_qbars.append(float(np.mean(MAIN_OBJECTIVE.q(theta))))

    result = scaffold_round(
        x,
        xi,
        gamma=gamma,
        H=H,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    lam = 1.0 - gamma
    weights = lam ** np.arange(H - 1, -1, -1)
    expected = -(np.asarray(pre_qbars) @ weights) / geometric_sum(H, lam)
    incorrectly_post_update = -(np.asarray(post_qbars) @ weights) / geometric_sum(H, lam)
    observed = balance_round_value(result.qbar, gamma=gamma, a=1.0)
    assert observed == expected
    assert not np.isclose(observed, incorrectly_post_update, rtol=0.0, atol=1.0e-12)


def test_balance_value_accepts_chain_axis() -> None:
    qbars = np.array([[1.0, 2.0], [3.0, 4.0]])
    values = balance_round_value(qbars, gamma=0.1, a=1.0)
    assert values.shape == (2,)
