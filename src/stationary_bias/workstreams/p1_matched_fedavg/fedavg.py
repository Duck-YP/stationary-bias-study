"""Exact one-round recursion for matched one-dimensional homogeneous FedAvg."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.models.objectives import Objective


@dataclass(frozen=True)
class FedAvgRoundResult:
    """Result of one scalar-chain FedAvg communication round."""

    x_new: float
    qbar: np.ndarray
    theta_final: np.ndarray


@dataclass(frozen=True)
class BatchedFedAvgRoundResult:
    """Result of one FedAvg round vectorized across independent chains."""

    x_new: np.ndarray
    qbar: np.ndarray
    theta_final: np.ndarray


def fedavg_round(
    x: float,
    *,
    gamma: float,
    H: int,
    objective: Objective,
    epsilon_steps: np.ndarray,
) -> FedAvgRoundResult:
    """Run one exact FedAvg round using an explicitly supplied noise tensor.

    No client or server control state exists in this kernel.  Recording qbar
    on the pre-update local states permits the same stationary mean-balance
    identity used by the homogeneous SCAFFOLD study: after decomposing
    ``grad(theta) = a * theta + q(theta)``, the expected averaged recursion
    depends only on these qbar values and mean-zero additive noise.
    """

    if gamma <= 0.0 or H < 1:
        raise ValueError("gamma must be positive and H must be at least one")
    noises = np.asarray(epsilon_steps)
    if noises.ndim != 2 or noises.shape[0] != H or noises.shape[1] == 0:
        raise ValueError("epsilon_steps must have shape [H, clients] with clients > 0")

    theta = np.full(noises.shape[1], float(x), dtype=np.float64)
    qbar = np.empty(H, dtype=np.float64)
    for h in range(H):
        qbar[h] = float(np.mean(objective.q(theta)))
        theta = theta - gamma * (objective.grad(theta) + noises[h])

    return FedAvgRoundResult(
        x_new=float(np.mean(theta)),
        qbar=qbar,
        theta_final=theta,
    )


def fedavg_round_many(
    x: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: Objective,
    epsilon_steps: np.ndarray,
) -> BatchedFedAvgRoundResult:
    """Vectorize one exact FedAvg round across independent chains.

    ``epsilon_steps`` has shape ``[chains, H, clients]`` and is supplied by
    the matched experiment.  The kernel never creates a hidden RNG stream.
    """

    global_states = np.asarray(x, dtype=np.float64)
    noises = np.asarray(epsilon_steps)
    if global_states.ndim != 1:
        raise ValueError("x must have shape [chains]")
    if gamma <= 0.0 or H < 1:
        raise ValueError("gamma must be positive and H must be at least one")
    if noises.ndim != 3:
        raise ValueError("epsilon_steps must have shape [chains, H, clients]")
    if noises.shape[0] != global_states.size or noises.shape[1] != H:
        raise ValueError("epsilon_steps must have shape [chains, H, clients]")
    if noises.shape[2] == 0:
        raise ValueError("epsilon_steps needs at least one client")

    theta = np.repeat(global_states[:, None], noises.shape[2], axis=1)
    qbar = np.empty((global_states.size, H), dtype=np.float64)
    for h in range(H):
        qbar[:, h] = np.mean(objective.q(theta), axis=1)
        theta = theta - gamma * (objective.grad(theta) + noises[:, h, :])

    return BatchedFedAvgRoundResult(
        x_new=np.mean(theta, axis=1),
        qbar=qbar,
        theta_final=theta,
    )
