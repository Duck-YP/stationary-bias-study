import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import stationary_bias.workstreams.p2_multidimensional_validation.formal as formal
from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import (
    scaffold_round_many_vector,
)
from stationary_bias.workstreams.p2_multidimensional_validation.formal_analysis import (
    analyze_formal_saved,
    build_falsification_summary,
    build_formal_report_and_plots,
    validate_saved_formal_matrix,
)
from stationary_bias.workstreams.p2_multidimensional_validation.formal_inference import (
    evaluate_vector_precision,
    fit_delta_line,
    seed_block_bootstrap,
    student_t_critical,
)
from stationary_bias.workstreams.p2_multidimensional_validation.theory import (
    vector_theory_targets,
)


def test_d5_frozen_inputs_algebra_and_manifest_contract() -> None:
    result = formal.check_d5_protocol()
    config = formal.load_formal_config("d5")
    assert result["status"] == "PASS"
    assert result["scientific_execution"] == "NOT_RUN"
    assert result["matrix"]["chains"] == 80
    assert result["manifest_audit"] == "PASS"
    assert result["config_sha256"] == hashlib.sha256(
        formal.P2_D5_CONFIG_PATH.read_bytes()
    ).hexdigest()
    assert result["protocol_sha256"] == hashlib.sha256(
        formal.P2_D5_PROTOCOL_PATH.read_bytes()
    ).hexdigest()
    np.testing.assert_allclose(
        result["A_eigenvalues"], config["objective"]["A_eigenvalues"], atol=1e-14
    )
    np.testing.assert_allclose(
        result["C_eigenvalues"], config["noise"]["covariance_eigenvalues"], atol=1e-14
    )
    assert result["commutator_frobenius_norm"] == pytest.approx(
        0.08761712161444248
    )
    assert result["mu"] == pytest.approx(0.8037572789315114)
    assert result["L"] == pytest.approx(1.6235689623537297)
    assert result["lyapunov_residual"] < 1e-14


def test_d5_direction_theory_and_decomposition() -> None:
    config = formal.load_formal_config("d5")
    objective = formal.objective_from_formal_config(config)
    covariance = formal.covariance_from_formal_config(config)
    u = objective.u
    assert np.linalg.norm(u) == pytest.approx(1.0)
    assert np.any(u > 0) and np.any(u < 0) and np.count_nonzero(u) == 5
    for H in (2, 4):
        targets = vector_theory_targets(objective, covariance, H)
        expected = config["theory"]["by_H"][H]
        np.testing.assert_allclose(targets.S_C, config["theory"]["S_C"], atol=1e-14)
        np.testing.assert_allclose(targets.B11_d, config["theory"]["B11_d"], atol=1e-14)
        np.testing.assert_allclose(targets.B20, expected["B20"], atol=1e-14)
        np.testing.assert_allclose(targets.B20_local, expected["B20_local"], atol=1e-14)
        np.testing.assert_allclose(targets.B20_ctrl, expected["B20_ctrl"], atol=1e-14)
        np.testing.assert_allclose(
            targets.B20_local + targets.B20_ctrl, targets.B20, atol=1e-15
        )


def test_existing_vector_kernel_accepts_d5_tiny_data() -> None:
    config = formal.load_formal_config("d5")
    objective = formal.objective_from_formal_config(config)
    result = scaffold_round_many_vector(
        np.zeros((2, 5)),
        np.zeros((2, 3, 5)),
        gamma=1 / 32,
        H=2,
        objective=objective,
        epsilon_steps=np.zeros((2, 2, 3, 5)),
    )
    assert result.x_new.shape == (2, 5)
    assert result.xi_new.shape == (2, 3, 5)
    assert result.qbar.shape == (2, 2, 5)


