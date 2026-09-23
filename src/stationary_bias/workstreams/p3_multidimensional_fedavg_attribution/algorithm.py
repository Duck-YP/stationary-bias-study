"""Exact vector FedAvg recursion with no control state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class VectorObjective(Protocol):
    dimension: int

    def grad(self, x: np.ndarray) -> np.ndarray: ...

    def q(self, x: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class VectorFedAvgRoundResult:
    x_new: np.ndarray
    qbar: np.ndarray
    theta_final: np.ndarray


def fedavg_round_many_vector(
    x: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: VectorObjective,
    epsilon_steps: np.ndarray,
) -> VectorFedAvgRoundResult:
    """Run one exact FedAvg round for independent vector-valued chains.

    ``x`` has shape ``[chains, d]`` and ``epsilon_steps`` has shape
    ``[chains, H, clients, d]``. The kernel has no control or auxiliary
    client state and never creates a hidden random-number stream.
    """

    global_states = np.asarray(x, dtype=np.float64)
    noises = np.asarray(epsilon_steps, dtype=np.float64)
    dimension = objective.dimension
    if global_states.ndim != 2 or global_states.shape[1] != dimension:
        raise ValueError("x must have shape [chains, d]")
    if gamma <= 0.0 or H < 1:
        raise ValueError("gamma must be positive and H must be at least one")
    if noises.ndim != 4:
        raise ValueError("epsilon_steps must have shape [chains, H, clients, d]")
    if noises.shape[:2] != (global_states.shape[0], H):
        raise ValueError("epsilon_steps chain or local-step dimension differs")
    if noises.shape[2] < 1 or noises.shape[3] != dimension:
        raise ValueError("epsilon_steps needs clients > 0 and final dimension d")

    theta = np.repeat(global_states[:, None, :], noises.shape[2], axis=1)
    qbar = np.empty((global_states.shape[0], H, dimension), dtype=np.float64)
    for h in range(H):
        q_values = objective.q(theta)
        gradients = objective.grad(theta)
        if q_values.shape != theta.shape or gradients.shape != theta.shape:
            raise ValueError("objective grad and q must preserve the input shape")
        qbar[:, h, :] = np.mean(q_values, axis=1)
        theta = theta - gamma * (gradients + noises[:, h, :, :])

    return VectorFedAvgRoundResult(
        x_new=np.mean(theta, axis=1),
        qbar=qbar,
        theta_final=theta,
    )
