import numpy as np

from stationary_bias.core.models.noise import sample_noise


def test_rademacher_values_and_fixed_seed_reproducibility() -> None:
    first = sample_noise("rademacher", np.random.default_rng(20260819), 100_000)
    second = sample_noise("rademacher", np.random.default_rng(20260819), 100_000)
    assert set(np.unique(first)) == {-1.0, 1.0}
    np.testing.assert_array_equal(first, second)


def test_zero_noise_is_deterministic() -> None:
    values = sample_noise("zero", np.random.default_rng(1), (10, 3))
    np.testing.assert_array_equal(values, np.zeros((10, 3)))
