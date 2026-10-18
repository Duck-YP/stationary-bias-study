"""Frozen coordinatewise inference primitives for the formal study."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


_FORMAL_T_CRITICAL = {
    # Two-sided confidence level, degrees of freedom.
    (0.95, 7): 2.3646242515927844,
    (0.975, 7): 2.8412442485881835,
    (0.99, 7): 3.4994832973504924,
}


@dataclass(frozen=True)
class CoordinateInterval:
    mean: float
    sd: float
    se: float
    low: float
    high: float
    half_width: float
    confidence_level: float
    degrees_of_freedom: int


@dataclass(frozen=True)
class LinearFit:
    beta0: float
    beta1: float
    fitted: np.ndarray
    residuals: np.ndarray


def student_t_critical(confidence_level: float, degrees_of_freedom: int) -> float:
    """Return the exact critical value used by the frozen eight-chain protocol."""

    key = (float(confidence_level), int(degrees_of_freedom))
    try:
        return _FORMAL_T_CRITICAL[key]
    except KeyError as exc:
        raise ValueError(
            "Formal inference only defines df=7 at confidence 0.95, 0.975, or 0.99"
        ) from exc


def coordinate_interval(
    values: Sequence[float] | np.ndarray, *, confidence_level: float
) -> CoordinateInterval:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size != 8:
        raise ValueError("Coordinate inference requires eight chain estimates")
    if not np.all(np.isfinite(array)):
        raise ValueError("Formal coordinate estimates must be finite")
    df = array.size - 1
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=1))
    se = sd / np.sqrt(array.size)
    half_width = student_t_critical(confidence_level, df) * se
    return CoordinateInterval(
        mean=mean,
        sd=sd,
        se=se,
        low=mean - half_width,
        high=mean + half_width,
        half_width=half_width,
        confidence_level=float(confidence_level),
        degrees_of_freedom=df,
    )


def precision_thresholds(
    B20: Sequence[float] | np.ndarray,
    *,
    absolute: float = 0.0025,
    relative: float = 0.10,
) -> np.ndarray:
    targets = np.asarray(B20, dtype=np.float64)
    return np.maximum(float(absolute), float(relative) * np.abs(targets))


def evaluate_vector_precision(
    chain_balance_coefficients: np.ndarray,
    B20: Sequence[float] | np.ndarray,
    *,
    confidence_level: float = 0.975,
    absolute: float = 0.0025,
    relative: float = 0.10,
) -> dict[str, object]:
    values = np.asarray(chain_balance_coefficients, dtype=np.float64)
    targets = np.asarray(B20, dtype=np.float64)
    if values.shape != (8, targets.size):
        raise ValueError("Formal precision requires shape [8, d]")
    intervals = [
        coordinate_interval(values[:, coordinate], confidence_level=confidence_level)
        for coordinate in range(targets.size)
    ]
    half_widths = np.array([item.half_width for item in intervals])
    thresholds = precision_thresholds(
        targets, absolute=absolute, relative=relative
    )
    coordinate_pass = half_widths <= thresholds
    return {
        "intervals": intervals,
        "half_widths": half_widths,
        "thresholds": thresholds,
        "coordinate_pass": coordinate_pass,
        "joint_pass": bool(np.all(coordinate_pass)),
    }


def fit_delta_line(
    delta: Sequence[float] | np.ndarray,
    values: Sequence[float] | np.ndarray,
) -> LinearFit:
    x = np.asarray(delta, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or y.shape != x.shape or x.size < 2:
        raise ValueError("A delta fit needs at least two paired one-dimensional arrays")
    design = np.column_stack([np.ones(x.size, dtype=np.float64), x])
    beta, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != 2:
        raise ValueError("The frozen delta-only fit is not identifiable")
    fitted = design @ beta
    return LinearFit(
        beta0=float(beta[0]),
        beta1=float(beta[1]),
        fitted=fitted,
        residuals=y - fitted,
    )


def seed_block_bootstrap(
    delta: Sequence[float] | np.ndarray,
    values: np.ndarray,
    seed_labels: Sequence[int] | np.ndarray,
    *,
    repetitions: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    """Resample one seed index vector and reuse it across every setting."""

    x = np.asarray(delta, dtype=np.float64)
    data = np.asarray(values, dtype=np.float64)
    labels = np.asarray(seed_labels, dtype=int)
    if (
        data.ndim != 3
        or data.shape[:2] != (x.size, labels.size)
        or data.shape[2] < 1
    ):
        raise ValueError("Bootstrap values must have shape [settings, seeds, coordinates]")
    if labels.size != 8 or len(set(labels.tolist())) != 8:
        raise ValueError("Seed-block bootstrap requires eight unique frozen seed labels")
    if repetitions < 1 or not np.all(np.isfinite(data)):
        raise ValueError("Bootstrap repetitions and values must be valid")

    setting_means = np.mean(data, axis=1)
    base_fits = [fit_delta_line(x, setting_means[:, j]) for j in range(data.shape[2])]
    rng = np.random.default_rng(int(bootstrap_seed))
    sampled_indices = np.empty((repetitions, labels.size), dtype=np.int64)
    intercepts = np.empty((repetitions, data.shape[2]), dtype=np.float64)
    for replicate in range(repetitions):
        indices = rng.integers(0, labels.size, size=labels.size)
        sampled_indices[replicate] = indices
        # This single index vector is deliberately applied to every setting.
        replicate_means = np.mean(data[:, indices, :], axis=1)
        for coordinate in range(data.shape[2]):
            intercepts[replicate, coordinate] = fit_delta_line(
                x, replicate_means[:, coordinate]
            ).beta0
    return {
        "setting_means": setting_means,
        "fits": base_fits,
        "intercepts": intercepts,
        "sampled_indices": sampled_indices,
    }


def bootstrap_percentile_intervals(intercepts: np.ndarray) -> dict[str, np.ndarray]:
    values = np.asarray(intercepts, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("Formal bootstrap intercepts must have shape [replicates, 2]")
    return {
        "marginal_low": np.quantile(values, 0.025, axis=0),
        "marginal_high": np.quantile(values, 0.975, axis=0),
        "simultaneous_low": np.quantile(values, 0.0125, axis=0),
        "simultaneous_high": np.quantile(values, 0.9875, axis=0),
    }
