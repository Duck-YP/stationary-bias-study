"""Stationary-mean estimators and chain-level inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from ..theory.one_dimensional import geometric_sum, lambda_gamma


# Two-sided 95% Student-t quantiles. Formal studies use df=7; the table
# keeps the helper useful for small diagnostic subsets without adding SciPy.
_T_975 = {
    1: 12.7062047364,
    2: 4.30265272975,
    3: 3.18244630528,
    4: 2.7764451052,
    5: 2.57058183564,
    6: 2.44691184879,
    7: 2.36462425159,
    8: 2.3060041352,
    9: 2.26215716285,
    10: 2.22813885196,
    11: 2.20098516008,
    12: 2.17881282966,
    13: 2.16036865646,
    14: 2.14478668792,
    15: 2.13144954556,
    16: 2.11990529922,
    17: 2.10981557783,
    18: 2.10092204024,
    19: 2.09302405441,
    20: 2.08596344727,
    21: 2.07961384473,
    22: 2.0738730679,
    23: 2.06865761042,
    24: 2.06389856163,
    25: 2.05953855275,
    26: 2.05552943864,
    27: 2.05183051648,
    28: 2.0484071418,
    29: 2.04522964213,
    30: 2.0422724563,
}


@dataclass(frozen=True)
class Summary:
    mean: float
    std: float
    se: float
    ci_low: float
    ci_high: float


def balance_round_value(qbar: np.ndarray, *, gamma: float, a: float) -> float | np.ndarray:
    """Apply the exact stationary mean-balance identity to pre-update qbars."""

    values = np.asarray(qbar, dtype=np.float64)
    H = values.shape[-1]
    lam = lambda_gamma(gamma, a)
    weights = np.power(lam, np.arange(H - 1, -1, -1, dtype=np.float64))
    result = -(values @ weights) / (a * geometric_sum(H, lam))
    return float(result) if np.ndim(result) == 0 else result


def standard_error(values: Sequence[float] | np.ndarray) -> float:
    array = np.asarray(values, dtype=np.float64)
    if array.size < 2:
        return float("nan")
    return float(np.std(array, ddof=1) / np.sqrt(array.size))


def student_t_critical_95(df: int) -> float:
    if df < 1:
        return float("nan")
    if df <= 30:
        return _T_975[df]
    return 1.95996398454


def student_t_summary(values: Sequence[float] | np.ndarray) -> Summary:
    array = np.asarray(values, dtype=np.float64)
    if array.size < 2:
        value = float(array[0]) if array.size else float("nan")
        return Summary(value, float("nan"), float("nan"), float("nan"), float("nan"))
    mean = float(np.mean(array))
    std = float(np.std(array, ddof=1))
    se = std / np.sqrt(array.size)
    half = student_t_critical_95(array.size - 1) * se
    return Summary(mean, std, se, mean - half, mean + half)


def linear_fit(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    design = np.column_stack([np.ones(len(x), dtype=np.float64), np.asarray(x)])
    beta, _, _, _ = np.linalg.lstsq(design, np.asarray(y, dtype=np.float64), rcond=None)
    return float(beta[0]), float(beta[1])


def chain_level_bootstrap_fit(
    x_values: Sequence[float],
    chain_values_by_setting: Sequence[Sequence[float] | np.ndarray],
    *,
    repetitions: int,
    seed: int,
) -> dict[str, float | np.ndarray]:
    """Resample chains independently within every setting, then refit."""

    x = np.asarray(x_values, dtype=np.float64)
    chains = [np.asarray(values, dtype=np.float64) for values in chain_values_by_setting]
    if len(x) != len(chains) or any(values.size == 0 for values in chains):
        raise ValueError("Each x setting needs at least one chain estimate")
    setting_means = np.array([np.mean(values) for values in chains])
    beta0, beta1 = linear_fit(x, setting_means)

    rng = np.random.default_rng(seed)
    intercepts = np.empty(repetitions, dtype=np.float64)
    slopes = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        resampled_means = np.array(
            [np.mean(rng.choice(values, size=values.size, replace=True)) for values in chains]
        )
        intercepts[index], slopes[index] = linear_fit(x, resampled_means)
    low, high = np.quantile(intercepts, [0.025, 0.975])
    return {
        "intercept": beta0,
        "slope": beta1,
        "intercept_ci_low": float(low),
        "intercept_ci_high": float(high),
        "bootstrap_intercepts": intercepts,
        "bootstrap_slopes": slopes,
    }