def test_d5_matrix_ids_dimensions_and_workload_formulas() -> None:
    config = formal.load_formal_config("d5")
    first = formal.build_formal_run_matrix("d5", config)
    second = formal.build_formal_run_matrix("d5", config)
    assert len(first) == 80
    assert len({item.run_id for item in first}) == 80
    assert [item.run_id for item in first] == [item.run_id for item in second]
    assert {(item.H, item.N) for item in first} == {
        (H, N) for H in (2, 4) for N in (32, 48, 64, 96, 128)
    }
    for spec in first:
        dimensions = formal.formal_protocol_dimensions(spec, config)
        mixing = int(np.ceil(1 / (config["protocol"]["mixing_mu"] * spec.H * spec.gamma)))
        assert dimensions["mixing_scale"] == mixing
        assert dimensions["burn_in_rounds"] == 100 * mixing
        assert dimensions["batch_length"] == 20 * mixing


def test_d5_inference_precision_ols_and_bootstrap_contract() -> None:
    config = formal.load_formal_config("d5")
    assert student_t_critical(0.99, 7) == pytest.approx(3.4994832973504924)
    targets = np.asarray(config["theory"]["by_H"][2]["B20"])
    passing = np.tile(targets, (8, 1))
    assert evaluate_vector_precision(
        passing, targets, confidence_level=0.99
    )["joint_pass"] is True
    failing = passing.copy()
    failing[:, 4] += np.linspace(-0.02, 0.02, 8)
    precision = evaluate_vector_precision(failing, targets, confidence_level=0.99)
    assert precision["coordinate_pass"].tolist() == [True, True, True, True, False]
    delta = np.array([2 / N for N in (32, 48, 64, 96, 128)])
    fit = fit_delta_line(delta, -0.25 + 0.7 * delta)
    assert fit.beta0 == pytest.approx(-0.25)
    assert fit.beta1 == pytest.approx(0.7)
    assert config["bootstrap"]["repetitions"] == 5000
    assert config["bootstrap"]["seed"] == 3901
    values = np.arange(5 * 8 * 5, dtype=float).reshape(5, 8, 5)
    boot = seed_block_bootstrap(
        delta, values, config["chains"]["seeds"], repetitions=3, bootstrap_seed=3901
    )
    assert boot["sampled_indices"].shape == (3, 8)
    assert boot["intercepts"].shape == (3, 5)
    # Each replicate exposes one seed-index block, reused by all five settings.
    assert boot["sampled_indices"].ndim == 2


def _write_synthetic_d5_matrix(root: Path) -> None:
    root.mkdir()
    config = formal.load_formal_config("d5")
    specs = formal.build_formal_run_matrix("d5", config)
    objective = formal.objective_from_formal_config(config)
    covariance = formal.covariance_from_formal_config(config)
    effects = dict(
        zip(config["chains"]["seeds"], np.linspace(-0.0005, 0.0005, 8), strict=True)
    )
    run_rows: list[dict[str, object]] = []
    batch_rows: list[dict[str, object]] = []
    config_hash = hashlib.sha256(formal.P2_D5_CONFIG_PATH.read_bytes()).hexdigest()
    for spec in specs:
        targets = vector_theory_targets(objective, covariance, spec.H)
        for estimator in ("direct_sample_mean", "stationary_mean_balance"):
            for coordinate in range(5):
                C_value = (
                    float(targets.B20[coordinate])
                    + (coordinate + 1) * 0.1 * spec.delta
                    + effects[spec.seed]
                    + (0.0001 if estimator == "direct_sample_mean" else 0.0)
                )
                row = {
                    "study": "p2_multidimensional_validation",
                    "phase": "formal",
                    "matrix_id": spec.matrix_id,
                    "setting_id": spec.setting_id,
                    "run_id": spec.run_id,
                    "seed": spec.seed,
                    "d": 5,
                    "coordinate": coordinate,
                    "H": spec.H,
                    "N": spec.N,
                    "gamma": spec.gamma,
                    "delta": spec.delta,
                    "estimator": estimator,
                    "b_component": spec.gamma**2 * C_value
                    + (spec.gamma / spec.N) * targets.B11_d[coordinate],
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
                    "mixing_scale": 1,
                    "burn_in_rounds": 100,
                    "batch_length": 20,
                    "source_commit": "fixture-commit",
                    "source_dirty_at_run_start": False,
                    "config_sha256": config_hash,
                }
                run_rows.append(row)
                batch_rows.append(row | {"batch_index": 0})
    pd.DataFrame(run_rows).to_csv(root / "run_summary.csv", index=False)
    pd.DataFrame(batch_rows).to_csv(root / "batch_summary.csv", index=False)
    provenance = {
        "matrix_id": config["matrix_identifier"],
        "source_commit": "fixture-commit",
        "source_dirty_at_run_start": False,
        "environment": {"python": "3.12.fixture"},
        "config_path": str(formal.P2_D5_CONFIG_PATH),
        "config_sha256": config_hash,
        "protocol_path": str(formal.P2_D5_PROTOCOL_PATH),
        "protocol_sha256": hashlib.sha256(formal.P2_D5_PROTOCOL_PATH.read_bytes()).hexdigest(),
        "seeds": config["chains"]["seeds"],
        "bootstrap_seed": 3901,
        "bootstrap_repetitions": 5000,
        "run_matrix": formal.audit_formal_run_matrix("d5", specs),
        "expected_chain_count": 80,
    }
    (root / formal.P2_RUN_START_PROVENANCE).write_text(json.dumps(provenance))


