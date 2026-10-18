import numpy as np

from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
from stationary_bias.core.algorithms.scaffold import scaffold_round


def test_zero_sum_invariant_over_random_rounds() -> None:
    rng = np.random.default_rng(881)
    x = 0.7
    xi = np.zeros(17)
    maximum = 0.0
    for _ in range(2_000):
        result = scaffold_round(
            x,
            xi,
            gamma=1.0 / 32.0,
            H=4,
            objective=MAIN_OBJECTIVE,
            noise="rademacher",
            rng=rng,
        )
        x, xi = result.x_new, result.xi_new
        maximum = max(maximum, abs(float(np.sum(xi))))
    assert maximum <= 1.0e-10


def test_no_noise_zero_equilibrium_is_exact() -> None:
    rng = np.random.default_rng(91)
    x = 0.0
    xi = np.zeros(8)
    for _ in range(100):
        result = scaffold_round(
            x,
            xi,
            gamma=0.1,
            H=3,
            objective=MAIN_OBJECTIVE,
            noise="zero",
            rng=rng,
        )
        x, xi = result.x_new, result.xi_new
    assert x == 0.0
    np.testing.assert_array_equal(xi, np.zeros(8))
