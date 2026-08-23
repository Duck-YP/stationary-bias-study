"""Exact one-round recursion for the frozen one-dimensional SCAFFOLD model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .noise_models import sample_noise
from .objectives import Objective


@dataclass(frozen=True)
class RoundResult:
    x_new: float
    xi_new: np.ndarray
    qbar: np.ndarray
    theta_final: np.ndarray
    abs_control_sum: float


@dataclass(frozen=True)
class BatchedRoundResult:
    x_new: np.ndarray
    xi_new: np.ndarray
    qbar: np.ndarray
    theta_final: np.ndarray
    abs_control_sum: np.ndarray


def scaffold_round(
    x: float,
    xi: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: Objective,
    noise: str = "rademacher",
    rng: np.random.Generator | None = None,
    epsilon_steps: np.ndarray | None = None,
) -> RoundResult:
    """Run the exact recursion, recording qbar on pre-update local states."""

    controls = np.asarray(xi, dtype=np.float64)
    if controls.ndim != 1 or controls.size == 0:
        raise ValueError("xi must be a non-empty one-dimensional vector")
    if gamma <= 0.0 or H < 1:
        raise ValueError("gamma must be positive and H must be at least one")
    if epsilon_steps is None:
        if rng is None:
            raise ValueError("rng is required when epsilon_steps is not supplied")
        noises = np.stack([sample_noise(noise, rng, controls.shape) for _ in range(H)])
    else:
        noises = np.asarray(epsilon_steps, dtype=np.float64)
        if noises.shape != (H, controls.size):
            raise ValueError(f"epsilon_steps must have shape {(H, controls.size)}")

    theta = np.full(controls.shape, float(x), dtype=np.float64)
    qbar = np.empty(H, dtype=np.float64)
    for h in range(H):
        qbar[h] = float(np.mean(objective.q(theta)))
        theta = theta - gamma * (objective.grad(theta) + controls + noises[h])

    x_new = float(np.mean(theta))
    xi_new = controls + (theta - x_new) / (gamma * H)
    return RoundResult(
        x_new=x_new,
        xi_new=xi_new,
        qbar=qbar,
        theta_final=theta,
        abs_control_sum=float(abs(np.sum(xi_new))),
    )


def scaffold_round_many(
    x: np.ndarray,
    xi: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: Objective,
    epsilon_steps: np.ndarray,
) -> BatchedRoundResult:
    """Vectorize an exact round across independent chains.

    The leading axis is the chain axis. Randomness is supplied explicitly so
    each chain can be driven by its own RNG stream.
    """

    global_states = np.asarray(x, dtype=np.float64)
    controls = np.asarray(xi, dtype=np.float64)
    noises = np.asarray(epsilon_steps)
    if global_states.ndim != 1 or controls.ndim != 2:
        raise ValueError("x and xi must have shapes [chains] and [chains, clients]")
    if controls.shape[0] != global_states.size:
        raise ValueError("x and xi chain counts differ")
    if noises.shape != (global_states.size, H, controls.shape[1]):
        raise ValueError("epsilon_steps has the wrong shape")

    theta = np.repeat(global_states[:, None], controls.shape[1], axis=1)
    qbar = np.empty((global_states.size, H), dtype=np.float64)
    for h in range(H):
        qbar[:, h] = np.mean(objective.q(theta), axis=1)
        theta = theta - gamma * (objective.grad(theta) + controls + noises[:, h, :])

    x_new = np.mean(theta, axis=1)
    xi_new = controls + (theta - x_new[:, None]) / (gamma * H)
    return BatchedRoundResult(
        x_new=x_new,
        xi_new=xi_new,
        qbar=qbar,
        theta_final=theta,
        abs_control_sum=np.abs(np.sum(xi_new, axis=1)),
    )


def generate_noise_block(
    rngs: Sequence[np.random.Generator],
    noise: str,
    *,
    rounds: int,
    H: int,
    N: int,
) -> np.ndarray:
    """Generate a block while preserving one independent RNG per chain."""

    if noise == "zero":
        return np.zeros((len(rngs), rounds, H, N), dtype=np.int8)
    if noise != "rademacher":
        raise ValueError(f"Unknown noise model: {noise}")
    block = np.empty((len(rngs), rounds, H, N), dtype=np.int8)
    for chain_index, rng in enumerate(rngs):
        block[chain_index] = 2 * rng.integers(
            0, 2, size=(rounds, H, N), dtype=np.int8
        ) - 1
    return block
