"""Calculated theory targets for multidimensional matched attribution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..p2_multidimensional_validation.objective import RankOneVectorObjective
from ..p2_multidimensional_validation.theory import (
    solve_symmetric_lyapunov,
    vector_theory_targets,
)


@dataclass(frozen=True)
class FedAvgVectorTheoryTargets:
    S_C: np.ndarray
    B11_d: np.ndarray
    B20_FA: np.ndarray


@dataclass(frozen=True)
class MatchedVectorTheoryTargets:
    """Calculated matched FedAvg/SCAFFOLD attribution targets."""

    S_C: np.ndarray
    B11_d: np.ndarray
    B20_FA: np.ndarray
    B20_SCAF: np.ndarray
    B20_ctrl: np.ndarray


def fedavg_vector_theory_targets(
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    H: int,
) -> FedAvgVectorTheoryTargets:
    """Calculate ``S_C``, ``B11_d``, and the FedAvg local coefficient."""

    if H < 1:
        raise ValueError("H must be at least one")
    C = np.asarray(covariance, dtype=np.float64)
    if C.shape != objective.A.shape:
        raise ValueError("covariance and objective dimensions differ")
    S_C = solve_symmetric_lyapunov(objective.A, C)
    B11_d = -0.5 * np.linalg.solve(
        objective.A, objective.third_derivative_contraction(S_C)
    )
    B20_FA = -((H - 1) / 4.0) * np.linalg.solve(
        objective.A, objective.third_derivative_contraction(C)
    )
    return FedAvgVectorTheoryTargets(S_C=S_C, B11_d=B11_d, B20_FA=B20_FA)


def normalize_fedavg_bias(
    bias: np.ndarray, *, gamma: float, N: int, B11_d: np.ndarray
) -> np.ndarray:
    """Apply the frozen intrinsic-sign normalization coordinatewise."""

    values = np.asarray(bias, dtype=np.float64)
    leading = np.asarray(B11_d, dtype=np.float64)
    if gamma <= 0.0 or N < 1 or values.shape[-1] != leading.size:
        raise ValueError("bias, gamma, N, and B11_d dimensions must be valid")
    return (values - (gamma / N) * leading) / gamma**2


def matched_vector_theory_targets(
    objective: RankOneVectorObjective,
    covariance: np.ndarray,
    H: int,
) -> MatchedVectorTheoryTargets:
    """Calculate both algorithms and their audited control contribution."""

    fedavg = fedavg_vector_theory_targets(objective, covariance, H)
    scaffold = vector_theory_targets(objective, covariance, H)
    control = scaffold.B20 - fedavg.B20_FA
    if not np.allclose(control, scaffold.B20_ctrl, rtol=1.0e-13, atol=1.0e-15):
        raise RuntimeError("SCAFFOLD - FedAvg theory does not equal B20_ctrl")
    if not np.allclose(fedavg.B20_FA, scaffold.B20_local, rtol=1.0e-13, atol=1.0e-15):
        raise RuntimeError("FedAvg theory does not equal the existing SCAFFOLD local coefficient")
    return MatchedVectorTheoryTargets(
        S_C=fedavg.S_C,
        B11_d=fedavg.B11_d,
        B20_FA=fedavg.B20_FA,
        B20_SCAF=scaffold.B20,
        B20_ctrl=control,
    )
