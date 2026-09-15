"""Frozen-matrix loading and execution for the P2 formal coefficient study."""

from __future__ import annotations

import hashlib
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from ...core.artifacts import (
    create_staging_directory,
    rebase_staged_paths,
    require_complete_existing_output,
    replace_output_directory,
    validate_controlled_overwrite,
)
from ...core.inference.statistics import standard_error
from ...core.inference.validation import estimator_agreement, stationarity_check
from ...core.io import (
    REPO_ROOT,
    environment_manifest,
    gamma_token,
    load_yaml,
    write_csv,
    write_json,
)
from .formal_inference import evaluate_vector_precision
from .objective import RankOneVectorObjective
from .simulation import _advance_block
from .theory import normalize_vector_bias, vector_theory_targets


P2_FORMAL_ROOT = REPO_ROOT / "workstreams" / "p2_multidimensional_validation"
P2_FORMAL_CONFIG_ROOT = P2_FORMAL_ROOT / "configs"
P2_PRIMARY_CONFIG_PATH = P2_FORMAL_CONFIG_ROOT / "d2_coefficient_primary.yaml"
P2_H4_SMALL_CONFIG_PATH = (
    P2_FORMAL_CONFIG_ROOT / "d2_h4_small_step_confirmation.yaml"
)
P2_FORMAL_PROTOCOL_PATH = P2_FORMAL_ROOT / "formal_protocol.md"
P2_D5_CONFIG_PATH = P2_FORMAL_CONFIG_ROOT / "d5_controlled_validation.yaml"
P2_D5_PROTOCOL_PATH = P2_FORMAL_ROOT / "d5_protocol.md"
P2_RUN_START_PROVENANCE = "run_start_provenance.json"
P2_FORMAL_MANIFEST = "formal_manifest.json"
P2_RAW_RESULT_FILES = ("run_summary.csv", "batch_summary.csv")
P2_ROW_PROVENANCE_FIELDS = {
    "source_commit",
    "source_dirty_at_run_start",
}
FORMAL_TARGETS = ("primary", "h4-small-step")


