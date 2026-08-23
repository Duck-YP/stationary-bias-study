import pytest

from stationary_bias.theoretical_bias import b20_control, b20_local, b20_total


def test_required_exact_theory_coefficients() -> None:
    assert b20_total(2) == -0.1875
    assert b20_total(4) == -0.59375


@pytest.mark.parametrize("H", [1, 2, 3, 4, 10])
def test_source_decomposition_sums_to_total(H: int) -> None:
    assert b20_local(H) + b20_control(H) == pytest.approx(b20_total(H), abs=1.0e-15)
