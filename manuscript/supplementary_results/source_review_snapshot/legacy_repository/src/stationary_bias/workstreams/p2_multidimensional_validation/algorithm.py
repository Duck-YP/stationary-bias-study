"""Coordinate-aware SCAFFOLD kernel isolated from the frozen scalar kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class VectorObjective(Protocol):
    dimension: int

    def grad(self, x: np.ndarray) -> np.ndarray: ...

    def q(self, x: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class VectorBatchedRoundResult:
    x_new: np.ndarray
    xi_new: np.ndarray
    qbar: np.ndarray
    theta_final: np.ndarray
    control_sum: np.ndarray
    max_abs_control_sum: np.ndarray


def scaffold_round_many_vector(
    x: np.ndarray,
    xi: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: VectorObjective,
    epsilon_steps: np.ndarray,
) -> VectorBatchedRoundResult:
    """Run one vector SCAFFOLD round across independent chains."""

    global_states = np.asarray(x, dtype=np.float64)
    controls = np.asarray(xi, dtype=np.float64)
    noises = np.asarray(epsilon_steps, dtype=np.float64)
    dimension = objective.dimension
    if global_states.ndim != 2 or global_states.shape[1] != dimension:
        raise ValueError("x must have shape [chains, d]")
    if controls.ndim != 3 or controls.shape[0] != global_states.shape[0]:
        raise ValueError("xi must have shape [chains, clients, d]")
    if controls.shape[1] == 0 or controls.shape[2] != dimension:
        raise ValueError("xi must have shape [chains, clients, d] with clients > 0")
    expected_noise_shape = (
        global_states.shape[0],
        H,
        controls.shape[1],
        dimension,
    )
    if noises.shape != expected_noise_shape:
        raise ValueError(f"epsilon_steps must have shape {expected_noise_shape}")
    if gamma <= 0.0 or H < 1:
        raise ValueError("gamma must be positive and H must be at least one")

    theta = np.repeat(global_states[:, None, :], controls.shape[1], axis=1)
    qbar = np.empty((global_states.shape[0], H, dimension), dtype=np.float64)
    for h in range(H):
        q_values = objective.q(theta)
        if q_values.shape != theta.shape:
            raise ValueError("objective.q must preserve the input shape")
        qbar[:, h, :] = np.mean(q_values, axis=1)
        gradients = objective.grad(theta)
        if gradients.shape != theta.shape:
            raise ValueError("objective.grad must preserve the input shape")
        theta = theta - gamma * (gradients + controls + noises[:, h, :, :])

    x_new = np.mean(theta, axis=1)
    xi_new = controls + (theta - x_new[:, None, :]) / (gamma * H)
    control_sum = np.sum(xi_new, axis=1)
    return VectorBatchedRoundResult(
        x_new=x_new,
        xi_new=xi_new,
        qbar=qbar,
        theta_final=theta,
        control_sum=control_sum,
        max_abs_control_sum=np.max(np.abs(control_sum), axis=1),
    )

