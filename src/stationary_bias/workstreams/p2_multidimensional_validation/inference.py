"""Vector stationary mean-balance estimator."""

from __future__ import annotations

import numpy as np


def vector_balance_round_value(
    qbar: np.ndarray, *, gamma: float, A: np.ndarray
) -> np.ndarray:
    """Map pre-update qbar values to the stationary server-mean estimate."""

    values = np.asarray(qbar, dtype=np.float64)
    matrix = np.asarray(A, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("A must be square")
    dimension = matrix.shape[0]
    if values.ndim < 2 or values.shape[-1] != dimension:
        raise ValueError("qbar must have shape [..., H, d]")
    H = values.shape[-2]
    if H < 1 or gamma <= 0.0:
        raise ValueError("H and gamma must be positive")

    identity = np.eye(dimension, dtype=np.float64)
    transition = identity - gamma * matrix
    weighted = np.zeros(values.shape[:-2] + (dimension,), dtype=np.float64)
    for h in range(H):
        power = np.linalg.matrix_power(transition, H - 1 - h)
        weighted += np.einsum("ij,...j->...i", power, values[..., h, :])
    stationary_operator = identity - np.linalg.matrix_power(transition, H)
    flat_rhs = (-gamma * weighted).reshape(-1, dimension)
    flat_result = np.linalg.solve(stationary_operator, flat_rhs.T).T
    return flat_result.reshape(weighted.shape)
