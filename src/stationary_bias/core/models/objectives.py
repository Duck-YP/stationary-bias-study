"""Shared one-dimensional objectives used by the numerical studies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


ArrayLike = float | np.ndarray


def log_cosh(x: ArrayLike) -> ArrayLike:
    """Numerically stable log(cosh(x))."""

    values = np.asarray(x, dtype=np.float64)
    result = np.logaddexp(values, -values) - np.log(2.0)
    return float(result) if result.ndim == 0 else result


def nonlinear_grad(x: ArrayLike) -> ArrayLike:
    values = np.asarray(x, dtype=np.float64)
    result = values + 0.5 * np.asarray(log_cosh(values))
    return float(result) if result.ndim == 0 else result


def nonlinear_second(x: ArrayLike) -> ArrayLike:
    values = np.asarray(x, dtype=np.float64)
    result = 1.0 + 0.5 * np.tanh(values)
    return float(result) if result.ndim == 0 else result


def quadratic_grad(x: ArrayLike) -> ArrayLike:
    values = np.asarray(x, dtype=np.float64)
    return float(values) if values.ndim == 0 else values.copy()


def quadratic_second(x: ArrayLike) -> ArrayLike:
    values = np.asarray(x, dtype=np.float64)
    result = np.ones_like(values)
    return float(result) if result.ndim == 0 else result


@dataclass(frozen=True)
class Objective:
    name: str
    a: float
    tau: float
    mu: float
    L: float
    grad: Callable[[ArrayLike], ArrayLike]
    second: Callable[[ArrayLike], ArrayLike]

    def q(self, x: ArrayLike) -> ArrayLike:
        values = np.asarray(x, dtype=np.float64)
        result = np.asarray(self.grad(values)) - self.a * values
        return float(result) if result.ndim == 0 else result


MAIN_OBJECTIVE = Objective(
    name="nonlinear_main",
    a=1.0,
    tau=0.5,
    mu=0.5,
    L=1.5,
    grad=nonlinear_grad,
    second=nonlinear_second,
)

QUADRATIC_OBJECTIVE = Objective(
    name="quadratic",
    a=1.0,
    tau=0.0,
    mu=1.0,
    L=1.0,
    grad=quadratic_grad,
    second=quadratic_second,
)


def get_objective(name: str) -> Objective:
    if name == MAIN_OBJECTIVE.name:
        return MAIN_OBJECTIVE
    if name == QUADRATIC_OBJECTIVE.name:
        return QUADRATIC_OBJECTIVE
    raise ValueError(f"Unknown objective: {name}")
