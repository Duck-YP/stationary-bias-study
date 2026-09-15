"""Frozen d=2 coordinate-rotation orchestration for the P2 vector kernel."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from ...core.artifacts import (
    create_staging_directory,
    replace_output_directory,
    require_complete_existing_output,
    stage_existing_directory,
    validate_controlled_overwrite,
)
from ...core.io import (
    REPO_ROOT,
    environment_manifest,
    gamma_token,
    load_yaml,
    write_csv,
    write_json,
)
from .algorithm import scaffold_round_many_vector
from .noise import generate_vector_noise_block
from .objective import RankOneVectorObjective
from .theory import vector_theory_targets


P2_ROTATION_ROOT = REPO_ROOT / "workstreams" / "p2_multidimensional_validation"
P2_ROTATION_CONFIG_PATH = P2_ROTATION_ROOT / "configs" / "d2_rotation_invariance.yaml"
P2_ROTATION_PROTOCOL_PATH = P2_ROTATION_ROOT / "rotation_protocol.md"
P2_ROTATION_PROVENANCE = "run_start_provenance.json"
P2_ROTATION_PAIR_SUMMARY = "pair_summary.csv"
P2_ROTATION_RESIDUAL_SUMMARY = "rotation_residual_summary.csv"
P2_ROTATION_THEORY_SUMMARY = "theory_rotation_summary.csv"
P2_ROTATION_MANIFEST = "rotation_manifest.json"
P2_ROTATION_REPORT = "p2_d2_rotation_report.md"
P2_ROTATION_RAW_FILES = (
    P2_ROTATION_PAIR_SUMMARY,
    P2_ROTATION_RESIDUAL_SUMMARY,
    P2_ROTATION_THEORY_SUMMARY,
)


@dataclass(frozen=True)
class RotationPairSpec:
    matrix_id: str
    seed: int
    d: int
    H: int
    N: int
    gamma: float
    communication_rounds: int
    x0: np.ndarray

    @property
    def pair_id(self) -> str:
        return (
            f"p2__phase-rotation__matrix-{self.matrix_id}__H{self.H}__N{self.N}"
            f"__g{gamma_token(self.gamma)}__seed{self.seed}"
        )


def load_rotation_config() -> dict[str, Any]:
    return load_yaml(P2_ROTATION_CONFIG_PATH)


def rotation_artifact_root(config: dict[str, Any] | None = None) -> Path:
    config = config or load_rotation_config()
    return REPO_ROOT / str(config["artifact_contract"]["namespace"])


def rotation_matrix(config: dict[str, Any]) -> np.ndarray:
    return np.asarray(config["coordinate_transform"]["Q"], dtype=np.float64)


def rotate_last_axis(values: np.ndarray, Q: np.ndarray) -> np.ndarray:
    """Apply the column-vector map ``Q v`` to last-axis NumPy vectors."""

    array = np.asarray(values, dtype=np.float64)
    matrix = np.asarray(Q, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Q must be square")
    if array.ndim == 0 or array.shape[-1] != matrix.shape[0]:
        raise ValueError("values must store coordinates on the last axis")
    return array @ matrix.T


def objectives_from_rotation_config(
    config: dict[str, Any],
) -> tuple[RankOneVectorObjective, RankOneVectorObjective]:
    original = config["original_system"]
    rotated = config["rotated_system"]
    alpha = float(original["alpha"])
    return (
        RankOneVectorObjective(
            np.asarray(original["A"], dtype=np.float64),
            np.asarray(original["u"], dtype=np.float64),
            alpha,
        ),
        RankOneVectorObjective(
            np.asarray(rotated["A_rot"], dtype=np.float64),
            np.asarray(rotated["u_rot"], dtype=np.float64),
            alpha,
        ),
    )


def build_rotation_pair_matrix(
    config: dict[str, Any] | None = None,
) -> list[RotationPairSpec]:
    config = config or load_rotation_config()
    matrix = config["paired_matrix"]
    x0 = np.asarray(config["initialization"]["x0"], dtype=np.float64)
    specs: list[RotationPairSpec] = []
    for H in matrix["H_values"]:
        for setting in matrix["settings"]:
            denominator = int(setting["gamma_denominator"])
            for seed in matrix["seeds"]:
                specs.append(
                    RotationPairSpec(
                        matrix_id=str(config["matrix_identifier"]),
                        seed=int(seed),
                        d=int(matrix["dimension"]),
                        H=int(H),
                        N=int(setting["N"]),
                        gamma=int(setting["gamma_numerator"]) / denominator,
                        communication_rounds=int(matrix["communication_rounds"]),
                        x0=x0.copy(),
                    )
                )
    return specs


def audit_rotation_pair_matrix(
    specs: Sequence[RotationPairSpec] | None = None,
) -> dict[str, Any]:
    items = list(specs or build_rotation_pair_matrix())
    pair_ids = [item.pair_id for item in items]
    settings = sorted({(item.N, item.gamma) for item in items})
    return {
        "matrix_id": items[0].matrix_id if items else "",
        "pair_count": len(items),
        "unique_pair_ids": len(set(pair_ids)),
        "all_unique": len(pair_ids) == len(set(pair_ids)),
        "H_values": sorted({item.H for item in items}),
        "settings": [
            {"N": N, "gamma": gamma} for N, gamma in settings
        ],
        "seeds": sorted({item.seed for item in items}),
        "communication_rounds": sorted(
            {item.communication_rounds for item in items}
        ),
        "gamma_equals_inverse_N": all(
            item.gamma == 1.0 / item.N for item in items
        ),
    }


def theory_rotation_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    Q = rotation_matrix(config)
    original = config["original_system"]
    rotated = config["rotated_system"]
    theory = config["theory"]
    gates = config["theory_equivariance_gates"]
    A = np.asarray(original["A"], dtype=np.float64)
    C = np.asarray(original["C"], dtype=np.float64)
    u = np.asarray(original["u"], dtype=np.float64)
    A_rot = np.asarray(rotated["A_rot"], dtype=np.float64)
    C_rot = np.asarray(rotated["C_rot"], dtype=np.float64)
    u_rot = np.asarray(rotated["u_rot"], dtype=np.float64)
    S = np.asarray(theory["original"]["S_C"], dtype=np.float64)
    S_rot = np.asarray(theory["rotated"]["S_rot"], dtype=np.float64)
    B10 = np.asarray(theory["original"]["B10"], dtype=np.float64)
    B10_rot = np.asarray(theory["rotated"]["B10_rot"], dtype=np.float64)
    definitions = [
        ("R0", None, np.linalg.norm(Q.T @ Q - np.eye(Q.shape[0]), ord="fro")),
        ("R1", None, np.linalg.norm(A_rot - Q @ A @ Q.T, ord="fro")),
        ("R2", None, np.linalg.norm(C_rot - Q @ C @ Q.T, ord="fro")),
        ("R3", None, np.linalg.norm(u_rot - Q @ u)),
        ("R4", None, np.linalg.norm(S_rot - Q @ S @ Q.T, ord="fro")),
        ("R5", None, np.linalg.norm(B10_rot - Q @ B10)),
    ]
    rows: list[dict[str, Any]] = []
    for gate, H, residual in definitions:
        threshold = float(gates[gate]["tolerance"])
        rows.append(
            {
                "gate": gate,
                "H_if_applicable": H,
                "residual": float(residual),
                "threshold": threshold,
                "passed": bool(residual <= threshold),
            }
        )
    for H in (2, 4):
        B20 = np.asarray(theory["original"]["by_H"][H]["B20"], dtype=np.float64)
        B20_rot = np.asarray(
            theory["rotated"]["by_H"][H]["B20_rot"], dtype=np.float64
        )
        residual = float(np.linalg.norm(B20_rot - Q @ B20))
        threshold = float(gates["R6"]["tolerance"])
        rows.append(
            {
                "gate": "R6",
                "H_if_applicable": H,
                "residual": residual,
                "threshold": threshold,
                "passed": bool(residual <= threshold),
            }
        )
    return rows


def _assert_exact_frozen_config(config: dict[str, Any]) -> None:
    expected = {
        "Q": [[0.8660254037844386, -0.5], [0.5, 0.8660254037844386]],
        "A": [[1.2, 0.2], [0.2, 1.0]],
        "C": [[1.0, 0.2], [0.2, 0.7]],
        "u": [0.7071067811865475, 0.7071067811865475],
        "alpha": 0.25,
        "A_rot": [
            [0.976794919243112, 0.186602540378444],
            [0.186602540378444, 1.223205080756888],
        ],
        "C_rot": [
            [0.751794919243112, 0.229903810567666],
            [0.229903810567666, 0.948205080756888],
        ],
        "u_rot": [0.258819045102521, 0.965925826289068],
        "x0": [0.2, -0.1],
        "x0_rot": [0.223205080756888, 0.013397459621556],
        "S_C": [
            [0.413009404388715, 0.021943573667712],
            [0.021943573667712, 0.345611285266458],
        ],
        "S_rot": [
            [0.377156182362097, 0.040156028497438],
            [0.040156028497438, 0.381464507293076],
        ],
        "B10": [-0.024459428167733, -0.030574285209666],
        "B10_rot": [-0.005895343550464, -0.038707821777988],
        "B20_H2": [-0.048004016395207, -0.060005020494009],
        "B20_rot_H2": [-0.011570187434929, -0.075967880300021],
        "B20_H4": [-0.152012718584823, -0.190015898231029],
        "B20_rot_H4": [-0.036638926877277, -0.240564954283401],
    }
    observed = {
        "Q": config["coordinate_transform"]["Q"],
        "A": config["original_system"]["A"],
        "C": config["original_system"]["C"],
        "u": config["original_system"]["u"],
        "alpha": config["original_system"]["alpha"],
        "A_rot": config["rotated_system"]["A_rot"],
        "C_rot": config["rotated_system"]["C_rot"],
        "u_rot": config["rotated_system"]["u_rot"],
        "x0": config["initialization"]["x0"],
        "x0_rot": config["initialization"]["x0_rot"],
        "S_C": config["theory"]["original"]["S_C"],
        "S_rot": config["theory"]["rotated"]["S_rot"],
        "B10": config["theory"]["original"]["B10"],
        "B10_rot": config["theory"]["rotated"]["B10_rot"],
        "B20_H2": config["theory"]["original"]["by_H"][2]["B20"],
        "B20_rot_H2": config["theory"]["rotated"]["by_H"][2]["B20_rot"],
        "B20_H4": config["theory"]["original"]["by_H"][4]["B20"],
        "B20_rot_H4": config["theory"]["rotated"]["by_H"][4]["B20_rot"],
    }
    for key, value in expected.items():
        if observed[key] != value:
            raise RuntimeError(f"Frozen rotation value changed: {key}")
    matrix = config["paired_matrix"]
    if (
        config["protocol_status"] != "frozen_not_executed"
        or config["matrix_identifier"] != "p2-d2-rotation-invariance"
        or matrix["dimension"] != 2
        or matrix["H_values"] != [2, 4]
        or matrix["settings"]
        != [
            {"N": 16, "gamma_numerator": 1, "gamma_denominator": 16},
            {"N": 64, "gamma_numerator": 1, "gamma_denominator": 64},
        ]
        or matrix["seeds"] != [1101, 1102, 1103, 1104]
        or type(matrix["communication_rounds"]) is not int
        or matrix["communication_rounds"] != 200
        or matrix["paired_run_count"] != 16
    ):
        raise RuntimeError("Frozen rotation matrix changed")
    if (
        config["noise_coupling"]["rotated_construction"]
        != "epsilon_rot = Q @ epsilon"
        or config["noise_coupling"]["independently_generate_from_C_rot"]
        != "forbidden"
        or config["noise_coupling"]["same_realization_across_each_pair"]
        != ["seed", "communication_round", "local_step", "client"]
        or config["pathwise_equivariance"]["primary_gate"]["tolerance"]
        != 1.0e-10
    ):
        raise RuntimeError("Frozen rotation coupling or pathwise gate changed")
    expected_tolerances = {
        "R0": 1.0e-14,
        "R1": 1.0e-13,
        "R2": 1.0e-13,
        "R3": 1.0e-13,
        "R4": 1.0e-12,
        "R5": 1.0e-12,
        "R6": 1.0e-12,
    }
    observed_tolerances = {
        gate: float(item["tolerance"])
        for gate, item in config["theory_equivariance_gates"].items()
        if gate in expected_tolerances
    }
    if observed_tolerances != expected_tolerances:
        raise RuntimeError("Frozen rotation theory tolerances changed")
    if (
        config["artifact_contract"]["namespace"]
        != "workstreams/p2_multidimensional_validation/artifacts/formal/p2-d2-rotation-invariance"
    ):
        raise RuntimeError("Frozen rotation artifact namespace changed")
    if (
        config["interpretation_boundary"]["permitted_conclusion"]
        != "The implementation and theoretical coefficient are equivariant under the pre-registered 30-degree orthogonal coordinate transformation."
    ):
        raise RuntimeError("Frozen rotation interpretation boundary changed")


def check_rotation_protocol() -> dict[str, Any]:
    config = load_rotation_config()
    _assert_exact_frozen_config(config)
    specs = build_rotation_pair_matrix(config)
    audit = audit_rotation_pair_matrix(specs)
    expected_audit = {
        "matrix_id": "p2-d2-rotation-invariance",
        "pair_count": 16,
        "unique_pair_ids": 16,
        "all_unique": True,
        "H_values": [2, 4],
        "settings": [{"N": 16, "gamma": 1 / 16}, {"N": 64, "gamma": 1 / 64}],
        "seeds": [1101, 1102, 1103, 1104],
        "communication_rounds": [200],
        "gamma_equals_inverse_N": True,
    }
    if audit != expected_audit:
        raise RuntimeError(f"Frozen rotation matrix differs: {audit}")
    rows = theory_rotation_rows(config)
    failed = [row for row in rows if not row["passed"]]
    if failed:
        raise RuntimeError(f"Frozen rotation theory gates failed: {failed}")
    original_objective, rotated_objective = objectives_from_rotation_config(config)
    original_covariance = np.asarray(config["original_system"]["C"], dtype=np.float64)
    rotated_covariance = np.asarray(config["rotated_system"]["C_rot"], dtype=np.float64)
    for H in (2, 4):
        original_targets = vector_theory_targets(original_objective, original_covariance, H)
        rotated_targets = vector_theory_targets(rotated_objective, rotated_covariance, H)
        configured_original = config["theory"]["original"]
        configured_rotated = config["theory"]["rotated"]
        checks = (
            (original_targets.S_C, configured_original["S_C"], "S_C"),
            (original_targets.B10, configured_original["B10"], "B10"),
            (original_targets.B20, configured_original["by_H"][H]["B20"], f"B20 H={H}"),
            (rotated_targets.S_C, configured_rotated["S_rot"], "S_rot"),
            (rotated_targets.B10, configured_rotated["B10_rot"], "B10_rot"),
            (
                rotated_targets.B20,
                configured_rotated["by_H"][H]["B20_rot"],
                f"B20_rot H={H}",
            ),
        )
        for actual, expected, label in checks:
            if not np.allclose(actual, expected, rtol=0.0, atol=1.0e-14):
                raise RuntimeError(f"Frozen rotation theory target changed: {label}")
    Q = rotation_matrix(config)
    x0 = np.asarray(config["initialization"]["x0"], dtype=np.float64)
    x0_rot = np.asarray(config["initialization"]["x0_rot"], dtype=np.float64)
    if np.linalg.norm(x0_rot - rotate_last_axis(x0, Q)) > 1.0e-13:
        raise RuntimeError("Frozen rotated initialization is inconsistent")
    if not P2_ROTATION_PROTOCOL_PATH.is_file():
        raise RuntimeError("Missing frozen rotation protocol document")
    protocol = P2_ROTATION_PROTOCOL_PATH.read_text(encoding="utf-8")
    required_fragments = (
        "theta = pi / 6",
        "A_rot = [[0.976794919243112, 0.186602540378444]",
        "C_rot = [[0.751794919243112, 0.229903810567666]",
        "u_rot = [0.258819045102521",
        "grad f_rot(y) = Q grad f(Q.T y)",
        "epsilon_rot = Q epsilon",
        "The fixed pathwise horizon is `T=200` communication rounds per paired run.",
        "r_x    = max over t=1,...,200",
        "r_xi   = max over t=1,...,200 and clients c",
        "r_qbar = max over t=1,...,200 and local steps h",
        "`max(r_x, r_xi, r_qbar) <= 1e-10`",
        "seeds `1101`, `1102`, `1103`, and `1104`",
        "x0 = [0.2, -0.1]",
        "R0 = ||Q.T Q - I||_F                         <= 1e-14",
        "R6 = ||B20_rot(H) - Q B20(H)||_2             <= 1e-12",
        "artifacts/formal/p2-d2-rotation-invariance/",
        "permitted empirical and numerical sanity conclusion",
    )
    missing = [fragment for fragment in required_fragments if fragment not in protocol]
    if missing:
        raise RuntimeError(f"Frozen rotation protocol document disagrees: {missing}")
    return {
        "status": "PASS",
        "workstream": "p2",
        "phase": "rotation_pipeline_check_only",
        "protocol_status": config["protocol_status"],
        "communication_rounds": 200,
        "matrix": audit,
        "theory_gates": rows,
        "config_sha256": hashlib.sha256(P2_ROTATION_CONFIG_PATH.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(P2_ROTATION_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "scientific_execution": "NOT_RUN",
    }


def generate_paired_noise(
    spec: RotationPairSpec,
    config: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """Draw the original block once and rotate it without another RNG stream."""

    covariance = np.asarray(config["original_system"]["C"], dtype=np.float64)
    Q = rotation_matrix(config)
    rng = np.random.default_rng(spec.seed)
    original = generate_vector_noise_block(
        [rng],
        covariance,
        rounds=spec.communication_rounds,
        H=spec.H,
        N=spec.N,
    )[0]
    rotated = rotate_last_axis(original, Q)
    return original, rotated


def run_rotation_pair(
    spec: RotationPairSpec,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one pathwise-coupled pair through the shared vector SCAFFOLD kernel."""

    config = config or load_rotation_config()
    Q = rotation_matrix(config)
    original_objective, rotated_objective = objectives_from_rotation_config(config)
    original_noise, rotated_noise = generate_paired_noise(spec, config)
    x = spec.x0[None, :].copy()
    x_rot = rotate_last_axis(x, Q)
    xi = np.zeros((1, spec.N, spec.d), dtype=np.float64)
    xi_rot = np.zeros_like(xi)
    r_x = 0.0
    r_xi = 0.0
    r_qbar = 0.0
    for round_index in range(spec.communication_rounds):
        original = scaffold_round_many_vector(
            x,
            xi,
            gamma=spec.gamma,
            H=spec.H,
            objective=original_objective,
            epsilon_steps=original_noise[round_index][None, ...],
        )
        rotated = scaffold_round_many_vector(
            x_rot,
            xi_rot,
            gamma=spec.gamma,
            H=spec.H,
            objective=rotated_objective,
            epsilon_steps=rotated_noise[round_index][None, ...],
        )
        arrays = (
            original.x_new,
            original.xi_new,
            original.qbar,
            rotated.x_new,
            rotated.xi_new,
            rotated.qbar,
        )
        if not all(np.all(np.isfinite(array)) for array in arrays):
            raise RuntimeError(f"Rotation pair became non-finite: {spec.pair_id}")
        r_x = max(
            r_x,
            float(np.max(np.abs(rotated.x_new - rotate_last_axis(original.x_new, Q)))),
        )
        r_xi = max(
            r_xi,
            float(np.max(np.abs(rotated.xi_new - rotate_last_axis(original.xi_new, Q)))),
        )
        r_qbar = max(
            r_qbar,
            float(np.max(np.abs(rotated.qbar - rotate_last_axis(original.qbar, Q)))),
        )
        x, xi = original.x_new, original.xi_new
        x_rot, xi_rot = rotated.x_new, rotated.xi_new
    r_max = max(r_x, r_xi, r_qbar)
    tolerance = float(config["pathwise_equivariance"]["primary_gate"]["tolerance"])
    return {
        "study": "p2_multidimensional_validation",
        "phase": "rotation",
        "matrix_id": spec.matrix_id,
        "pair_id": spec.pair_id,
        "seed": spec.seed,
        "H": spec.H,
        "N": spec.N,
        "gamma": spec.gamma,
        "communication_rounds": spec.communication_rounds,
        "r_x": r_x,
        "r_xi": r_xi,
        "r_qbar": r_qbar,
        "r_max": r_max,
        "pathwise_pass": bool(r_max <= tolerance),
    }


