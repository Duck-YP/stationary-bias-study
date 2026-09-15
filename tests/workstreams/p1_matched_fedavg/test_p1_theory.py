import pytest

from stationary_bias.workstreams.p1_matched_fedavg.theory import (
    b20_fedavg,
    delta_b20_scaffold_minus_fedavg,
)
from stationary_bias.core.theory.one_dimensional import b20_total


@pytest.mark.parametrize(
    ("H", "fedavg", "delta"),
    [
        (1, 0.0, 0.0),
        (2, -0.125, -0.0625),
        (4, -0.375, -0.21875),
    ],
)
def test_p1_theory_targets(H: int, fedavg: float, delta: float) -> None:
    assert b20_fedavg(H) == fedavg
    assert delta_b20_scaffold_minus_fedavg(H) == delta
    assert b20_fedavg(H) + delta_b20_scaffold_minus_fedavg(H) == pytest.approx(
        b20_total(H), abs=1.0e-15
    )
