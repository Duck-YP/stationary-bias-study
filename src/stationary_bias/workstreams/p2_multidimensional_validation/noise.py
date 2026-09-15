"""Bounded correlated vector noise for P2."""

from __future__ import annotations

from typing import Sequence

import numpy as np


CONTROLLED_COVARIANCE = np.array([[1.0, 0.3], [0.3, 0.7]], dtype=np.float64)


def covariance_cholesky(covariance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(covariance, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("covariance must be square")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1.0e-14):
        raise ValueError("covariance must be symmetric")
    return np.linalg.cholesky(matrix)


def generate_vector_noise_block(
    rngs: Sequence[np.random.Generator],
    covariance: np.ndarray,
    *,
    rounds: int,
    H: int,
    N: int,
) -> np.ndarray:
    """Draw independent Rademacher vectors, then apply the covariance factor."""

    factor = covariance_cholesky(covariance)
    dimension = factor.shape[0]
    if not rngs or rounds < 1 or H < 1 or N < 1:
        raise ValueError("rngs, rounds, H, and N must all be non-empty or positive")
    block = np.empty((len(rngs), rounds, H, N, dimension), dtype=np.float64)
    for chain_index, rng in enumerate(rngs):
        signs = 2 * rng.integers(
            0, 2, size=(rounds, H, N, dimension), dtype=np.int8
        ) - 1
        block[chain_index] = np.einsum(
            "ij,...j->...i", factor, signs.astype(np.float64)
        )
    return block