@dataclass(frozen=True)
class FormalRunSpec:
    matrix_id: str
    target: str
    setting_id: str
    d: int
    H: int
    N: int
    gamma: float
    delta: float
    seed: int
    x0: np.ndarray

    @property
    def setting_key(self) -> tuple[int, int, float]:
        return self.H, self.N, self.gamma

    @property
    def run_id(self) -> str:
        return (
            f"p2__phase-formal__matrix-{self.matrix_id}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def formal_config_path(target: str) -> Path:
    if target == "primary":
        return P2_PRIMARY_CONFIG_PATH
    if target == "h4-small-step":
        return P2_H4_SMALL_CONFIG_PATH
    if target == "d5":
        return P2_D5_CONFIG_PATH
    raise ValueError(f"Unknown P2 formal target: {target}")


def formal_protocol_path(target: str) -> Path:
    return P2_D5_PROTOCOL_PATH if target == "d5" else P2_FORMAL_PROTOCOL_PATH


def load_formal_config(target: str) -> dict[str, Any]:
    return load_yaml(formal_config_path(target))


def formal_artifact_root(target: str, config: dict[str, Any] | None = None) -> Path:
    config = config or load_formal_config(target)
    return REPO_ROOT / str(config["artifact_namespace"])


def _path_definition(target: str, config: dict[str, Any]) -> tuple[list[int], list[dict[str, Any]]]:
    if target in ("primary", "d5"):
        item = config["primary_joint_path"]
        return [int(value) for value in item["H_values"]], list(item["path"])
    item = config["smaller_step_path"]
    return [int(item["H"])], list(item["path"])


def build_formal_run_matrix(
    target: str, config: dict[str, Any] | None = None
) -> list[FormalRunSpec]:
    config = config or load_formal_config(target)
    H_values, path = _path_definition(target, config)
    d = int(config["objective"]["d"])
    x0 = np.asarray(config["objective"]["x_star"], dtype=np.float64)
    seeds = [int(seed) for seed in config["chains"]["seeds"]]
    matrix_id = str(config["matrix_identifier"])
    specs: list[FormalRunSpec] = []
    for H in H_values:
        for point in path:
            denominator = int(point["gamma_denominator"])
            N = int(point["N"])
            gamma = 1.0 / denominator
            delta = gamma + 1.0 / N
            setting_id = (
                f"{matrix_id}__H{H}__N{N}__g{gamma_token(gamma)}"
            )
            for seed in seeds:
                specs.append(
                    FormalRunSpec(
                        matrix_id=matrix_id,
                        target=target,
                        setting_id=setting_id,
                        d=d,
                        H=H,
                        N=N,
                        gamma=gamma,
                        delta=delta,
                        seed=seed,
                        x0=x0.copy(),
                    )
                )
    return specs


def audit_formal_run_matrix(
    target: str, runs: Sequence[FormalRunSpec] | None = None
) -> dict[str, Any]:
    runs = list(runs or build_formal_run_matrix(target))
    run_ids = [item.run_id for item in runs]
    settings = sorted({item.setting_key for item in runs})
    return {
        "matrix_id": runs[0].matrix_id if runs else "",
        "target": target,
        "settings": len(settings),
        "chains": len(runs),
        "chains_per_setting": sorted(
            sum(item.setting_key == setting for item in runs) for setting in settings
        ),
        "H_values": sorted({item.H for item in runs}),
        "N_values": sorted({item.N for item in runs}),
        "seeds": sorted({item.seed for item in runs}),
        "unique_run_ids": len(set(run_ids)),
        "all_unique": len(run_ids) == len(set(run_ids)),
        "gamma_equals_inverse_N": all(
            item.gamma == 1.0 / item.N for item in runs
        ),
    }


def objective_from_formal_config(config: dict[str, Any]) -> RankOneVectorObjective:
    item = config["objective"]
    return RankOneVectorObjective(
        np.asarray(item["A"], dtype=np.float64),
        np.asarray(item["u"], dtype=np.float64),
        float(item["alpha"]),
    )


def covariance_from_formal_config(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["noise"]["covariance"], dtype=np.float64)


def _assert_config_agreement(
    primary: dict[str, Any], confirmation: dict[str, Any]
) -> None:
    for key in ("d", "A", "u", "alpha", "x_star", "global_hessian_bounds"):
        if primary["objective"][key] != confirmation["objective"][key]:
            raise RuntimeError(f"Frozen P2 objective configs disagree on {key}")
    for key in (
        "noise",
        "protocol",
        "per_setting_uncertainty",
        "precision_stopping",
        "extrapolation",
    ):
        if primary[key] != confirmation[key]:
            raise RuntimeError(f"Frozen P2 configs disagree on {key}")
    primary_h4 = primary["theory"]["by_H"][4]
    for key in ("B20", "B20_local", "B20_ctrl"):
        if primary_h4[key] != confirmation["theory"][key]:
            raise RuntimeError(f"Frozen P2 H=4 theory configs disagree on {key}")


def check_formal_protocol() -> dict[str, Any]:
    primary = load_formal_config("primary")
    confirmation = load_formal_config("h4-small-step")
    _assert_config_agreement(primary, confirmation)
    expected_objective = {
        "d": 2,
        "A": [[1.2, 0.2], [0.2, 1.0]],
        "u": [0.7071067811865475, 0.7071067811865475],
        "alpha": 0.25,
        "x_star": [0.0, 0.0],
        "global_hessian_bounds": {
            "mu": 0.85,
            "L": 1.565036762718386,
        },
    }
    for key, expected in expected_objective.items():
        if primary["objective"][key] != expected:
            raise RuntimeError(f"Frozen P2 objective value changed: {key}")
    expected_noise = {
        "covariance": [[1.0, 0.2], [0.2, 0.7]],
        "covariance_eigenvalues": [0.6, 1.1],
        "A_C_minus_C_A": [[0.0, -0.02], [0.02, 0.0]],
    }
    for key, expected in expected_noise.items():
        if primary["noise"][key] != expected:
            raise RuntimeError(f"Frozen P2 noise value changed: {key}")
    expected_protocol = {
        "mixing_mu": 0.85,
        "burn_in_multiples": 100,
        "batch_length_multiples": 20,
        "min_batches": 100,
        "max_batches": 400,
        "extension_batches": 50,
        "max_abs_control_sum": 1.0e-10,
        "estimator_agreement_z": 3.0,
        "stationarity_z": 3.0,
        "stationarity_min_chains": 7,
    }
    for key, expected in expected_protocol.items():
        if primary["protocol"][key] != expected:
            raise RuntimeError(f"Frozen P2 protocol value changed: {key}")
    uncertainty = primary["per_setting_uncertainty"]
    if (
        uncertainty["degrees_of_freedom"] != 7
        or uncertainty["familywise_confidence_level"] != 0.95
        or uncertainty["simultaneous_coordinate_confidence_level"] != 0.975
        or uncertainty["marginal_diagnostic_confidence_level"] != 0.95
    ):
        raise RuntimeError("Frozen P2 uncertainty levels changed")
    stopping = primary["precision_stopping"]
    if (
        stopping["absolute_half_width"] != 0.0025
        or stopping["relative_half_width"] != 0.10
        or stopping["check_after_batches"] != 100
        or stopping["extend_by_batches"] != 50
        or stopping["stop_at_batches"] != 400
    ):
        raise RuntimeError("Frozen P2 precision rule changed")
    extrapolation = primary["extrapolation"]
    if (
        extrapolation["model"] != "C_hat_j = beta0_j + beta1_j * delta"
        or extrapolation["delta"] != "gamma + 1/N"
        or extrapolation["coefficient_estimate"] != "beta0_j"
    ):
        raise RuntimeError("Frozen P2 extrapolation model changed")
    if (
        primary["bootstrap"]["seed"] != 2901
        or confirmation["bootstrap"]["seed"] != 2902
        or primary["bootstrap"]["repetitions"] != 2000
        or confirmation["bootstrap"]["repetitions"] != 2000
        or primary["bootstrap"]["simultaneous_quantiles"] != [0.0125, 0.9875]
        or confirmation["bootstrap"]["simultaneous_quantiles"]
        != [0.0125, 0.9875]
    ):
        raise RuntimeError("Frozen P2 bootstrap protocol changed")
    expected_namespaces = {
        "primary": (
            "workstreams/p2_multidimensional_validation/artifacts/formal/"
            "p2-d2-coefficient-primary"
        ),
        "h4-small-step": (
            "workstreams/p2_multidimensional_validation/artifacts/formal/"
            "p2-d2-h4-small-step-confirmation"
        ),
    }
    if primary["artifact_namespace"] != expected_namespaces["primary"]:
        raise RuntimeError("Frozen P2 primary artifact namespace changed")
    if confirmation["artifact_namespace"] != expected_namespaces["h4-small-step"]:
        raise RuntimeError("Frozen P2 confirmation artifact namespace changed")
    if (
        primary["protocol_status"] != "frozen_not_executed"
        or confirmation["protocol_status"] != "frozen_not_executed"
        or primary["interpretation_boundary"] != "consistency_test_not_proof"
        or confirmation["interpretation_boundary"] != "consistency_test_not_proof"
    ):
        raise RuntimeError("Frozen P2 protocol identity changed")
    expected_audits = {
        "primary": {
            "matrix_id": "p2-d2-coefficient-primary",
            "target": "primary",
            "settings": 10,
            "chains": 80,
            "chains_per_setting": [8] * 10,
            "H_values": [2, 4],
            "N_values": [12, 16, 24, 32, 48],
            "seeds": list(range(901, 909)),
            "unique_run_ids": 80,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
        "h4-small-step": {
            "matrix_id": "p2-d2-h4-small-step-confirmation",
            "target": "h4-small-step",
            "settings": 4,
            "chains": 32,
            "chains_per_setting": [8] * 4,
            "H_values": [4],
            "N_values": [64, 96, 128, 192],
            "seeds": list(range(1001, 1009)),
            "unique_run_ids": 32,
            "all_unique": True,
            "gamma_equals_inverse_N": True,
        },
    }
    for target, expected in expected_audits.items():
        observed = audit_formal_run_matrix(target)
        if observed != expected:
            raise RuntimeError(
                f"P2 {target} matrix differs from its frozen protocol: {observed}"
            )

    objective = objective_from_formal_config(primary)
    covariance = covariance_from_formal_config(primary)
    if np.min(np.linalg.eigvalsh(covariance)) <= 0.0:
        raise RuntimeError("Frozen P2 covariance is not positive definite")
    if np.allclose(
        objective.A @ covariance - covariance @ objective.A,
        0.0,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise RuntimeError("Frozen P2 covariance unexpectedly commutes with A")
    for H in (2, 4):
        targets = vector_theory_targets(objective, covariance, H)
        configured = primary["theory"]["by_H"][H]
        checks = (
            (targets.S_C, primary["theory"]["S_C"], "S_C"),
            (targets.B10, primary["theory"]["B10"], "B10"),
            (targets.B20, configured["B20"], f"H={H} B20"),
            (targets.B20_local, configured["B20_local"], f"H={H} B20_local"),
            (targets.B20_ctrl, configured["B20_ctrl"], f"H={H} B20_ctrl"),
        )
        for actual, expected, label in checks:
            if not np.allclose(actual, expected, rtol=0.0, atol=1.0e-14):
                raise RuntimeError(f"Frozen P2 theory mismatch for {label}")
        if not np.allclose(
            targets.B20_local + targets.B20_ctrl,
            targets.B20,
            rtol=0.0,
            atol=1.0e-15,
        ):
            raise RuntimeError(f"Frozen P2 theory decomposition fails for H={H}")

    if not P2_FORMAL_PROTOCOL_PATH.is_file():
        raise RuntimeError("Missing frozen P2 formal protocol document")
    protocol_text = P2_FORMAL_PROTOCOL_PATH.read_text(encoding="utf-8")
    required_protocol_fragments = (
        "C_hat(gamma, N, H) = [b_hat(gamma, N, H) - (gamma/N) B10] / gamma^2",
        "A = [[1.2, 0.2], [0.2, 1.0]]",
        "C = [[1.0, 0.2], [0.2, 0.7]]",
        "(gamma, N) = (1/12,12), (1/16,16), (1/24,24), (1/32,32), (1/48,48)",
        "(gamma, N) = (1/64,64), (1/96,96), (1/128,128), (1/192,192)",
        "Primary seeds are `901` through `908`",
        "seeds `1001` through `1008`",
        "h_j <= max(0.0025, 0.10 * abs(B20_j(H)))",
        "C_hat_j = beta0_j + beta1_j delta",
        "2,000 replicates and seed `2902`",
        expected_namespaces["primary"] + "/",
        expected_namespaces["h4-small-step"] + "/",
    )
    missing_fragments = [
        fragment for fragment in required_protocol_fragments if fragment not in protocol_text
    ]
    if missing_fragments:
        raise RuntimeError(
            "Frozen P2 protocol document disagrees with config/code: "
            + repr(missing_fragments)
        )
    return {
        "status": "PASS",
        "workstream": "p2",
        "phase": "formal_pipeline_check_only",
        "protocol_status": primary["protocol_status"],
        "primary": expected_audits["primary"],
        "h4_small_step": expected_audits["h4-small-step"],
        "bootstrap": {
            "primary_seed": int(primary["bootstrap"]["seed"]),
            "h4_small_step_seed": int(confirmation["bootstrap"]["seed"]),
            "repetitions": int(primary["bootstrap"]["repetitions"]),
        },
        "config_sha256": {
            target: hashlib.sha256(formal_config_path(target).read_bytes()).hexdigest()
            for target in FORMAL_TARGETS
        },
        "protocol_sha256": hashlib.sha256(
            P2_FORMAL_PROTOCOL_PATH.read_bytes()
        ).hexdigest(),
        "scientific_execution": "NOT_RUN",
    }


def check_d5_protocol() -> dict[str, Any]:
    """Audit every frozen d=5 scientific input without simulating a trajectory."""

    config = load_formal_config("d5")
    expected_objective = {
        "d": 5,
        "A": [
            [1.40, 0.15, 0.00, 0.00, 0.00],
            [0.15, 1.20, 0.12, 0.00, 0.00],
            [0.00, 0.12, 1.10, 0.10, 0.00],
            [0.00, 0.00, 0.10, 1.30, 0.08],
            [0.00, 0.00, 0.00, 0.08, 1.00],
        ],
        "v": [1.0, 2.0, -1.0, 1.5, -0.5],
        "alpha": 0.25,
        "x_star": [0.0] * 5,
    }
    for key, expected in expected_objective.items():
        if config["objective"][key] != expected:
            raise RuntimeError(f"Frozen P2 d=5 objective value changed: {key}")
    objective = objective_from_formal_config(config)
    covariance = covariance_from_formal_config(config)
    v = np.asarray(config["objective"]["v"], dtype=np.float64)
    u = np.asarray(config["objective"]["u"], dtype=np.float64)
    if not np.allclose(u, v / np.linalg.norm(v), rtol=0.0, atol=1.0e-15):
        raise RuntimeError("Frozen P2 d=5 direction is not normalized v")
    if not (np.any(u > 0.0) and np.any(u < 0.0) and np.count_nonzero(u) > 1):
        raise RuntimeError("Frozen P2 d=5 direction lost its mixed non-axis structure")
    if not np.allclose(objective.A, objective.A.T, rtol=0.0, atol=1.0e-15):
        raise RuntimeError("Frozen P2 d=5 A is not symmetric")
    if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1.0e-15):
        raise RuntimeError("Frozen P2 d=5 covariance is not symmetric")
    A_eigenvalues = np.linalg.eigvalsh(objective.A)
    C_eigenvalues = np.linalg.eigvalsh(covariance)
    if min(A_eigenvalues) <= 0.0 or min(C_eigenvalues) <= 0.0:
        raise RuntimeError("Frozen P2 d=5 A and C must be positive definite")
    commutator_norm = float(
        np.linalg.norm(objective.A @ covariance - covariance @ objective.A, ord="fro")
    )
    if not np.isclose(
        commutator_norm,
        float(config["noise"]["commutator_frobenius_norm"]),
        rtol=0.0,
        atol=1.0e-14,
    ):
        raise RuntimeError("Frozen P2 d=5 commutator norm changed")
    rank_one = float(config["objective"]["alpha"]) * np.outer(u, u)
    mu = float(np.linalg.eigvalsh(objective.A - rank_one)[0])
    L = float(np.linalg.eigvalsh(objective.A + rank_one)[-1])
    bounds = config["objective"]["global_hessian_bounds"]
    if not np.allclose([mu, L], [bounds["mu"], bounds["L"]], rtol=0.0, atol=1.0e-14):
        raise RuntimeError("Frozen P2 d=5 Hessian bounds changed")
    lyapunov_residual = 0.0
    decomposition_residuals: dict[int, float] = {}
    for H in (2, 4):
        targets = vector_theory_targets(objective, covariance, H)
        configured = config["theory"]["by_H"][H]
        checks = (
            (targets.S_C, config["theory"]["S_C"], "S_C"),
            (targets.B10, config["theory"]["B10"], "B10"),
            (targets.B20, configured["B20"], f"H={H} B20"),
            (targets.B20_local, configured["B20_local"], f"H={H} B20_local"),
            (targets.B20_ctrl, configured["B20_ctrl"], f"H={H} B20_ctrl"),
        )
        for actual, expected, label in checks:
            if not np.allclose(actual, expected, rtol=0.0, atol=1.0e-14):
                raise RuntimeError(f"Frozen P2 d=5 theory mismatch for {label}")
        lyapunov_residual = float(
            np.linalg.norm(objective.A @ targets.S_C + targets.S_C @ objective.A - covariance)
        )
        decomposition_residuals[H] = float(
            np.linalg.norm(targets.B20_local + targets.B20_ctrl - targets.B20)
        )
    audit = audit_formal_run_matrix("d5")
    expected_audit = {
        "matrix_id": "p2-d5-controlled-validation",
        "target": "d5",
        "settings": 10,
        "chains": 80,
        "chains_per_setting": [8] * 10,
        "H_values": [2, 4],
        "N_values": [32, 48, 64, 96, 128],
        "seeds": list(range(1201, 1209)),
        "unique_run_ids": 80,
        "all_unique": True,
        "gamma_equals_inverse_N": True,
    }
    if audit != expected_audit:
        raise RuntimeError(f"P2 d=5 matrix differs from its frozen protocol: {audit}")
    uncertainty = config["per_setting_uncertainty"]
    from .formal_inference import student_t_critical

    critical = student_t_critical(0.99, 7)
    if not np.isclose(
        critical, uncertainty["simultaneous_t_critical"], rtol=0.0, atol=1.0e-15
    ):
        raise RuntimeError("Frozen P2 d=5 t critical changed")
    if (
        uncertainty["coordinates"] != 5
        or uncertainty["familywise_confidence_level"] != 0.95
        or uncertainty["simultaneous_coordinate_confidence_level"] != 0.99
        or config["bootstrap"]["repetitions"] != 5000
        or config["bootstrap"]["seed"] != 3901
        or config["bootstrap"]["simultaneous_quantiles"] != [0.005, 0.995]
        or config["gates"]["combined_pass_requires"] != ["V0", "V1", "V2", "V5"]
    ):
        raise RuntimeError("Frozen P2 d=5 inference protocol changed")
    required_fragments = (
        "d=5",
        "t_(7,0.995) = 3.4994832973504924",
        "5,000 bootstrap replicates",
        "V0 requires",
        "V5 requires exactly ten settings and 80 chains",
        str(config["artifact_namespace"]) + "/",
    )
    protocol_text = P2_D5_PROTOCOL_PATH.read_text(encoding="utf-8")
    missing = [item for item in required_fragments if item not in protocol_text]
    if missing:
        raise RuntimeError(f"Frozen P2 d=5 protocol document is incomplete: {missing}")
    preview = _initial_manifest(
        "d5",
        config,
        {
            "source_commit": "PREVIEW",
            "source_dirty_at_run_start": False,
            "environment": {},
            "config_path": str(P2_D5_CONFIG_PATH.relative_to(REPO_ROOT)),
            "config_sha256": hashlib.sha256(P2_D5_CONFIG_PATH.read_bytes()).hexdigest(),
            "protocol_path": str(P2_D5_PROTOCOL_PATH.relative_to(REPO_ROOT)),
            "protocol_sha256": hashlib.sha256(P2_D5_PROTOCOL_PATH.read_bytes()).hexdigest(),
            "seeds": list(range(1201, 1209)),
            "bootstrap_seed": 3901,
            "bootstrap_repetitions": 5000,
            "run_matrix": audit,
            "expected_chain_count": 80,
        },
        [],
        [],
    )
    audit_d5_manifest(preview)
    return {
        "status": "PASS",
        "workstream": "p2",
        "phase": "d5_formal_pipeline_check_only",
        "matrix": audit,
        "A_eigenvalues": A_eigenvalues.tolist(),
        "C_eigenvalues": C_eigenvalues.tolist(),
        "commutator_frobenius_norm": commutator_norm,
        "u": u.tolist(),
        "mu": mu,
        "L": L,
        "lyapunov_residual": lyapunov_residual,
        "decomposition_residuals": decomposition_residuals,
        "simultaneous_t_critical": critical,
        "config_sha256": hashlib.sha256(P2_D5_CONFIG_PATH.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(P2_D5_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "manifest_audit": "PASS",
        "scientific_execution": "NOT_RUN",
    }


def formal_protocol_dimensions(
    spec: FormalRunSpec, config: dict[str, Any]
) -> dict[str, int]:
    protocol = config["protocol"]
    mixing_scale = math.ceil(
        1.0 / (float(protocol["mixing_mu"]) * spec.H * spec.gamma)
    )
    return {
        "mixing_scale": mixing_scale,
        "burn_in_rounds": int(protocol["burn_in_multiples"]) * mixing_scale,
        "batch_length": int(protocol["batch_length_multiples"]) * mixing_scale,
        "min_batches": int(protocol["min_batches"]),
        "max_batches": int(protocol["max_batches"]),
        "extension_batches": int(protocol["extension_batches"]),
    }


def _setting_groups(runs: Sequence[FormalRunSpec]) -> list[list[FormalRunSpec]]:
    groups: dict[tuple[int, int, float], list[FormalRunSpec]] = {}
    for item in runs:
        groups.setdefault(item.setting_key, []).append(item)
    return list(groups.values())


def _setting_diagnostics(
    direct_batches: np.ndarray,
    balance_batches: np.ndarray,
    *,
    gamma: float,
    N: int,
    B10: np.ndarray,
    B20: np.ndarray,
    finite_flags: np.ndarray,
    max_control_sum: np.ndarray,
    config: dict[str, Any],
) -> dict[str, Any]:
    chain_direct = np.mean(direct_batches, axis=0)
    chain_balance = np.mean(balance_batches, axis=0)
    chain_C = normalize_vector_bias(
        chain_balance, gamma=gamma, N=N, B10=B10
    )
    precision = evaluate_vector_precision(
        chain_C,
        B20,
        confidence_level=float(
            config["per_setting_uncertainty"][
                "simultaneous_coordinate_confidence_level"
            ]
        ),
        absolute=float(config["precision_stopping"]["absolute_half_width"]),
        relative=float(config["precision_stopping"]["relative_half_width"]),
    )
    chains, d = chain_balance.shape
    stationarity_flags = np.zeros((chains, d), dtype=bool)
    agreement_flags = np.zeros((chains, d), dtype=bool)
    for chain in range(chains):
        for coordinate in range(d):
            stationarity_flags[chain, coordinate] = stationarity_check(
                balance_batches[:, chain, coordinate],
                z=float(config["protocol"]["stationarity_z"]),
            ).passed
            agreement_flags[chain, coordinate] = estimator_agreement(
                chain_direct[chain, coordinate],
                chain_balance[chain, coordinate],
                standard_error(direct_batches[:, chain, coordinate]),
                standard_error(balance_batches[:, chain, coordinate]),
                z=float(config["protocol"]["estimator_agreement_z"]),
            )
    required = int(config["protocol"]["stationarity_min_chains"])
    stationarity_coordinate_pass = np.sum(stationarity_flags, axis=0) >= required
    finite_pass = bool(np.all(finite_flags))
    control_pass = bool(
        np.max(max_control_sum)
        <= float(config["protocol"]["max_abs_control_sum"])
    )
    return {
        "chain_direct": chain_direct,
        "chain_balance": chain_balance,
        "chain_C_balance": chain_C,
        "precision": precision,
        "stationarity_flags": stationarity_flags,
        "stationarity_coordinate_pass": stationarity_coordinate_pass,
        "stationarity_pass": bool(np.all(stationarity_coordinate_pass)),
        "agreement_flags": agreement_flags,
        "finite_pass": finite_pass,
        "control_pass": control_pass,
        "hard_validity_pass": finite_pass and control_pass,
        "validity_pass": finite_pass
        and control_pass
        and bool(np.all(stationarity_coordinate_pass)),
    }


def simulate_formal_setting(
    specs: Sequence[FormalRunSpec],
    config: dict[str, Any],
    *,
    run_start_provenance: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run one frozen eight-chain setting through the existing vector kernel."""

    specs = list(specs)
    if len(specs) != 8 or any(item.setting_key != specs[0].setting_key for item in specs):
        raise ValueError("A formal setting must contain exactly eight matching chains")
    spec = specs[0]
    objective = objective_from_formal_config(config)
    covariance = covariance_from_formal_config(config)
    targets = vector_theory_targets(objective, covariance, spec.H)
    dimensions = formal_protocol_dimensions(spec, config)
    x = np.stack([item.x0 for item in specs])
    xi = np.zeros((len(specs), spec.N, spec.d), dtype=np.float64)
    rngs = [np.random.default_rng(item.seed) for item in specs]
    finite_flags = np.ones(len(specs), dtype=bool)
    max_control_sum = np.zeros(len(specs), dtype=np.float64)

    remaining = dimensions["burn_in_rounds"]
    while remaining:
        rounds = min(dimensions["batch_length"], remaining)
        x, xi, stats = _advance_block(
            x,
            xi,
            rngs,
            rounds=rounds,
            gamma=spec.gamma,
            H=spec.H,
            N=spec.N,
            objective=objective,
            covariance=covariance,
            collect=False,
        )
        finite_flags &= stats["finite"].astype(bool)
        max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
        remaining -= rounds
        if not np.all(finite_flags):
            raise RuntimeError(f"Formal setting {spec.setting_id} became non-finite in burn-in")

    direct_batches: list[np.ndarray] = []
    balance_batches: list[np.ndarray] = []
    batch_rows: list[dict[str, Any]] = []
    target_batches = dimensions["min_batches"]
    diagnostics: dict[str, Any] | None = None
    stopping_reason = ""
    while len(direct_batches) < dimensions["max_batches"]:
        while len(direct_batches) < target_batches:
            batch_index = len(direct_batches)
            x, xi, stats = _advance_block(
                x,
                xi,
                rngs,
                rounds=dimensions["batch_length"],
                gamma=spec.gamma,
                H=spec.H,
                N=spec.N,
                objective=objective,
                covariance=covariance,
                collect=True,
            )
            direct_batches.append(stats["direct"].copy())
            balance_batches.append(stats["balance"].copy())
            finite_flags &= stats["finite"].astype(bool)
            max_control_sum = np.maximum(max_control_sum, stats["max_control_sum"])
            for estimator, values in (
                ("direct_sample_mean", stats["direct"]),
                ("stationary_mean_balance", stats["balance"]),
            ):
                normalized = normalize_vector_bias(
                    values, gamma=spec.gamma, N=spec.N, B10=targets.B10
                )
                for chain, item in enumerate(specs):
                    for coordinate in range(spec.d):
                        batch_rows.append(
                            {
                                "study": "p2_multidimensional_validation",
                                "phase": "formal",
                                "matrix_id": spec.matrix_id,
                                "setting_id": item.setting_id,
                                "run_id": item.run_id,
                                "seed": item.seed,
                                "d": item.d,
                                "coordinate": coordinate,
                                "H": item.H,
                                "N": item.N,
                                "gamma": item.gamma,
                                "delta": item.delta,
                                "estimator": estimator,
                                "batch_index": batch_index,
                                "b_component": float(values[chain, coordinate]),
                                "B10_component": float(targets.B10[coordinate]),
                                "C_component": float(normalized[chain, coordinate]),
                                "B20_component": float(targets.B20[coordinate]),
                                "normalized_error_component": float(
                                    normalized[chain, coordinate]
                                    - targets.B20[coordinate]
                                ),
                            }
                        )
            if not np.all(finite_flags):
                break

        direct_array = np.stack(direct_batches)
        balance_array = np.stack(balance_batches)
        diagnostics = _setting_diagnostics(
            direct_array,
            balance_array,
            gamma=spec.gamma,
            N=spec.N,
            B10=targets.B10,
            B20=targets.B20,
            finite_flags=finite_flags,
            max_control_sum=max_control_sum,
            config=config,
        )
        if not diagnostics["hard_validity_pass"]:
            stopping_reason = "VALIDITY_FAILED"
            break
        if diagnostics["stationarity_pass"] and diagnostics["precision"]["joint_pass"]:
            stopping_reason = "PRECISION_REACHED"
            break
        if target_batches >= dimensions["max_batches"]:
            stopping_reason = (
                "MAX_BATCHES_REACHED"
                if diagnostics["stationarity_pass"]
                else "MAX_BATCHES_REACHED_STATIONARITY_FAILED"
            )
            break
        target_batches = min(
            dimensions["max_batches"],
            target_batches + dimensions["extension_batches"],
        )

    if diagnostics is None:
        raise RuntimeError("Formal setting produced no diagnostic object")
    batches_used = len(direct_batches)
    for row in batch_rows:
        row.update(
            {
                "batches_used": batches_used,
                "stopping_reason": stopping_reason,
                "validity_pass": bool(diagnostics["validity_pass"]),
            }
        )

    run_rows: list[dict[str, Any]] = []
    provenance_fields = {
        "source_commit": run_start_provenance["source_commit"],
        "source_dirty_at_run_start": run_start_provenance[
            "source_dirty_at_run_start"
        ],
        "config_sha256": run_start_provenance["config_sha256"],
    }
    estimator_arrays = {
        "direct_sample_mean": diagnostics["chain_direct"],
        "stationary_mean_balance": diagnostics["chain_balance"],
    }
    for estimator, values in estimator_arrays.items():
        normalized = normalize_vector_bias(
            values, gamma=spec.gamma, N=spec.N, B10=targets.B10
        )
        for chain, item in enumerate(specs):
            for coordinate in range(spec.d):
                run_rows.append(
                    {
                        "study": "p2_multidimensional_validation",
                        "phase": "formal",
                        "matrix_id": spec.matrix_id,
                        "setting_id": item.setting_id,
                        "run_id": item.run_id,
                        "seed": item.seed,
                        "d": item.d,
                        "coordinate": coordinate,
                        "H": item.H,
                        "N": item.N,
                        "gamma": item.gamma,
                        "delta": item.delta,
                        "estimator": estimator,
                        "b_component": float(values[chain, coordinate]),
                        "B10_component": float(targets.B10[coordinate]),
                        "C_component": float(normalized[chain, coordinate]),
                        "B20_component": float(targets.B20[coordinate]),
                        "normalized_error_component": float(
                            normalized[chain, coordinate] - targets.B20[coordinate]
                        ),
                        "batches_used": batches_used,
                        "stopping_reason": stopping_reason,
                        "validity_pass": bool(diagnostics["validity_pass"]),
                        "finite_state_pass": bool(finite_flags[chain]),
                        "zero_sum_control_error": float(max_control_sum[chain]),
                        "zero_sum_control_pass": bool(diagnostics["control_pass"]),
                        "stationarity_pass": bool(
                            diagnostics["stationarity_flags"][chain, coordinate]
                        ),
                        "direct_balance_agreement_pass": bool(
                            diagnostics["agreement_flags"][chain, coordinate]
                        ),
                        "mixing_scale": dimensions["mixing_scale"],
                        "burn_in_rounds": dimensions["burn_in_rounds"],
                        "batch_length": dimensions["batch_length"],
                        **provenance_fields,
                    }
                )
    return run_rows, batch_rows


def _capture_formal_provenance(
    target: str, runs: Sequence[FormalRunSpec], config: dict[str, Any]
) -> dict[str, Any]:
    environment = environment_manifest()
    audit = audit_formal_run_matrix(target, runs)
    return {
        "schema_version": 1,
        "capture_point": "before_any_p2_formal_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "formal",
        "matrix_id": str(config["matrix_identifier"]),
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "environment": environment,
        "config_path": str(formal_config_path(target).relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(
            formal_config_path(target).read_bytes()
        ).hexdigest(),
        "protocol_path": str(formal_protocol_path(target).relative_to(REPO_ROOT)),
        "protocol_sha256": hashlib.sha256(
            formal_protocol_path(target).read_bytes()
        ).hexdigest(),
        "seeds": sorted({item.seed for item in runs}),
        "bootstrap_seed": int(config["bootstrap"]["seed"]),
        "bootstrap_repetitions": int(config["bootstrap"]["repetitions"]),
        "run_matrix": audit,
        "expected_chain_count": len(runs),
        "planned_coordinate_run_rows": len(runs) * 2 * int(config["objective"]["d"]),
        "artifact_namespace": str(config["artifact_namespace"]),
    }


def validate_formal_output_root(target_root: Path, expected_root: Path) -> None:
    resolved = target_root.resolve()
    expected = expected_root.resolve()
    parts = set(resolved.parts)
    if "p0_scaffold_bias" in parts or "p1_matched_fedavg" in parts:
        raise RuntimeError("P2 formal writes cannot target a P0 or P1 namespace")
    if resolved != expected:
        raise RuntimeError("P2 formal writes require the frozen artifact namespace")


def _initial_manifest(
    target: str,
    config: dict[str, Any],
    provenance: dict[str, Any],
    run_rows: Sequence[dict[str, Any]],
    batch_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    if target == "d5":
        report = "p2_d5_controlled_validation_report.md"
        figures = [
            "p2_d5_H2_coefficient_convergence.png",
            "p2_d5_H4_coefficient_convergence.png",
        ]
    elif target == "primary":
        report = "p2_d2_coefficient_primary_report.md"
        figures = []
    else:
        report = "p2_d2_h4_small_step_report.md"
        figures = []
    observed_chain_count = len({str(row.get("run_id")) for row in run_rows})
    return {
        "schema_version": 1,
        "study": "p2_multidimensional_validation",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": provenance["source_commit"],
        "source_dirty_at_provenance_capture": provenance[
            "source_dirty_at_run_start"
        ],
        "source_dirty": provenance["source_dirty_at_run_start"],
        "environment": provenance["environment"],
        "config_path": provenance["config_path"],
        "config_sha256": provenance["config_sha256"],
        "protocol_path": provenance["protocol_path"],
        "protocol_sha256": provenance["protocol_sha256"],
        "formal_seed_group": provenance["seeds"],
        "bootstrap_seed": provenance["bootstrap_seed"],
        "bootstrap_repetitions": provenance["bootstrap_repetitions"],
        "objective": config["objective"],
        "covariance": config["noise"]["covariance"],
        "theory": config["theory"],
        "run_matrix": provenance["run_matrix"],
        "expected_chain_count": provenance["expected_chain_count"],
        "observed_chain_count": observed_chain_count,
        "observed_rows": {
            "run_summary": len(run_rows),
            "batch_summary": len(batch_rows),
        },
        "stopping_protocol": config["precision_stopping"],
        "uncertainty_protocol": config["per_setting_uncertainty"],
        "fit_model": config["extrapolation"],
        "artifact_namespace": config["artifact_namespace"],
        "artifact_filenames": list(config.get("artifact_filenames", [
            "run_summary.csv", "batch_summary.csv", "setting_summary.csv",
            "setting_diagnostics.csv", "fit_summary.csv",
            "bootstrap_intercepts.csv", "falsification_summary.csv", report,
            *figures, P2_FORMAL_MANIFEST, P2_RUN_START_PROVENANCE,
        ])),
        "gate_definitions": config.get("gates", {}),
        "gate_results": "NOT_ANALYZED",
        "combined_formal_pass": "NOT_ANALYZED",
        "interpretation_boundary": config["interpretation_boundary"],
        "derived_outputs": "NOT_BUILT",
    }


def audit_d5_manifest(manifest: dict[str, Any]) -> None:
    """Fail if a future d=5 manifest omits any preregistered evidence field."""

    required = {
        "source_commit", "source_dirty", "config_sha256", "protocol_sha256",
        "matrix_id", "objective", "covariance", "theory", "run_matrix",
        "expected_chain_count", "observed_chain_count", "uncertainty_protocol",
        "stopping_protocol", "fit_model", "bootstrap_seed",
        "bootstrap_repetitions", "gate_definitions", "gate_results",
        "combined_formal_pass",
        "interpretation_boundary", "artifact_namespace", "artifact_filenames",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise RuntimeError(f"P2 d=5 manifest contract lacks fields: {missing}")
    if manifest["matrix_id"] != "p2-d5-controlled-validation":
        raise RuntimeError("P2 d=5 manifest matrix identity changed")
    if manifest["source_dirty"] is not False:
        raise RuntimeError("P2 d=5 manifest must record source_dirty=false")
    objective = manifest["objective"]
    for field in ("d", "A", "u", "alpha", "global_hessian_bounds"):
        if field not in objective:
            raise RuntimeError(f"P2 d=5 manifest objective lacks {field}")
    theory = manifest["theory"]
    for field in ("S_C", "B10", "by_H"):
        if field not in theory:
            raise RuntimeError(f"P2 d=5 manifest theory lacks {field}")
    for H in (2, 4):
        by_H = theory["by_H"]
        values = by_H[H] if H in by_H else by_H[str(H)]
        for field in ("B20", "B20_local", "B20_ctrl"):
            if field not in values:
                raise RuntimeError(f"P2 d=5 manifest H={H} theory lacks {field}")
    filenames = set(manifest["artifact_filenames"])
    expected_files = set(load_formal_config("d5")["artifact_filenames"])
    if filenames != expected_files:
        raise RuntimeError("P2 d=5 manifest artifact inventory is incomplete")
    matrix = manifest["run_matrix"]
    if matrix.get("settings") != 10 or matrix.get("chains") != 80:
        raise RuntimeError("P2 d=5 manifest lacks the exact frozen matrix")
    uncertainty = manifest["uncertainty_protocol"]
    if (
        uncertainty.get("coordinates") != 5
        or uncertainty.get("simultaneous_t_critical") != 3.4994832973504924
    ):
        raise RuntimeError("P2 d=5 manifest lacks five-coordinate uncertainty")
    gates = manifest["gate_definitions"]
    if not {"V0", "V1", "V2", "V3", "V4", "V5"} <= set(gates):
        raise RuntimeError("P2 d=5 manifest lacks V0-V5 definitions")
    boundary = manifest["interpretation_boundary"]
    if not {"classification", "permitted_conclusion", "excluded_claims"} <= set(boundary):
        raise RuntimeError("P2 d=5 manifest interpretation boundary is incomplete")


def run_formal_matrix(target: str) -> dict[str, Any]:
    """Build a complete frozen result in staging and install it transactionally."""

    if target == "d5":
        check_d5_protocol()
    else:
        check_formal_protocol()
    config = load_formal_config(target)
    runs = build_formal_run_matrix(target, config)
    expected_root = formal_artifact_root(target, config)
    validate_formal_output_root(expected_root, expected_root)
    provenance = _capture_formal_provenance(target, runs, config)
    if (
        provenance["source_dirty_at_run_start"] is not False
        or provenance["source_commit"] == "NO_COMMIT"
    ):
        raise RuntimeError(
            "Formal P2 runs require a clean committed source tree at run start"
        )
    require_complete_existing_output(
        expected_root,
        required_files=(*P2_RAW_RESULT_FILES, P2_RUN_START_PROVENANCE),
    )
    staged_root = create_staging_directory(expected_root)
    try:
        write_json(provenance, staged_root / P2_RUN_START_PROVENANCE)
        all_run_rows: list[dict[str, Any]] = []
        all_batch_rows: list[dict[str, Any]] = []
        groups = _setting_groups(runs)
        for index, setting in enumerate(groups, start=1):
            item = setting[0]
            print(
                f"[p2-formal] setting {index}/{len(groups)}: "
                f"H={item.H} N={item.N} gamma={item.gamma:.10g}",
                flush=True,
            )
            run_rows, batch_rows = simulate_formal_setting(
                setting, config, run_start_provenance=provenance
            )
            all_run_rows.extend(run_rows)
            all_batch_rows.extend(batch_rows)
            write_csv(all_run_rows, staged_root / "run_summary.csv")
            write_csv(all_batch_rows, staged_root / "batch_summary.csv")
        manifest = _initial_manifest(
            target, config, provenance, all_run_rows, all_batch_rows
        )
        if target == "d5":
            audit_d5_manifest(manifest)
        write_json(manifest, staged_root / P2_FORMAL_MANIFEST)
        from .formal_analysis import (
            analyze_formal_saved,
            build_formal_report_and_plots,
        )

        primary_root = formal_artifact_root("primary") if target == "h4-small-step" else None
        analysis = analyze_formal_saved(
            target,
            staged_root,
            primary_output_root=primary_root,
        )
        report_outputs = build_formal_report_and_plots(target, staged_root)
        overwrite_audit = validate_controlled_overwrite(
            staged_root,
            expected_root,
            raw_result_files=P2_RAW_RESULT_FILES,
            provenance_filename=P2_RUN_START_PROVENANCE,
            identity_fields=("config_sha256", "protocol_sha256", "matrix_id"),
            excluded_row_fields=P2_ROW_PROVENANCE_FIELDS,
        )
        replace_output_directory(staged_root, expected_root)
    except BaseException:
        if staged_root.exists():
            shutil.rmtree(staged_root)
        raise
    outputs = {
        "target": target,
        "output_root": expected_root,
        "run_rows": all_run_rows,
        "batch_rows": all_batch_rows,
        "manifest": expected_root / P2_FORMAL_MANIFEST,
        "analysis": analysis,
        "report": report_outputs["report"],
        "figures": report_outputs["figures"],
        "overwrite_audit": overwrite_audit,
    }
    return rebase_staged_paths(outputs, staged_root, expected_root)
