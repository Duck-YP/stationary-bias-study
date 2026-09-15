import numpy as np

from stationary_bias.core.inference.statistics import balance_round_value
from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
from stationary_bias.workstreams.p2_multidimensional_validation.inference import (
    vector_balance_round_value,
)
from stationary_bias.workstreams.p2_multidimensional_validation.noise import (
    CONTROLLED_COVARIANCE,
)
from stationary_bias.workstreams.p2_multidimensional_validation.objective import (
    RankOneVectorObjective,
    controlled_objective,
)
from stationary_bias.workstreams.p2_multidimensional_validation.theory import (
    vector_theory_targets,
)


def test_controlled_objective_origin_hessian_and_batched_shapes() -> None:
    objective = controlled_objective()
    zeros = np.zeros((3, 4, 2))
    np.testing.assert_array_equal(objective.grad(zeros), zeros)
    np.testing.assert_array_equal(objective.hessian_at_minimum, objective.A)
    assert objective.dimension == 2
    assert objective.grad(zeros).shape == zeros.shape
    assert objective.q(zeros).shape == zeros.shape


def test_third_derivative_contraction_matches_generic_tensor() -> None:
    objective = controlled_objective()
    matrix = np.array([[0.8, -0.2], [-0.2, 1.1]])
    tensor = objective.alpha * np.einsum(
        "i,j,k->ijk", objective.u, objective.u, objective.u
    )
    generic = np.einsum("ijk,jk->i", tensor, matrix)
    np.testing.assert_allclose(
        objective.third_derivative_contraction(matrix),
        generic,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_theory_lyapunov_residual_and_source_decomposition() -> None:
    objective = controlled_objective()
    targets = vector_theory_targets(objective, CONTROLLED_COVARIANCE, H=2)
    residual = objective.A @ targets.S_C + targets.S_C @ objective.A
    np.testing.assert_allclose(residual, CONTROLLED_COVARIANCE, rtol=0.0, atol=1.0e-14)
    np.testing.assert_allclose(
        targets.B20_local + targets.B20_ctrl,
        targets.B20,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_vector_balance_uses_preupdate_qbars() -> None:
    objective = controlled_objective()
    x = np.array([[0.4, -0.1]])
    theta = np.repeat(x[:, None, :], 2, axis=1)
    controls = np.array([[[0.2, -0.1], [-0.2, 0.1]]])
    noise = np.array(
        [[[[0.3, -0.2], [-0.3, 0.2]], [[-0.1, 0.4], [0.1, -0.4]]]]
    )
    gamma = 0.07
    pre = []
    post = []
    for h in range(2):
        pre.append(np.mean(objective.q(theta), axis=1))
        theta = theta - gamma * (
            objective.grad(theta) + controls + noise[:, h]
        )
        post.append(np.mean(objective.q(theta), axis=1))
    pre_values = np.stack(pre, axis=1)
    post_values = np.stack(post, axis=1)
    observed = vector_balance_round_value(pre_values, gamma=gamma, A=objective.A)
    incorrect = vector_balance_round_value(post_values, gamma=gamma, A=objective.A)
    assert not np.allclose(observed, incorrect, rtol=0.0, atol=1.0e-12)


def test_d1_vector_balance_reduces_to_scalar_balance() -> None:
    objective = RankOneVectorObjective(np.array([[1.0]]), np.array([1.0]), 0.5)
    theta = np.array([[0.2, -0.1], [-0.4, 0.3]])
    qbars = np.empty((2, 3))
    for h in range(3):
        qbars[:, h] = np.mean(MAIN_OBJECTIVE.q(theta), axis=1)
        theta = theta - 0.05 * MAIN_OBJECTIVE.grad(theta)
    scalar = balance_round_value(qbars, gamma=0.05, a=1.0)
    vector = vector_balance_round_value(
        qbars[:, :, None], gamma=0.05, A=objective.A
    )
    np.testing.assert_allclose(vector[:, 0], scalar, rtol=0.0, atol=1.0e-15)

