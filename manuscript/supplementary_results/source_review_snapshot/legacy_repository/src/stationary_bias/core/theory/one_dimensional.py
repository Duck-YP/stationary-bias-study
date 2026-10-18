"""Candidate-theorem coefficients and normalization helpers."""

from __future__ import annotations

import numpy as np


def leading_bias_coefficient(a: float, tau: float, sigma2: float) -> float:
    """Coefficient multiplying gamma/N in the candidate expansion."""

    return -(tau * sigma2) / (4.0 * a * a)


def b20_local(H: int, *, a: float = 1.0, tau: float = 0.5, sigma2: float = 1.0) -> float:
    if H < 1:
        raise ValueError("H must be at least one")
    return -(tau * sigma2 / (4.0 * a)) * (H - 1)


def b20_control(H: int, *, a: float = 1.0, tau: float = 0.5, sigma2: float = 1.0) -> float:
    if H < 1:
        raise ValueError("H must be at least one")
    return -(tau * sigma2 / (12.0 * a)) * ((H - 1) * (2 * H - 1) / H)


def b20_total(H: int, *, a: float = 1.0, tau: float = 0.5, sigma2: float = 1.0) -> float:
    if H < 1:
        raise ValueError("H must be at least one")
    return -(tau * sigma2 / (12.0 * a)) * ((H - 1) * (5 * H - 1) / H)


def lambda_gamma(gamma: float, a: float) -> float:
    return 1.0 - a * gamma


def geometric_sum(H: int, lam: float) -> float:
    if H < 1:
        raise ValueError("H must be at least one")
    return float(np.sum(np.power(lam, np.arange(H, dtype=np.float64))))


def normalize_bias(
    b: float | np.ndarray,
    *,
    gamma: float,
    N: int,
    a: float,
    tau: float,
    sigma2: float,
) -> float | np.ndarray:
    leading = leading_bias_coefficient(a, tau, sigma2)
    return (np.asarray(b) - leading * gamma / N) / (gamma * gamma)

