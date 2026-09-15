import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import stationary_bias.cli as cli
import stationary_bias.workstreams.p2_multidimensional_validation.rotation as rotation
from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import (
    scaffold_round_many_vector,
)


def test_rotation_config_protocol_theory_and_matrix_integrity() -> None:
    checked = rotation.check_rotation_protocol()
    assert checked["status"] == "PASS"
    assert checked["communication_rounds"] == 200
    assert checked["scientific_execution"] == "NOT_RUN"
    assert checked["matrix"] == {
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
    assert len(checked["theory_gates"]) == 8
    assert all(row["passed"] for row in checked["theory_gates"])


def test_last_axis_rotation_uses_q_transpose() -> None:
    config = rotation.load_rotation_config()
    Q = rotation.rotation_matrix(config)
    values = np.array([[0.2, -0.1], [-0.3, 0.7], [1.2, 0.4]])
    observed = rotation.rotate_last_axis(values, Q)
    expected = np.stack([Q @ row for row in values])
    np.testing.assert_allclose(observed, expected, rtol=0.0, atol=1.0e-15)
    assert not np.allclose(observed, values @ Q, rtol=0.0, atol=1.0e-12)


def test_objective_gradient_and_q_are_equivariant() -> None:
    config = rotation.load_rotation_config()
    Q = rotation.rotation_matrix(config)
    original, rotated = rotation.objectives_from_rotation_config(config)
    points = np.array(
        [[0.31, -0.27], [-0.8, 0.2], [1.1, -0.9], [0.02, 0.44]]
    )
    transformed = rotation.rotate_last_axis(points, Q)
    np.testing.assert_allclose(
        rotated.grad(transformed),
        rotation.rotate_last_axis(original.grad(points), Q),
        rtol=0.0,
        atol=1.0e-15,
    )
    np.testing.assert_allclose(
        rotated.q(transformed),
        rotation.rotate_last_axis(original.q(points), Q),
        rtol=0.0,
        atol=1.0e-15,
    )


def test_deterministic_one_round_scaffold_equivariance() -> None:
    config = rotation.load_rotation_config()
    Q = rotation.rotation_matrix(config)
    original_objective, rotated_objective = rotation.objectives_from_rotation_config(config)
    x = np.array([[0.37, -0.22]])
    xi = np.array([[[0.12, -0.04], [-0.05, 0.09], [-0.07, -0.05]]])
    np.testing.assert_allclose(np.sum(xi, axis=1), 0.0, rtol=0.0, atol=1.0e-15)
    noise = np.array(
        [
            [
                [[0.4, -0.3], [-0.2, 0.1], [0.15, 0.25]],
                [[-0.1, 0.2], [0.3, -0.4], [-0.25, 0.05]],
                [[0.07, -0.11], [0.19, 0.23], [-0.31, 0.13]],
            ]
        ]
    )
    original = scaffold_round_many_vector(
        x,
        xi,
        gamma=0.04,
        H=3,
        objective=original_objective,
        epsilon_steps=noise,
    )
    rotated = scaffold_round_many_vector(
        rotation.rotate_last_axis(x, Q),
        rotation.rotate_last_axis(xi, Q),
        gamma=0.04,
        H=3,
        objective=rotated_objective,
        epsilon_steps=rotation.rotate_last_axis(noise, Q),
    )
    residuals = {
        "r_x": np.max(
            np.abs(rotated.x_new - rotation.rotate_last_axis(original.x_new, Q))
        ),
        "r_xi": np.max(
            np.abs(rotated.xi_new - rotation.rotate_last_axis(original.xi_new, Q))
        ),
        "r_qbar": np.max(
            np.abs(rotated.qbar - rotation.rotate_last_axis(original.qbar, Q))
        ),
    }
    assert max(residuals.values()) <= 2.0e-15


def test_short_multi_round_pair_is_pathwise_equivariant() -> None:
    config = rotation.load_rotation_config()
    formal = rotation.build_rotation_pair_matrix(config)[0]
    fixture = replace(
        formal,
        N=5,
        gamma=0.04,
        communication_rounds=7,
    )
    row = rotation.run_rotation_pair(fixture, config)
    assert row["communication_rounds"] == 7
    assert row["r_max"] <= 1.0e-12
    assert row["pathwise_pass"] is True


def test_paired_noise_is_reproducible_and_has_no_rotated_rng(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = rotation.load_rotation_config()
    spec = replace(
        rotation.build_rotation_pair_matrix(config)[0],
        N=3,
        communication_rounds=2,
    )
    generator_calls = []
    default_rng = np.random.default_rng

    def one_rng(seed):
        generator_calls.append(seed)
        return default_rng(seed)

    monkeypatch.setattr(rotation.np.random, "default_rng", one_rng)
    first_original, first_rotated = rotation.generate_paired_noise(spec, config)
    assert generator_calls == [spec.seed]
    second_original, second_rotated = rotation.generate_paired_noise(spec, config)
    assert generator_calls == [spec.seed, spec.seed]
    np.testing.assert_array_equal(first_original, second_original)
    np.testing.assert_array_equal(first_rotated, second_rotated)
    np.testing.assert_allclose(
        first_rotated,
        first_original @ rotation.rotation_matrix(config).T,
        rtol=0.0,
        atol=0.0,
    )

    calls = []
    frozen_original = first_original.copy()

    def one_original_draw(rngs, covariance, *, rounds, H, N):
        calls.append((len(rngs), rounds, H, N, np.asarray(covariance).copy()))
        return frozen_original[None, ...]

    monkeypatch.setattr(rotation, "generate_vector_noise_block", one_original_draw)
    observed_original, observed_rotated = rotation.generate_paired_noise(spec, config)
    assert len(calls) == 1
    assert calls[0][:4] == (1, 2, spec.H, 3)
    np.testing.assert_array_equal(observed_original, frozen_original)
    np.testing.assert_array_equal(
        observed_rotated,
        rotation.rotate_last_axis(frozen_original, rotation.rotation_matrix(config)),
    )


def test_matrix_ids_are_stable_unique_and_exact() -> None:
    first = rotation.build_rotation_pair_matrix()
    second = rotation.build_rotation_pair_matrix()
    assert len(first) == 16
    assert [item.pair_id for item in first] == [item.pair_id for item in second]
    assert len({item.pair_id for item in first}) == 16
    assert {item.seed for item in first} == {1101, 1102, 1103, 1104}
    assert {item.H for item in first} == {2, 4}
    assert {(item.N, item.gamma) for item in first} == {(16, 1 / 16), (64, 1 / 64)}
    assert {item.communication_rounds for item in first} == {200}
    assert all(item.gamma == 1 / item.N for item in first)
    assert all("p2__phase-rotation" in item.pair_id for item in first)


def _synthetic_rotation_outputs(root: Path) -> tuple[Path, list[dict], list[dict]]:
    config = rotation.load_rotation_config()
    specs = rotation.build_rotation_pair_matrix(config)
    pair_rows = []
    for index, spec in enumerate(specs, start=1):
        residual = index * 1.0e-14
        pair_rows.append(
            {
                "study": "p2_multidimensional_validation",
                "phase": "rotation",
                "matrix_id": spec.matrix_id,
                "pair_id": spec.pair_id,
                "seed": spec.seed,
                "H": spec.H,
                "N": spec.N,
                "gamma": spec.gamma,
                "communication_rounds": spec.communication_rounds,
                "r_x": residual,
                "r_xi": residual / 2,
                "r_qbar": residual / 3,
                "r_max": residual,
                "pathwise_pass": True,
            }
        )
    theory_rows = rotation.theory_rotation_rows(config)
    provenance = {
        "schema_version": 1,
        "capture_point": "before_any_p2_rotation_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "rotation",
        "matrix_id": config["matrix_identifier"],
        "source_commit": "fixture-commit",
        "source_dirty_at_run_start": False,
        "environment": {"python": "3.12.fixture"},
        "config_path": str(rotation.P2_ROTATION_CONFIG_PATH),
        "config_sha256": hashlib.sha256(
            rotation.P2_ROTATION_CONFIG_PATH.read_bytes()
        ).hexdigest(),
        "protocol_path": str(rotation.P2_ROTATION_PROTOCOL_PATH),
        "protocol_sha256": hashlib.sha256(
            rotation.P2_ROTATION_PROTOCOL_PATH.read_bytes()
        ).hexdigest(),
        "run_matrix": rotation.audit_rotation_pair_matrix(),
        "pairs": [
            {
                "pair_id": spec.pair_id,
                "seed": spec.seed,
                "H": spec.H,
                "N": spec.N,
                "gamma": spec.gamma,
                "communication_rounds": spec.communication_rounds,
            }
            for spec in specs
        ],
        "artifact_namespace": config["artifact_contract"]["namespace"],
    }
    output = root / "synthetic-rotation"
    rotation.write_rotation_raw_outputs(
        pair_rows,
        theory_rows,
        provenance,
        config,
        target_root=output,
        expected_root=output,
    )
    return output, pair_rows, theory_rows


def test_artifact_schema_and_report_use_only_saved_summaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = rotation.load_rotation_config()
    root, pair_rows, theory_rows = _synthetic_rotation_outputs(tmp_path)
    expected_raw = {
        rotation.P2_ROTATION_PROVENANCE,
        rotation.P2_ROTATION_PAIR_SUMMARY,
        rotation.P2_ROTATION_RESIDUAL_SUMMARY,
        rotation.P2_ROTATION_THEORY_SUMMARY,
        rotation.P2_ROTATION_MANIFEST,
        rotation.P2_ROTATION_REPORT,
    }
    assert {path.name for path in root.iterdir()} == expected_raw
    pairs = pd.read_csv(root / rotation.P2_ROTATION_PAIR_SUMMARY)
    residuals = pd.read_csv(root / rotation.P2_ROTATION_RESIDUAL_SUMMARY)
    theory = pd.read_csv(root / rotation.P2_ROTATION_THEORY_SUMMARY)
    assert len(pairs) == len(pair_rows)
    assert len(theory) == len(theory_rows)
    assert set(residuals["metric"]) == {"r_x", "r_xi", "r_qbar", "r_max"}
    assert set(residuals["scope"]) == {"pair", "global"}
    assert all(np.isscalar(value) for value in residuals["residual"])
    manifest = json.loads((root / rotation.P2_ROTATION_MANIFEST).read_text())
    assert manifest["report"] == "BUILT_FROM_SAVED_SUMMARIES"
    assert rotation.P2_ROTATION_REPORT in manifest["artifact_filenames"]
    assert manifest["pathwise_gate"] == {
        "residual": "max(r_x, r_xi, r_qbar)",
        "tolerance": 1.0e-10,
        "scope": "every_paired_run",
        "required_pass_count": 16,
        "observed_pass_count": 16,
    }
    assert manifest["pathwise_gate"]["tolerance"] == config[
        "pathwise_equivariance"
    ]["primary_gate"]["tolerance"]
    assert manifest["expected_pair_count"] == 16
    assert manifest["observed_pair_count"] == 16
    assert manifest["run_matrix"]["communication_rounds"] == [200]
    assert manifest["run_matrix"]["seeds"] == [1101, 1102, 1103, 1104]
    assert manifest["config_sha256"] == hashlib.sha256(
        rotation.P2_ROTATION_CONFIG_PATH.read_bytes()
    ).hexdigest()
    assert manifest["protocol_sha256"] == hashlib.sha256(
        rotation.P2_ROTATION_PROTOCOL_PATH.read_bytes()
    ).hexdigest()
    assert manifest["source_commit"] == "fixture-commit"
    assert manifest["source_dirty_at_provenance_capture"] is False
    assert manifest["interpretation_boundary"] == config["interpretation_boundary"]
    assert manifest["interpretation_boundary"]["permitted_conclusion"] == (
        "The implementation and theoretical coefficient are equivariant under the "
        "pre-registered 30-degree orthogonal coordinate transformation."
    )
    assert set(manifest["interpretation_boundary"]["excluded_claims"]) == {
        "new_theorem_proof",
        "independent_coefficient_validation",
        "invariance_under_every_coordinate_transformation",
        "robustness_to_a_different_noise_law",
        "d5_validation",
        "heterogeneity_validation",
    }
    monkeypatch.setattr(
        rotation,
        "run_rotation_pair",
        lambda *args, **kwargs: pytest.fail("report attempted simulation"),
    )
    report = rotation.build_rotation_report_from_saved(root)
    text = report.read_text(encoding="utf-8")
    assert "EMPIRICAL / NUMERICAL SANITY" in text
    assert "fixture-commit" in text
    assert "Theory gates pass: `True`" in text
    assert "Every pathwise pair passes: `True`" in text
    updated_manifest = json.loads((root / rotation.P2_ROTATION_MANIFEST).read_text())
    assert updated_manifest["report"] == "BUILT_FROM_SAVED_SUMMARIES"


def test_clean_source_overwrite_and_namespace_guards(tmp_path: Path) -> None:
    rotation.require_clean_committed_source(
        {"source_dirty_at_run_start": False, "source_commit": "abc123"}
    )
    with pytest.raises(RuntimeError, match="clean committed"):
        rotation.require_clean_committed_source(
            {"source_dirty_at_run_start": True, "source_commit": "abc123"}
        )
    with pytest.raises(RuntimeError, match="clean committed"):
        rotation.require_clean_committed_source(
            {"source_dirty_at_run_start": False, "source_commit": "NO_COMMIT"}
        )
    expected = tmp_path / "isolated-rotation"
    with pytest.raises(RuntimeError, match="selected isolated namespace"):
        rotation.validate_rotation_output_root(tmp_path / "other", expected)
    with pytest.raises(RuntimeError, match="prior P0/P1/P2 evidence"):
        prior = tmp_path / "p2-d2-coefficient-primary"
        rotation.validate_rotation_output_root(prior, prior)

    output, pair_rows, theory_rows = _synthetic_rotation_outputs(tmp_path)
    config = rotation.load_rotation_config()
    provenance = json.loads((output / rotation.P2_ROTATION_PROVENANCE).read_text())
    rotation.write_rotation_raw_outputs(
        pair_rows,
        theory_rows,
        provenance,
        config,
        target_root=output,
        expected_root=output,
    )
    changed = [dict(row) for row in pair_rows]
    changed[0]["r_x"] = 1.0e-12
    changed[0]["r_max"] = 1.0e-12
    with pytest.raises(RuntimeError, match="changed scientific results"):
        rotation.write_rotation_raw_outputs(
            changed,
            theory_rows,
            provenance,
            config,
            target_root=output,
            expected_root=output,
        )


def test_manifest_rejects_gate_result_inconsistent_with_frozen_tolerance(
    tmp_path: Path,
) -> None:
    output, pair_rows, theory_rows = _synthetic_rotation_outputs(tmp_path)
    config = rotation.load_rotation_config()
    provenance = json.loads((output / rotation.P2_ROTATION_PROVENANCE).read_text())
    inconsistent = [dict(row) for row in pair_rows]
    inconsistent[0]["r_max"] = 2.0e-10
    inconsistent[0]["pathwise_pass"] = True
    with pytest.raises(RuntimeError, match="disagrees with the frozen tolerance"):
        rotation._rotation_manifest(
            provenance, inconsistent, theory_rows, config
        )


def test_rotation_cli_check_only(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["p2", "rotation", "check"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["communication_rounds"] == 200
    assert payload["scientific_execution"] == "NOT_RUN"
