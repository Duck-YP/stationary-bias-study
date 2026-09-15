"""Externally specified theory targets for the isolated P1 comparison."""

from __future__ import annotations


def b20_fedavg(
    H: int,
    *,
    a: float = 1.0,
    tau: float = 0.5,
    sigma2: float = 1.0,
) -> float:
    """FedAvg client-independent coefficient specified for P1."""

    if H < 1:
        raise ValueError("H must be at least one")
    return -(tau * sigma2 * (H - 1)) / (4.0 * a)


def delta_b20_scaffold_minus_fedavg(
    H: int,
    *,
    a: float = 1.0,
    tau: float = 0.5,
    sigma2: float = 1.0,
) -> float:
    """Specified SCAFFOLD-minus-FedAvg second-order coefficient."""

    if H < 1:
        raise ValueError("H must be at least one")
    return -(tau * sigma2 * (H - 1) * (2 * H - 1)) / (12.0 * a * H)
