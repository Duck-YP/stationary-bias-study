import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import stationary_bias.cli as cli
import stationary_bias.workstreams.p2_multidimensional_validation.plateau as plateau
from stationary_bias.workstreams.p2_multidimensional_validation.formal import (
    P2_RUN_START_PROVENANCE,
)
from stationary_bias.workstreams.p2_multidimensional_validation.plateau_analysis import (
    build_plateau_fits,
    build_plateau_outputs,
    validate_saved_plateau,
)
from stationary_bias.workstreams.p2_multidimensional_validation.theory import (
    vector_theory_targets,
)


def _existing_p2_artifact_hashes() -> dict[Path, str]:
    root = (
        plateau.P2_PLATEAU_ROOT / "artifacts" / "formal"
    )
    return {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and path.parent.name != plateau.P2_PLATEAU_MATRIX_ID
    }


def _synthetic_plateau(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    config = plateau.load_plateau_config()
    specs = plateau.build_plateau_run_matrix(config)
    objective = plateau.objective_from_formal_config(config)
    covariance = plateau.covariance_from_formal_config(config)
    targets = vector_theory_targets(objective, covariance, 2)
    seed_effects = dict(
        zip(
            config["chains"]["seeds"],
            np.linspace(-0.0014, 0.0014, 8),
            strict=True,
        )
    )
    beta0 = targets.B20 + (1.0 / 24.0) * np.array([0.03, -0.02])
    beta1 = np.array([0.08, 0.10])
    run_rows: list[dict] = []
    batch_rows: list[dict] = []
    config_sha = hashlib.sha256(plateau.P2_PLATEAU_CONFIG_PATH.read_bytes()).hexdigest()
    for spec in specs:
        for estimator in ("direct_sample_mean", "stationary_mean_balance"):
            for coordinate in range(2):
                diagnostic_shift = 0.0002 if estimator == "direct_sample_mean" else 0.0
                C_value = (
                    beta0[coordinate]
                    + beta1[coordinate] / spec.N
                    + seed_effects[spec.seed]
                    + diagnostic_shift
                )
                b_value = (
                    spec.gamma**2 * C_value
                    + (spec.gamma / spec.N) * targets.B11_d[coordinate]
                )
                row = {
                    "study": "p2_multidimensional_validation",
                    "phase": "formal",
                    "matrix_id": spec.matrix_id,
                    "setting_id": spec.setting_id,
                    "run_id": spec.run_id,
                    "seed": spec.seed,
                    "d": spec.d,
                    "coordinate": coordinate,
                    "H": spec.H,
                    "N": spec.N,
                    "gamma": spec.gamma,
                    "delta": spec.delta,
                    "estimator": estimator,
                    "b_component": b_value,
                    "B11_d_component": targets.B11_d[coordinate],
                    "C_component": C_value,
                    "B20_component": targets.B20[coordinate],
                    "normalized_error_component": C_value - targets.B20[coordinate],
                    "batches_used": 100,
                    "stopping_reason": "PRECISION_REACHED",
                    "validity_pass": True,
                    "finite_state_pass": True,
                    "zero_sum_control_error": 0.0,
                    "zero_sum_control_pass": True,
                    "stationarity_pass": True,
                    "direct_balance_agreement_pass": True,
                    "mixing_scale": 15,
                    "burn_in_rounds": 1500,
                    "batch_length": 300,
                    "source_commit": "fixture-commit",
                    "source_dirty_at_run_start": False,
                    "config_sha256": config_sha,
                }
                run_rows.append(row)
                batch_rows.append(
                    {
                        key: row[key]
                        for key in (
                            "study",
                            "phase",
                            "matrix_id",
                            "setting_id",
                            "run_id",
                            "seed",
                            "d",
                            "coordinate",
                            "H",
                            "N",
                            "gamma",
                            "delta",
                            "estimator",
                            "b_component",
                            "B11_d_component",
                            "C_component",
                            "B20_component",
                            "normalized_error_component",
                            "batches_used",
                            "stopping_reason",
                            "validity_pass",
                        )
                    }
                    | {"batch_index": 0}
                )
    pd.DataFrame(run_rows).to_csv(root / "run_summary.csv", index=False)
    pd.DataFrame(batch_rows).to_csv(root / "batch_summary.csv", index=False)
    snapshot = root / config["config_snapshot_filename"]
    snapshot.write_bytes(plateau.P2_PLATEAU_CONFIG_PATH.read_bytes())
    provenance = {
        "schema_version": 2,
        "capture_point": "before_any_p2_plateau_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "formal_fixed_gamma_large_N_plateau",
        "matrix_id": plateau.P2_PLATEAU_MATRIX_ID,
        "source_commit": "fixture-commit",
        "source_dirty_at_run_start": False,
        "environment": {"python": "3.12.fixture", "packages": {}},
        "config_path": str(plateau.P2_PLATEAU_CONFIG_PATH),
        "config_sha256": config_sha,
        "protocol_path": str(plateau.P2_PLATEAU_PROTOCOL_PATH),
        "protocol_sha256": hashlib.sha256(
            plateau.P2_PLATEAU_PROTOCOL_PATH.read_bytes()
        ).hexdigest(),
        "config_snapshot": config["config_snapshot_filename"],
        "seeds": config["chains"]["seeds"],
        "bootstrap_seed": config["bootstrap"]["seed"],
        "bootstrap_repetitions": config["bootstrap"]["repetitions"],
        "run_matrix": plateau.audit_plateau_run_matrix(specs),
        "expected_chain_count": len(specs),
        "planned_coordinate_run_rows": len(run_rows),
        "commands": config["commands"],
        "artifact_namespace": config["artifact_namespace"],
    }
    (root / P2_RUN_START_PROVENANCE).write_text(
        json.dumps(provenance), encoding="utf-8"
    )


def test_plateau_matrix_is_exact_fixed_gamma_and_fresh() -> None:
    checked = plateau.check_plateau_protocol()
    assert checked["status"] == "PASS"
    assert checked["fresh_seed_block"] is True
    assert checked["fit_variable"] == "1/N"
    runs = plateau.build_plateau_run_matrix()
    assert plateau.audit_plateau_run_matrix(runs) == plateau.expected_plateau_audit()
    assert {run.gamma for run in runs} == {1.0 / 24.0}
    assert {run.N for run in runs} == {8, 16, 32, 64, 128}
    assert len(runs) == 40
    for N in (8, 16, 32, 64, 128):
        selected = [run for run in runs if run.N == N]
        assert len(selected) == 8
        assert {run.seed for run in selected} == set(range(1301, 1309))


def test_plateau_normalization_and_inverse_N_intercept(tmp_path: Path) -> None:
    _synthetic_plateau(tmp_path)
    run_df, _, _, config = validate_saved_plateau(tmp_path)
    sample = run_df.iloc[0]
    expected = (
        sample["b_component"]
        - (sample["gamma"] / sample["N"]) * sample["B11_d_component"]
    ) / sample["gamma"] ** 2
    assert sample["C_component"] == pytest.approx(expected)
    fits, curve, bootstrap = build_plateau_fits(run_df, config)
    assert set(fits["fit_variable"]) == {"inverse_N"}
    assert sorted(curve["inverse_N"].unique()) == sorted(
        1.0 / np.array([8, 16, 32, 64, 128])
    )
    targets = np.asarray(config["theory"]["B20"]["value"])
    expected_beta0 = targets + (1.0 / 24.0) * np.array([0.03, -0.02])
    np.testing.assert_allclose(
        fits.sort_values("coordinate")["beta0"], expected_beta0, atol=1.0e-14
    )
    assert len(bootstrap) == 4000


def test_plateau_outputs_have_two_figures_and_do_not_touch_previous_artifacts(
    tmp_path: Path,
) -> None:
    before = _existing_p2_artifact_hashes()
    _synthetic_plateau(tmp_path)
    outputs = build_plateau_outputs(tmp_path)
    assert outputs["verdict"] == "PASS"
    assert [path.name for path in outputs["figures"]] == [
        "p2_d2_fixed_gamma_largeN_coordinate_1.png",
        "p2_d2_fixed_gamma_largeN_coordinate_2.png",
    ]
    assert all(path.stat().st_size > 0 for path in outputs["figures"])
    report = outputs["report"].read_text(encoding="utf-8")
    assert "beta0_minus_B20_over_gamma" in report
    manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
    assert manifest["verdict"] == "PASS"
    assert manifest["fit_model"]["fit_variable"] == "inverse_N"
    assert manifest["theory"]["exact_B20_CI_coverage_required"] is False
    assert _existing_p2_artifact_hashes() == before


def test_plateau_formal_runner_refuses_dirty_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(plateau, "plateau_artifact_root", lambda *args: tmp_path / "formal")
    monkeypatch.setattr(
        plateau,
        "environment_manifest",
        lambda: {
            "python": "3.12.fixture",
            "platform": "fixture",
            "packages": {},
            "git_commit": "fixture-commit",
            "git_dirty": True,
        },
    )
    with pytest.raises(RuntimeError, match="clean committed source tree"):
        plateau.run_plateau_experiment()
    assert not (tmp_path / "formal").exists()


def test_plateau_cli_check_and_run_route(capsys, monkeypatch) -> None:
    assert cli.main(["p2", "plateau", "check"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    monkeypatch.setattr(
        plateau,
        "run_plateau_experiment",
        lambda: {
            "verdict": "PASS",
            "output_root": Path("fixture-plateau"),
            "report": Path("fixture-plateau/report.md"),
            "figures": [Path("fixture-plateau/c1.png"), Path("fixture-plateau/c2.png")],
            "manifest": Path("fixture-plateau/manifest.json"),
            "overwrite_audit": {
                "previous_output": "absent",
                "scientific_results_match": None,
                "compared_files": [],
            },
        },
    )
    assert cli.main(["p2", "plateau", "run"]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "PASS"
