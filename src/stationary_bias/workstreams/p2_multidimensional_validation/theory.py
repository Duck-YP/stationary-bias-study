"""Exact NumPy-only theory targets for the controlled objective."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .objective import RankOneVectorObjective


@dataclass(frozen=True)
class VectorTheoryTargets:
    S_C: np.ndarray
    B11_d: np.ndarray
    B20: np.ndarray
    B20_local: np.ndarray
    B20_ctrl: np.ndarray


def solve_symmetric_lyapunov(A: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Solve ``A S + S A = C`` using column-major vectorization."""

    matrix = np.asarray(A, dtype=np.float64)
    covariance = np.asarray(C, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("A must be square")
    if covariance.shape != matrix.shape:
        raise ValueError("C must have the same shape as A")
    identity = np.eye(matrix.shape[0], dtype=np.float64)
    operator = np.kron(identity, matrix) + np.kron(matrix.T, identity)
    vector = np.linalg.solve(operator, covariance.reshape(-1, order="F"))
    solution = vector.reshape(matrix.shape, order="F")
    return 0.5 * (solution + solution.T)


def vector_theory_targets(
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    H: int,
) -> VectorTheoryTargets:
    if H < 1:
        raise ValueError("H must be at least one")
    C = np.asarray(covariance, dtype=np.float64)
    S_C = solve_symmetric_lyapunov(objective.A, C)
    solve_T_S = np.linalg.solve(
        objective.A, objective.third_derivative_contraction(S_C)
    )
    solve_T_C = np.linalg.solve(
        objective.A, objective.third_derivative_contraction(C)
    )
    B11_d = -0.5 * solve_T_S
    B20_local = -((H - 1) / 4.0) * solve_T_C
    B20_ctrl = -((H - 1) * (2 * H - 1) / (12.0 * H)) * solve_T_C
    B20 = -((H - 1) * (5 * H - 1) / (12.0 * H)) * solve_T_C
    return VectorTheoryTargets(S_C, B11_d, B20, B20_local, B20_ctrl)


def normalize_vector_bias(
    bias: np.ndarray, *, gamma: float, N: int, B11_d: np.ndarray
) -> np.ndarray:
    values = np.asarray(bias, dtype=np.float64)
    leading = np.asarray(B11_d, dtype=np.float64)
    if values.shape[-1] != leading.size:
        raise ValueError("bias and B11_d dimensions differ")
    return (values - (gamma / N) * leading) / gamma**2
