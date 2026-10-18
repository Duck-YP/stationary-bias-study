"""Shared validity and stationarity gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .statistics import standard_error


@dataclass(frozen=True)
class StationarityCheck:
    first_half_mean: float
    second_half_mean: float
    first_half_se: float
    second_half_se: float
    passed: bool


def all_finite(*values: object) -> bool:
    return all(np.all(np.isfinite(np.asarray(value))) for value in values)


def control_invariant_pass(max_abs_control_sum: float, threshold: float = 1.0e-10) -> bool:
    return bool(np.isfinite(max_abs_control_sum) and max_abs_control_sum <= threshold)


def estimator_agreement(
    direct: float,
    balance: float,
    se_direct: float,
    se_balance: float,
    *,
    z: float = 3.0,
) -> bool:
    scale = z * np.sqrt(se_direct * se_direct + se_balance * se_balance)
    return bool(np.isfinite(scale) and abs(direct - balance) <= scale)


def stationarity_check(batch_balance_means: Sequence[float], *, z: float = 3.0) -> StationarityCheck:
    values = np.asarray(batch_balance_means, dtype=np.float64)
    split = values.size // 2
    if split < 2:
        return StationarityCheck(*(float("nan"),) * 4, passed=False)
    first = values[:split]
    second = values[split:]
    mean_first = float(np.mean(first))
    mean_second = float(np.mean(second))
    se_first = standard_error(first)
    se_second = standard_error(second)
    passed = abs(mean_first - mean_second) <= z * np.sqrt(se_first**2 + se_second**2)
    return StationarityCheck(mean_first, mean_second, se_first, se_second, bool(passed))


def precision_threshold(B_theory: float, *, absolute: float = 0.02, relative: float = 0.10) -> float:
    return max(absolute, relative * abs(B_theory))
