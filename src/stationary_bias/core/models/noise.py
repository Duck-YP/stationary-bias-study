"""Shared stochastic-noise mechanisms for the numerical studies."""

from __future__ import annotations

import numpy as np


NOISE_VARIANCES = {"rademacher": 1.0, "zero": 0.0}


def noise_variance(name: str) -> float:
    try:
        return NOISE_VARIANCES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown noise model: {name}") from exc


def sample_noise(
    name: str, rng: np.random.Generator, shape: int | tuple[int, ...]
) -> np.ndarray:
    if name == "rademacher":
        return 2.0 * rng.integers(0, 2, size=shape, dtype=np.int8).astype(np.float64) - 1.0
    if name == "zero":
        return np.zeros(shape, dtype=np.float64)
    raise ValueError(f"Unknown noise model: {name}")
