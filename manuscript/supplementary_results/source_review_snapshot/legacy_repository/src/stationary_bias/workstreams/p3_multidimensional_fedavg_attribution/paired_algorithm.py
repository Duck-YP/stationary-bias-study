"""Matched SCAFFOLD/FedAvg rounds with index-keyed common random numbers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..p2_multidimensional_validation.algorithm import (
    VectorBatchedRoundResult,
    scaffold_round_many_vector,
)
from ..p2_multidimensional_validation.noise import covariance_cholesky
from .algorithm import VectorFedAvgRoundResult, fedavg_round_many_vector


_P3_NOISE_DOMAIN = 0x4D444641  # Frozen domain separator; do not change.
_KEY_CONSTANTS = (
    0x9E3779B97F4A7C15,
    0xBF58476D1CE4E5B9,
    0x94D049BB133111EB,
    0xD2B74407B1CE6E93,
)


def _splitmix64(values: np.ndarray) -> np.ndarray:
    """Vectorized stateless 64-bit mixer used only to generate keyed signs."""

    with np.errstate(over="ignore"):
        mixed = values + np.uint64(0x9E3779B97F4A7C15)
        mixed = (mixed ^ (mixed >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        mixed = (mixed ^ (mixed >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        return mixed ^ (mixed >> np.uint64(31))


def _indexed_signs(
    seed: int,
    rounds: np.ndarray,
    local_steps: np.ndarray,
    clients: np.ndarray,
    coordinates: np.ndarray,
) -> np.ndarray:
    with np.errstate(over="ignore"):
        keys = (
            np.uint64(_P3_NOISE_DOMAIN)
            ^ np.uint64(seed) * np.uint64(_KEY_CONSTANTS[0])
            ^ rounds * np.uint64(_KEY_CONSTANTS[1])
            ^ local_steps * np.uint64(_KEY_CONSTANTS[2])
            ^ clients * np.uint64(_KEY_CONSTANTS[3])
            ^ coordinates
        )
    bits = _splitmix64(keys) & np.uint64(1)
    return np.where(bits == 0, -1.0, 1.0)


def indexed_noise_vector(
    seed: int,
    round_index: int,
    client_index: int,
    local_step: int,
    covariance: np.ndarray,
) -> np.ndarray:
    """Return one noise vector keyed only by the scientific index tuple."""

    if min(seed, round_index, client_index, local_step) < 0:
        raise ValueError("noise indices must be non-negative")
    factor = covariance_cholesky(covariance)
    coordinates = np.arange(factor.shape[0], dtype=np.uint64)
    signs = _indexed_signs(
        int(seed),
        np.asarray(np.uint64(round_index)),
        np.asarray(np.uint64(local_step)),
        np.asarray(np.uint64(client_index)),
        coordinates,
    )
    return factor @ signs


def indexed_noise_block(
    seeds: Sequence[int],
    *,
    round_start: int,
    rounds: int,
    H: int,
    N: int,
    covariance: np.ndarray,
) -> np.ndarray:
    """Build ``[pairs, rounds, H, clients, d]`` without mutable RNG state."""

    if not seeds or min(round_start, rounds - 1, H - 1, N - 1) < 0:
        raise ValueError("seeds and positive block dimensions are required")
    factor = covariance_cholesky(covariance)
    dimension = factor.shape[0]
    block = np.empty((len(seeds), rounds, H, N, dimension), dtype=np.float64)
    round_keys = np.arange(round_start, round_start + rounds, dtype=np.uint64)[:, None, None, None]
    local_keys = np.arange(H, dtype=np.uint64)[None, :, None, None]
    client_keys = np.arange(N, dtype=np.uint64)[None, None, :, None]
    coordinate_keys = np.arange(dimension, dtype=np.uint64)[None, None, None, :]
    for pair, seed in enumerate(seeds):
        signs = _indexed_signs(
            int(seed), round_keys, local_keys, client_keys, coordinate_keys
        )
        block[pair] = np.einsum("ij,...j->...i", factor, signs)
    return block


@dataclass(frozen=True)
class PairedRoundResult:
    scaffold: VectorBatchedRoundResult
    fedavg: VectorFedAvgRoundResult
    crn_integrity: np.ndarray


def paired_round_many_vector(
    x_scaffold: np.ndarray,
    xi_scaffold: np.ndarray,
    x_fedavg: np.ndarray,
    *,
    gamma: float,
    H: int,
    objective: object,
    epsilon_steps: np.ndarray,
) -> PairedRoundResult:
    """Advance separate algorithm states using the exact same noise array."""

    shared = np.array(epsilon_steps, dtype=np.float64, copy=True)
    reference = shared.copy()
    shared.setflags(write=False)
    scaffold = scaffold_round_many_vector(
        x_scaffold,
        xi_scaffold,
        gamma=gamma,
        H=H,
        objective=objective,
        epsilon_steps=shared,
    )
    scaffold_noise_unchanged = np.all(shared == reference, axis=(1, 2, 3))
    fedavg = fedavg_round_many_vector(
        x_fedavg,
        gamma=gamma,
        H=H,
        objective=objective,
        epsilon_steps=shared,
    )
    fedavg_noise_unchanged = np.all(shared == reference, axis=(1, 2, 3))
    return PairedRoundResult(
        scaffold=scaffold,
        fedavg=fedavg,
        crn_integrity=scaffold_noise_unchanged & fedavg_noise_unchanged,
    )