def test_d5_saved_analysis_gates_manifest_report_and_figures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "d5"
    _write_synthetic_d5_matrix(root)
    analyzed = analyze_formal_saved("d5", root)
    assert len(analyzed["setting_summary"]) == 100
    assert len(analyzed["fit_summary"]) == 50
    assert len(analyzed["bootstrap_intercepts"]) == 50_000
    gates = analyzed["falsification_summary"]
    assert set(gates["gate"]) == {"V0", "V1", "V2", "V3", "V4", "V5"}
    for gate in ("V0", "V1", "V2", "V5"):
        assert bool(gates.loc[gates["gate"] == gate, "passed"].iloc[0])
    manifest = json.loads(analyzed["manifest"].read_text())
    formal.audit_d5_manifest(manifest)
    assert manifest["source_dirty"] is False
    assert manifest["observed_chain_count"] == 80
    assert manifest["bootstrap_repetitions"] == 5000
    monkeypatch.setattr(
        formal,
        "simulate_formal_setting",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("simulator called")),
    )
    outputs = build_formal_report_and_plots("d5", root)
    assert outputs["report"].name == "p2_d5_controlled_validation_report.md"
    assert "pre-registered controlled d=5 experiment" in outputs["report"].read_text(
        encoding="utf-8"
    )
    assert {item.name for item in outputs["figures"]} == {
        "p2_d5_H2_coefficient_convergence.png",
        "p2_d5_H4_coefficient_convergence.png",
    }


def test_one_coordinate_coverage_failure_fails_v1_or_v2() -> None:
    fit_rows = []
    for H in (2, 4):
        for coordinate in range(5):
            fit_rows.append(
                {
                    "H": H,
                    "coordinate": coordinate,
                    "beta0": 0.0,
                    "beta1": 0.0,
                    "theory_covered_simultaneous": not (H == 2 and coordinate == 4),
                }
            )
    diagnostics = pd.DataFrame(
        [{"setting_id": "s", "coordinate": 0, "validity_pass": True,
          "direct_balance_C_difference_mean": 0.0,
          "direct_balance_C_difference_max_abs": 0.0}]
    )
    settings = pd.DataFrame(
        [{"setting_id": "s", "coordinate": 0,
          "estimator": "stationary_mean_balance", "theory_sign_pass": True}]
    )
    runs = pd.DataFrame(
        {"run_id": [f"r{i}" for i in range(80)],
         "setting_id": [f"s{i // 8}" for i in range(80)]}
    )
    gates = build_falsification_summary(
        "d5", runs, settings, diagnostics, pd.DataFrame(fit_rows)
    ).set_index("gate")
    assert not bool(gates.loc["V1", "passed"])
    assert bool(gates.loc["V2", "passed"])
    assert bool(gates.loc["V5", "passed"])


