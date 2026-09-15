import numpy as np

from stationary_bias.core.models.objectives import MAIN_OBJECTIVE, log_cosh, nonlinear_grad


def test_objective_origin() -> None:
    assert nonlinear_grad(0.0) == 0.0


def test_objective_constants_and_curvature_grid() -> None:
    assert MAIN_OBJECTIVE.a == 1.0
    assert MAIN_OBJECTIVE.tau == 0.5
    assert MAIN_OBJECTIVE.mu == 0.5
    assert MAIN_OBJECTIVE.L == 1.5
    grid = np.linspace(-100.0, 100.0, 100_001)
    curvature = MAIN_OBJECTIVE.second(grid)
    assert np.all(curvature >= 0.5)
    assert np.all(curvature <= 1.5)


def test_log_cosh_is_stable_at_large_magnitude() -> None:
    values = np.asarray(log_cosh(np.array([-10_000.0, 10_000.0])))
    assert np.all(np.isfinite(values))
    np.testing.assert_allclose(values, 10_000.0 - np.log(2.0), rtol=0.0, atol=1.0e-12)
