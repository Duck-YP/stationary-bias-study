"""Controlled rank-one nonlinear objective used by the smoke test."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


CONTROLLED_A = np.array([[1.2, 0.2], [0.2, 1.0]], dtype=np.float64)
CONTROLLED_U = np.array([1.0, 1.0], dtype=np.float64) / np.sqrt(2.0)
CONTROLLED_ALPHA = 0.25


def _log_cosh(values: np.ndarray) -> np.ndarray:
    return np.logaddexp(values, -values) - np.log(2.0)


@dataclass(frozen=True)
class RankOneVectorObjective:
    """Objective with gradient ``A x + alpha u log(cosh(u^T x))``."""

    A: np.ndarray
    u: np.ndarray
    alpha: float

    def __post_init__(self) -> None:
        matrix = np.asarray(self.A, dtype=np.float64)
        direction = np.asarray(self.u, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("A must be a square matrix")
        if direction.shape != (matrix.shape[0],):
            raise ValueError("u must have one entry per objective coordinate")
        if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1.0e-14):
            raise ValueError("A must be symmetric")
        if np.min(np.linalg.eigvalsh(matrix)) <= 0.0:
            raise ValueError("A must be positive definite")
        if not np.isclose(np.linalg.norm(direction), 1.0):
            raise ValueError("u must be a unit vector")
        object.__setattr__(self, "A", matrix.copy())
        object.__setattr__(self, "u", direction.copy())
        object.__setattr__(self, "alpha", float(self.alpha))

    @property
    def dimension(self) -> int:
        return int(self.A.shape[0])

    @property
    def hessian_at_minimum(self) -> np.ndarray:
        return self.A.copy()

    def _values(self, x: np.ndarray) -> np.ndarray:
        values = np.asarray(x, dtype=np.float64)
        if values.ndim == 0 or values.shape[-1] != self.dimension:
            raise ValueError(
                f"x must have a final coordinate axis of length {self.dimension}"
            )
        return values

    def q(self, x: np.ndarray) -> np.ndarray:
        values = self._values(x)
        projection = np.einsum("...i,i->...", values, self.u)
        return self.alpha * _log_cosh(projection)[..., None] * self.u

    def grad(self, x: np.ndarray) -> np.ndarray:
        values = self._values(x)
        linear = np.einsum("ij,...j->...i", self.A, values)
        return linear + self.q(values)

    def third_derivative_contraction(self, matrix: np.ndarray) -> np.ndarray:
        values = np.asarray(matrix, dtype=np.float64)
        if values.shape != (self.dimension, self.dimension):
            raise ValueError(
                f"matrix must have shape {(self.dimension, self.dimension)}"
            )
        scalar = float(self.u @ values @ self.u)
        return self.alpha * self.u * scalar


def controlled_objective() -> RankOneVectorObjective:
    return RankOneVectorObjective(CONTROLLED_A, CONTROLLED_U, CONTROLLED_ALPHA)