def rotation_residual_rows(
    pair_rows: Sequence[dict[str, Any]], tolerance: float
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pair_rows:
        for metric in ("r_x", "r_xi", "r_qbar", "r_max"):
            residual = float(pair[metric])
            rows.append(
                {
                    "scope": "pair",
                    "pair_id": pair["pair_id"],
                    "metric": metric,
                    "residual": residual,
                    "threshold": tolerance,
                    "passed": bool(residual <= tolerance),
                }
            )
    for metric in ("r_x", "r_xi", "r_qbar", "r_max"):
        residual = max(float(pair[metric]) for pair in pair_rows)
        rows.append(
            {
                "scope": "global",
                "pair_id": "",
                "metric": metric,
                "residual": residual,
                "threshold": tolerance,
                "passed": bool(residual <= tolerance),
            }
        )
    return rows


def capture_rotation_provenance(
    specs: Sequence[RotationPairSpec], config: dict[str, Any]
) -> dict[str, Any]:
    environment = environment_manifest()
    return {
        "schema_version": 1,
        "capture_point": "before_any_p2_rotation_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "rotation",
        "matrix_id": config["matrix_identifier"],
        "source_commit": environment["git_commit"],
        "source_dirty_at_run_start": environment["git_dirty"],
        "environment": environment,
        "config_path": str(P2_ROTATION_CONFIG_PATH.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(P2_ROTATION_CONFIG_PATH.read_bytes()).hexdigest(),
        "protocol_path": str(P2_ROTATION_PROTOCOL_PATH.relative_to(REPO_ROOT)),
        "protocol_sha256": hashlib.sha256(P2_ROTATION_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "run_matrix": audit_rotation_pair_matrix(specs),
        "pairs": [
            {
                "pair_id": item.pair_id,
                "seed": item.seed,
                "H": item.H,
                "N": item.N,
                "gamma": item.gamma,
                "communication_rounds": item.communication_rounds,
            }
            for item in specs
        ],
        "artifact_namespace": config["artifact_contract"]["namespace"],
    }


def require_clean_committed_source(provenance: dict[str, Any]) -> None:
    if (
        provenance.get("source_dirty_at_run_start") is not False
        or provenance.get("source_commit") in (None, "", "NO_COMMIT")
    ):
        raise RuntimeError(
            "Formal P2 rotation runs require a clean committed source tree at run start"
        )


def validate_rotation_output_root(target_root: Path, expected_root: Path) -> None:
    target = target_root.resolve()
    expected = expected_root.resolve()
    forbidden = {
        "p0_scaffold_bias",
        "p1_matched_fedavg",
        "p2-d2-coefficient-primary",
        "p2-d2-h4-small-step-confirmation",
    }
    if forbidden.intersection(target.parts):
        raise RuntimeError("Rotation writes cannot target prior P0/P1/P2 evidence")
    if target != expected:
        raise RuntimeError("Rotation writes require the selected isolated namespace")


def _rotation_manifest(
    provenance: dict[str, Any],
    pair_rows: Sequence[dict[str, Any]],
    theory_rows: Sequence[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    gate = config["pathwise_equivariance"]["primary_gate"]
    tolerance = float(gate["tolerance"])
    expected_pair_count = int(config["paired_matrix"]["paired_run_count"])
    expected_pair_ids = {item["pair_id"] for item in provenance["pairs"]}
    observed_pair_ids = {str(row["pair_id"]) for row in pair_rows}
    frozen_audit = audit_rotation_pair_matrix(build_rotation_pair_matrix(config))
    config_sha256 = hashlib.sha256(P2_ROTATION_CONFIG_PATH.read_bytes()).hexdigest()
    protocol_sha256 = hashlib.sha256(P2_ROTATION_PROTOCOL_PATH.read_bytes()).hexdigest()
    if (
        provenance["source_dirty_at_run_start"] is not False
        or not provenance["source_commit"]
        or not provenance["config_sha256"]
        or not provenance["protocol_sha256"]
    ):
        raise RuntimeError("Rotation manifest requires clean-source provenance")
    if (
        provenance["matrix_id"] != config["matrix_identifier"]
        or provenance["run_matrix"] != frozen_audit
        or provenance["config_sha256"] != config_sha256
        or provenance["protocol_sha256"] != protocol_sha256
        or len(pair_rows) != expected_pair_count
        or len(observed_pair_ids) != expected_pair_count
        or observed_pair_ids != expected_pair_ids
    ):
        raise RuntimeError("Rotation manifest requires the exact frozen 16-pair matrix")
    for row in pair_rows:
        expected_pass = float(row["r_max"]) <= tolerance
        if bool(row["pathwise_pass"]) != expected_pass:
            raise RuntimeError(
                "Rotation manifest pathwise result disagrees with the frozen tolerance"
            )
    pathwise_pass_count = sum(bool(row["pathwise_pass"]) for row in pair_rows)
    return {
        "schema_version": 1,
        "study": "p2_multidimensional_validation",
        "phase": "rotation",
        "matrix_id": provenance["matrix_id"],
        "source_commit": provenance["source_commit"],
        "source_dirty_at_provenance_capture": provenance[
            "source_dirty_at_run_start"
        ],
        "config_sha256": provenance["config_sha256"],
        "protocol_sha256": provenance["protocol_sha256"],
        "run_matrix": provenance["run_matrix"],
        "expected_pair_count": expected_pair_count,
        "observed_pair_count": len(pair_rows),
        "theory_gate_pass": bool(all(row["passed"] for row in theory_rows)),
        "pathwise_gate_pass": bool(all(row["pathwise_pass"] for row in pair_rows)),
        "pathwise_gate": {
            "residual": str(gate["quantity"]),
            "tolerance": tolerance,
            "scope": str(gate["scope"]),
            "required_pass_count": expected_pair_count,
            "observed_pass_count": pathwise_pass_count,
        },
        "artifact_namespace": provenance["artifact_namespace"],
        "artifact_filenames": [
            P2_ROTATION_PROVENANCE,
            P2_ROTATION_PAIR_SUMMARY,
            P2_ROTATION_RESIDUAL_SUMMARY,
            P2_ROTATION_THEORY_SUMMARY,
            P2_ROTATION_MANIFEST,
            P2_ROTATION_REPORT,
        ],
        "interpretation": "EMPIRICAL / NUMERICAL SANITY",
        "interpretation_boundary": config["interpretation_boundary"],
        "report": "NOT_BUILT",
    }


def write_rotation_raw_outputs(
    pair_rows: Sequence[dict[str, Any]],
    theory_rows: Sequence[dict[str, Any]],
    provenance: dict[str, Any],
    config: dict[str, Any],
    *,
    target_root: Path,
    expected_root: Path,
) -> Path:
    validate_rotation_output_root(target_root, expected_root)
    require_complete_existing_output(
        target_root,
        required_files=(*P2_ROTATION_RAW_FILES, P2_ROTATION_PROVENANCE),
    )
    staged = create_staging_directory(target_root)
    try:
        manifest = _rotation_manifest(provenance, pair_rows, theory_rows, config)
        tolerance = float(
            config["pathwise_equivariance"]["primary_gate"]["tolerance"]
        )
        write_json(provenance, staged / P2_ROTATION_PROVENANCE)
        write_csv(pair_rows, staged / P2_ROTATION_PAIR_SUMMARY)
        write_csv(
            rotation_residual_rows(pair_rows, tolerance),
            staged / P2_ROTATION_RESIDUAL_SUMMARY,
        )
        write_csv(theory_rows, staged / P2_ROTATION_THEORY_SUMMARY)
        write_json(manifest, staged / P2_ROTATION_MANIFEST)
        build_rotation_report_from_saved(staged)
        validate_controlled_overwrite(
            staged,
            target_root,
            raw_result_files=P2_ROTATION_RAW_FILES,
            provenance_filename=P2_ROTATION_PROVENANCE,
            identity_fields=("config_sha256", "protocol_sha256", "matrix_id"),
        )
        replace_output_directory(staged, target_root)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    return target_root


def run_rotation_matrix() -> dict[str, Any]:
    """Execute the frozen 16-pair matrix with formal write guards."""

    check_rotation_protocol()
    config = load_rotation_config()
    specs = build_rotation_pair_matrix(config)
    expected_root = rotation_artifact_root(config)
    validate_rotation_output_root(expected_root, expected_root)
    require_complete_existing_output(
        expected_root,
        required_files=(*P2_ROTATION_RAW_FILES, P2_ROTATION_PROVENANCE),
    )
    provenance = capture_rotation_provenance(specs, config)
    require_clean_committed_source(provenance)
    pair_rows = []
    for index, spec in enumerate(specs, start=1):
        print(
            f"[p2-rotation] pair {index}/{len(specs)}: "
            f"H={spec.H} N={spec.N} gamma={spec.gamma:.10g} seed={spec.seed}",
            flush=True,
        )
        pair_rows.append(run_rotation_pair(spec, config))
    theory_rows = theory_rotation_rows(config)
    output_root = write_rotation_raw_outputs(
        pair_rows,
        theory_rows,
        provenance,
        config,
        target_root=expected_root,
        expected_root=expected_root,
    )
    return {
        "output_root": output_root,
        "pair_rows": pair_rows,
        "theory_rows": theory_rows,
        "manifest": output_root / P2_ROTATION_MANIFEST,
    }


def build_rotation_report_from_saved(
    source_root: Path, *, output_path: Path | None = None
) -> Path:
    """Build the rotation report solely from saved scalar summaries."""

    provenance = json.loads((source_root / P2_ROTATION_PROVENANCE).read_text(encoding="utf-8"))
    pairs = pd.read_csv(source_root / P2_ROTATION_PAIR_SUMMARY)
    theory = pd.read_csv(source_root / P2_ROTATION_THEORY_SUMMARY)
    required_pair_columns = {
        "matrix_id",
        "pair_id",
        "seed",
        "H",
        "N",
        "gamma",
        "communication_rounds",
        "r_x",
        "r_xi",
        "r_qbar",
        "r_max",
        "pathwise_pass",
    }
    required_theory_columns = {
        "gate",
        "H_if_applicable",
        "residual",
        "threshold",
        "passed",
    }
    if not required_pair_columns <= set(pairs.columns):
        raise RuntimeError("Saved rotation pair summary has an invalid schema")
    if not required_theory_columns <= set(theory.columns):
        raise RuntimeError("Saved rotation theory summary has an invalid schema")
    Q = rotation_matrix(load_rotation_config())
    all_pathwise = bool(pairs["pathwise_pass"].astype(bool).all())
    all_theory = bool(theory["passed"].astype(bool).all())
    lines = [
        "# P2 d=2 rotation-equivariance report",
        "",
        "## Classification",
        "",
        "EMPIRICAL / NUMERICAL SANITY",
        "",
        "## Source provenance",
        "",
        f"- Source commit: `{provenance['source_commit']}`",
        f"- Source dirty at run start: `{provenance['source_dirty_at_run_start']}`",
        f"- Config SHA-256: `{provenance['config_sha256']}`",
        f"- Protocol SHA-256: `{provenance['protocol_sha256']}`",
        "",
        "## Frozen transformation",
        "",
        "```text",
        np.array2string(Q, precision=16),
        "```",
        "",
        "## Matrix and seeds",
        "",
        f"- Matrix: `{provenance['matrix_id']}`",
        f"- Pairs: {len(pairs)}",
        f"- Seeds: {', '.join(str(value) for value in sorted(pairs['seed'].unique()))}",
        f"- Communication rounds: {', '.join(str(value) for value in sorted(pairs['communication_rounds'].unique()))}",
        "",
        "## Theory gates",
        "",
        "| Gate | H | Residual | Threshold | Pass |",
        "|---|---:|---:|---:|:---:|",
    ]
    for row in theory.to_dict(orient="records"):
        H = "" if pd.isna(row["H_if_applicable"]) else str(int(row["H_if_applicable"]))
        lines.append(
            f"| {row['gate']} | {H} | {float(row['residual']):.6e} | "
            f"{float(row['threshold']):.6e} | {bool(row['passed'])} |"
        )
    lines.extend(
        [
            "",
            "## Pathwise residuals",
            "",
            "| Pair | H | N | Seed | r_x | r_xi | r_qbar | r_max | Pass |",
            "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
        ]
    )
    for row in pairs.to_dict(orient="records"):
        lines.append(
            f"| {row['pair_id']} | {int(row['H'])} | {int(row['N'])} | "
            f"{int(row['seed'])} | {float(row['r_x']):.6e} | "
            f"{float(row['r_xi']):.6e} | {float(row['r_qbar']):.6e} | "
            f"{float(row['r_max']):.6e} | {bool(row['pathwise_pass'])} |"
        )
    lines.extend(
        [
            "",
            "## Global pathwise gate",
            "",
            f"- max r_x: `{float(pairs['r_x'].max()):.6e}`",
            f"- max r_xi: `{float(pairs['r_xi'].max()):.6e}`",
            f"- max r_qbar: `{float(pairs['r_qbar'].max()):.6e}`",
            f"- Theory gates pass: `{all_theory}`",
            f"- Every pathwise pair passes: `{all_pathwise}`",
            "",
            "## Optional estimator diagnostics",
            "",
            "No optional estimator-equivariance diagnostic was recorded.",
            "",
            "## Interpretation boundary",
            "",
            "The numerical result checks implementation and representation consistency under the",
            "pre-registered 30-degree transformation. It is not a new proof, an independent",
            "coefficient validation, a universal coordinate-invariance result, or evidence about",
            "another noise law, d=5, or heterogeneity.",
            "",
        ]
    )
    destination = output_path or source_root / P2_ROTATION_REPORT
    destination.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = source_root / P2_ROTATION_MANIFEST
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["report"] = "BUILT_FROM_SAVED_SUMMARIES"
        write_json(manifest, manifest_path)
    return destination


def report_rotation_formal() -> Path:
    config = load_rotation_config()
    root = rotation_artifact_root(config)
    validate_rotation_output_root(root, root)
    if not root.is_dir():
        raise RuntimeError("Formal rotation summaries do not exist")
    staged = stage_existing_directory(root)
    try:
        report = build_rotation_report_from_saved(staged)
        validate_controlled_overwrite(
            staged,
            root,
            raw_result_files=P2_ROTATION_RAW_FILES,
            provenance_filename=P2_ROTATION_PROVENANCE,
            identity_fields=("config_sha256", "protocol_sha256", "matrix_id"),
        )
        replace_output_directory(staged, root)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    return root / report.relative_to(staged)