@pytest.mark.parametrize("mode", ["missing", "unexpected"])
def test_d5_missing_or_unexpected_rows_are_rejected(tmp_path: Path, mode: str) -> None:
    root = tmp_path / "d5"
    _write_synthetic_d5_matrix(root)
    run_path = root / "run_summary.csv"
    frame = pd.read_csv(run_path)
    if mode == "missing":
        frame = frame.iloc[:-1]
    else:
        frame.loc[0, "run_id"] = "unexpected-run"
    frame.to_csv(run_path, index=False)
    with pytest.raises(ValueError, match="completeness failed"):
        validate_saved_formal_matrix("d5", root)


def test_d5_clean_source_and_overwrite_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "formal-output"
    monkeypatch.setattr(formal, "formal_artifact_root", lambda *args: target)
    dirty = {
        "source_commit": "fixture",
        "source_dirty_at_run_start": True,
    }
    monkeypatch.setattr(formal, "_capture_formal_provenance", lambda *args: dirty)
    with pytest.raises(RuntimeError, match="clean committed"):
        formal.run_formal_matrix("d5")
    target.mkdir()
    (target / "sentinel").write_text("preserve")
    clean = dirty | {"source_dirty_at_run_start": False}
    monkeypatch.setattr(formal, "_capture_formal_provenance", lambda *args: clean)
    with pytest.raises(RuntimeError, match="complete current raw output"):
        formal.run_formal_matrix("d5")
    assert (target / "sentinel").read_text() == "preserve"
    with pytest.raises(RuntimeError, match="frozen artifact namespace"):
        formal.validate_formal_output_root(tmp_path / "wrong", target)


def test_d5_gate_failures_are_mechanical() -> None:
    fits = pd.DataFrame(
        [
            {"H": H, "coordinate": coordinate, "beta0": 0.0, "beta1": 0.0,
             "theory_covered_simultaneous": not (H == 4 and coordinate == 2)}
            for H in (2, 4) for coordinate in range(5)
        ]
    )
    diagnostics = pd.DataFrame(
        [{"setting_id": "s", "coordinate": 0, "validity_pass": False,
          "direct_balance_C_difference_mean": 0.0,
          "direct_balance_C_difference_max_abs": 0.0}]
    )
    settings = pd.DataFrame(
        [{"setting_id": "s", "coordinate": 0,
          "estimator": "stationary_mean_balance", "theory_sign_pass": False}]
    )
    runs = pd.DataFrame(
        {"run_id": [f"r{i}" for i in range(79)],
         "setting_id": [f"s{i // 8}" for i in range(79)]}
    )
    gates = build_falsification_summary(
        "d5", runs, settings, diagnostics, fits
    ).set_index("gate")
    assert not bool(gates.loc["V0", "passed"])
    assert bool(gates.loc["V1", "passed"])
    assert not bool(gates.loc["V2", "passed"])
    assert not bool(gates.loc["V5", "passed"])


def test_d5_cli_check_routes_without_scientific_execution(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import stationary_bias.cli as cli

    monkeypatch.setattr(
        formal,
        "run_formal_matrix",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("run called")),
    )
    assert cli.main(["p2", "d5", "check"]) == 0
    assert '"scientific_execution": "NOT_RUN"' in capsys.readouterr().out


def test_d2_regression_check_remains_unchanged() -> None:
    result = formal.check_formal_protocol()
    assert result["status"] == "PASS"
    assert result["primary"]["chains"] == 80
    assert student_t_critical(0.975, 7) == pytest.approx(2.8412442485881835)
