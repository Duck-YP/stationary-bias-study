import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import stationary_bias.cli as cli
import stationary_bias.workstreams.p2_multidimensional_validation.formal as formal
from stationary_bias.workstreams.p2_multidimensional_validation.formal_analysis import (
    analyze_formal_saved,
    build_falsification_summary,
    build_formal_report_and_plots,
    validate_saved_formal_matrix,
)
from stationary_bias.workstreams.p2_multidimensional_validation.formal_inference import (
    coordinate_interval,
    evaluate_vector_precision,
    fit_delta_line,
    seed_block_bootstrap,
    student_t_critical,
)
from stationary_bias.workstreams.p2_multidimensional_validation.theory import (
    vector_theory_targets,
)


def test_formal_config_loaders_and_exact_matrices() -> None:
    check = formal.check_formal_protocol()
    assert check["status"] == "PASS"
    assert check["primary"]["settings"] == 10
    assert check["primary"]["chains"] == 80
    assert check["primary"]["seeds"] == list(range(901, 909))
    assert check["h4_small_step"]["settings"] == 4
    assert check["h4_small_step"]["chains"] == 32
    assert check["h4_small_step"]["seeds"] == list(range(1001, 1009))
    assert check["bootstrap"] == {
        "primary_seed": 2901,
        "h4_small_step_seed": 2902,
        "repetitions": 2000,
    }
    for target in formal.FORMAL_TARGETS:
        runs = formal.build_formal_run_matrix(target)
        assert len({item.run_id for item in runs}) == len(runs)
        assert all(item.gamma == 1.0 / item.N for item in runs)


def test_theory_and_noncommuting_config_integrity() -> None:
    config = formal.load_formal_config("primary")
    objective = formal.objective_from_formal_config(config)
    covariance = formal.covariance_from_formal_config(config)
    assert np.min(np.linalg.eigvalsh(covariance)) > 0.0
    assert not np.allclose(objective.A @ covariance, covariance @ objective.A)
    for H in (2, 4):
        targets = vector_theory_targets(objective, covariance, H)
        expected = config["theory"]["by_H"][H]
        np.testing.assert_allclose(targets.S_C, config["theory"]["S_C"], atol=1e-14)
        np.testing.assert_allclose(targets.B11_d, config["theory"]["B11_d"], atol=1e-14)
        np.testing.assert_allclose(targets.B20, expected["B20"], atol=1e-14)
        np.testing.assert_allclose(
            targets.B20_local + targets.B20_ctrl, targets.B20, atol=1e-15
        )


def test_formal_ids_are_stable_and_encode_frozen_identity() -> None:
    first = formal.build_formal_run_matrix("primary")
    second = formal.build_formal_run_matrix("primary")
    assert [item.run_id for item in first] == [item.run_id for item in second]
    sample = first[0]
    assert "p2__phase-formal" in sample.run_id
    assert f"__H{sample.H}__N{sample.N}" in sample.run_id
    assert f"__seed{sample.seed}" in sample.run_id


def test_mixing_burn_in_and_batch_formulas() -> None:
    config = formal.load_formal_config("primary")
    spec = formal.build_formal_run_matrix("primary", config)[0]
    dimensions = formal.formal_protocol_dimensions(spec, config)
    expected_mixing = int(np.ceil(1.0 / (0.85 * spec.H * spec.gamma)))
    assert dimensions == {
        "mixing_scale": expected_mixing,
        "burn_in_rounds": 100 * expected_mixing,
        "batch_length": 20 * expected_mixing,
        "min_batches": 100,
        "max_batches": 400,
        "extension_batches": 50,
    }


def test_bonferroni_student_t_interval_is_exact() -> None:
    values = np.arange(8, dtype=float)
    summary = coordinate_interval(values, confidence_level=0.975)
    expected_se = np.std(values, ddof=1) / np.sqrt(8)
    assert summary.degrees_of_freedom == 7
    assert summary.confidence_level == 0.975
    assert student_t_critical(0.975, 7) == pytest.approx(2.8412442485881835)
    assert summary.half_width == pytest.approx(
        2.8412442485881835 * expected_se
    )
    marginal = coordinate_interval(values, confidence_level=0.95)
    assert marginal.half_width == pytest.approx(2.3646242515927844 * expected_se)


def test_vector_precision_requires_both_coordinates() -> None:
    target = np.array([-0.05, -0.20])
    passing = np.tile(target, (8, 1))
    result = evaluate_vector_precision(passing, target)
    np.testing.assert_allclose(result["thresholds"], [0.005, 0.02])
    assert result["joint_pass"] is True
    failing = passing.copy()
    failing[:, 1] += np.linspace(-0.1, 0.1, 8)
    result = evaluate_vector_precision(failing, target)
    assert result["coordinate_pass"].tolist() == [True, False]
    assert result["joint_pass"] is False


def test_delta_ols_recovers_known_line_and_uses_every_setting() -> None:
    delta = np.array([0.02, 0.03, 0.05, 0.08, 0.12])
    values = -0.125 + 0.75 * delta
    fit = fit_delta_line(delta, values)
    assert fit.beta0 == pytest.approx(-0.125)
    assert fit.beta1 == pytest.approx(0.75)
    assert fit.fitted.shape == delta.shape
    np.testing.assert_allclose(fit.residuals, 0.0, atol=1e-15)


def test_seed_block_bootstrap_is_deterministic_and_cross_setting() -> None:
    delta = np.array([0.02, 0.04, 0.08])
    labels = np.arange(901, 909)
    values = np.empty((3, 8, 2))
    for setting in range(3):
        for seed in range(8):
            values[setting, seed] = [
                -0.05 + delta[setting] + seed / 1000,
                -0.10 - 2 * delta[setting] - seed / 2000,
            ]
    first = seed_block_bootstrap(
        delta, values, labels, repetitions=2000, bootstrap_seed=2901
    )
    second = seed_block_bootstrap(
        delta, values, labels, repetitions=2000, bootstrap_seed=2901
    )
    assert first["intercepts"].shape == (2000, 2)
    assert first["sampled_indices"].shape == (2000, 8)
    np.testing.assert_array_equal(first["sampled_indices"], second["sampled_indices"])
    np.testing.assert_array_equal(first["intercepts"], second["intercepts"])
    # One sampled index vector, rather than separate setting-level draws, is exposed per replicate.
    assert first["sampled_indices"].ndim == 2
    quantiles = np.quantile(first["intercepts"], [0.0125, 0.9875], axis=0)
    assert quantiles.shape == (2, 2)


def _synthetic_saved_matrix(root: Path, target: str) -> None:
    root.mkdir(parents=True)
    config = formal.load_formal_config(target)
    specs = formal.build_formal_run_matrix(target, config)
    objective = formal.objective_from_formal_config(config)
    covariance = formal.covariance_from_formal_config(config)
    effects = dict(zip(config["chains"]["seeds"], np.linspace(-0.007, 0.007, 8), strict=True))
    run_rows = []
    batch_rows = []
    for spec in specs:
        targets = vector_theory_targets(objective, covariance, spec.H)
        for estimator in ("direct_sample_mean", "stationary_mean_balance"):
            for coordinate in range(spec.d):
                C_value = (
                    float(targets.B20[coordinate])
                    + (coordinate + 1) * 0.2 * spec.delta
                    + effects[spec.seed]
                    + (0.0005 if estimator == "direct_sample_mean" else 0.0)
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
                    "mixing_scale": 1,
                    "burn_in_rounds": 100,
                    "batch_length": 20,
                    "source_commit": "fixture-commit",
                    "source_dirty_at_run_start": False,
                    "config_sha256": hashlib.sha256(
                        formal.formal_config_path(target).read_bytes()
                    ).hexdigest(),
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
    provenance = {
        "schema_version": 2,
        "capture_point": "before_any_p2_formal_output_write",
        "study": "p2_multidimensional_validation",
        "phase": "formal",
        "matrix_id": config["matrix_identifier"],
        "source_commit": "fixture-commit",
        "source_dirty_at_run_start": False,
        "environment": {"python": "3.12.fixture", "packages": {}},
        "config_path": str(formal.formal_config_path(target)),
        "config_sha256": hashlib.sha256(
            formal.formal_config_path(target).read_bytes()
        ).hexdigest(),
        "protocol_path": str(formal.P2_FORMAL_PROTOCOL_PATH),
        "protocol_sha256": hashlib.sha256(
            formal.P2_FORMAL_PROTOCOL_PATH.read_bytes()
        ).hexdigest(),
        "seeds": list(config["chains"]["seeds"]),
        "bootstrap_seed": config["bootstrap"]["seed"],
        "bootstrap_repetitions": config["bootstrap"]["repetitions"],
        "run_matrix": formal.audit_formal_run_matrix(target, specs),
        "expected_chain_count": len(specs),
        "planned_coordinate_run_rows": len(run_rows),
        "artifact_namespace": config["artifact_namespace"],
    }
    (root / formal.P2_RUN_START_PROVENANCE).write_text(
        json.dumps(provenance), encoding="utf-8"
    )


def test_saved_fixture_analysis_report_and_plots_do_not_simulate(
    tmp_path: Path, monkeypatch
) -> None:
    primary = tmp_path / "primary"
    _synthetic_saved_matrix(primary, "primary")
    raw = pd.read_csv(primary / "run_summary.csv")
    batches = pd.read_csv(primary / "batch_summary.csv")
    assert {
        "matrix_id",
        "setting_id",
        "run_id",
        "coordinate",
        "delta",
        "estimator",
        "b_component",
        "B11_d_component",
        "C_component",
        "B20_component",
        "batches_used",
        "stopping_reason",
        "validity_pass",
    } <= set(raw.columns)
    assert "batch_index" in batches.columns
    analyzed = analyze_formal_saved("primary", primary)
    assert len(analyzed["setting_summary"]) == 40
    assert len(analyzed["fit_summary"]) == 20
    assert len(analyzed["bootstrap_intercepts"]) == 8000
    assert set(analyzed["falsification_summary"]["gate"]) == {
        "F0",
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
    }
    manifest = json.loads(analyzed["manifest"].read_text(encoding="utf-8"))
    assert {
        "source_commit",
        "config_sha256",
        "protocol_sha256",
        "formal_seed_group",
        "bootstrap_seed",
        "bootstrap_replicate_count",
        "objective_parameters",
        "covariance_C",
        "theory_targets",
        "run_matrix",
        "observed_row_counts",
        "stopping_protocol",
        "uncertainty_protocol",
        "fit_model",
        "artifact_filenames",
        "interpretation_boundary",
    } <= set(manifest)
    monkeypatch.setattr(
        formal,
        "simulate_formal_setting",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("report invoked simulator")
        ),
    )
    outputs = build_formal_report_and_plots("primary", primary)
    assert outputs["report"].name == "p2_d2_coefficient_primary_report.md"
    assert "EMPIRICAL" in outputs["report"].read_text(encoding="utf-8")
    assert {path.name for path in outputs["figures"]} == {
        "p2_d2_H2_coefficient_convergence.png",
        "p2_d2_H4_coefficient_convergence.png",
    }
    assert all(path.stat().st_size > 0 for path in outputs["figures"])


def test_confirmation_fixture_implements_F3_and_F4(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    confirmation = tmp_path / "confirmation"
    _synthetic_saved_matrix(primary, "primary")
    _synthetic_saved_matrix(confirmation, "h4-small-step")
    analyze_formal_saved("primary", primary)
    analyzed = analyze_formal_saved(
        "h4-small-step", confirmation, primary_output_root=primary
    )
    gates = analyzed["falsification_summary"]
    assert len(gates[gates["gate"] == "F3"]) == 2
    assert len(gates[gates["gate"] == "F4"]) == 8
    outputs = build_formal_report_and_plots("h4-small-step", confirmation)
    assert outputs["report"].name == "p2_d2_h4_small_step_report.md"
    assert [path.name for path in outputs["figures"]] == [
        "p2_d2_H4_small_step_confirmation.png"
    ]


def test_F6_missing_row_fails_instead_of_filtering(tmp_path: Path) -> None:
    root = tmp_path / "primary"
    _synthetic_saved_matrix(root, "primary")
    frame = pd.read_csv(root / "run_summary.csv")
    frame.iloc[:-1].to_csv(root / "run_summary.csv", index=False)
    with pytest.raises(ValueError, match="F6 frozen matrix completeness failed"):
        validate_saved_formal_matrix("primary", root)


def test_F0_through_F5_have_mechanical_pass_and_fail_cases() -> None:
    diagnostics = pd.DataFrame(
        [
            {
                "setting_id": "setting",
                "coordinate": 0,
                "validity_pass": True,
                "direct_balance_C_difference_mean": 0.01,
                "direct_balance_C_difference_max_abs": 0.02,
            }
        ]
    )
    primary_fits = pd.DataFrame(
        [
            {
                "H": H,
                "coordinate": coordinate,
                "beta0": -0.1 * (coordinate + 1),
                "beta1": 0.0,
                "B20_component": -0.1 * (coordinate + 1),
                "theory_covered_simultaneous": not (H == 2 and coordinate == 1),
            }
            for H in (2, 4)
            for coordinate in (0, 1)
        ]
    )
    primary = build_falsification_summary(
        "primary",
        pd.DataFrame(),
        pd.DataFrame(),
        diagnostics,
        primary_fits,
    )
    assert primary[primary["gate"] == "F0"]["passed"].tolist() == [True]
    assert primary[primary["gate"] == "F1"]["passed"].tolist() == [True, False]
    assert primary[primary["gate"] == "F2"]["passed"].tolist() == [True, True]
    assert set(primary["gate"]) >= {"F0", "F1", "F2", "F3", "F4", "F5", "F6"}

    confirmation_fits = primary_fits[primary_fits["H"] == 4].copy()
    confirmation_fits.loc[confirmation_fits["coordinate"] == 1, "theory_covered_simultaneous"] = False
    confirmation_settings = pd.DataFrame(
        [
            {
                "setting_id": "small",
                "estimator": "stationary_mean_balance",
                "H": 4,
                "coordinate": 0,
                "theory_sign_pass": True,
            },
            {
                "setting_id": "small",
                "estimator": "stationary_mean_balance",
                "H": 4,
                "coordinate": 1,
                "theory_sign_pass": False,
            },
        ]
    )
    confirmation = build_falsification_summary(
        "h4-small-step",
        pd.DataFrame(),
        confirmation_settings,
        diagnostics.assign(validity_pass=False),
        confirmation_fits,
        primary_fit_summary=primary_fits,
    )
    assert confirmation[confirmation["gate"] == "F0"]["passed"].tolist() == [False]
    assert confirmation[confirmation["gate"] == "F3"]["passed"].tolist() == [True, False]
    assert confirmation[confirmation["gate"] == "F4"]["passed"].tolist() == [True, False]
    assert confirmation[confirmation["gate"] == "F5"]["passed"].tolist() == [""]


def test_formal_write_guards_refuse_dirty_existing_and_other_workstreams(
    tmp_path: Path, monkeypatch
) -> None:
    target = (
        tmp_path
        / "workstreams"
        / "p2_multidimensional_validation"
        / "artifacts"
        / "formal"
        / "p2-d2-coefficient-primary"
    )
    monkeypatch.setattr(formal, "formal_artifact_root", lambda *args, **kwargs: target)
    monkeypatch.setattr(
        formal,
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
        formal.run_formal_matrix("primary")
    assert not target.exists()

    monkeypatch.setattr(
        formal,
        "environment_manifest",
        lambda: {
            "python": "3.12.fixture",
            "platform": "fixture",
            "packages": {},
            "git_commit": "fixture-commit",
            "git_dirty": False,
        },
    )
    target.mkdir(parents=True)
    (target / "formal_manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="complete current raw output"):
        formal.run_formal_matrix("primary")

    p0 = tmp_path / "workstreams" / "p0_scaffold_bias" / "artifacts" / "formal"
    with pytest.raises(RuntimeError, match="another workstream namespace"):
        formal.validate_formal_output_root(p0, p0)


def test_formal_cli_routes_without_running_scientific_matrix(
    capsys, monkeypatch
) -> None:
    assert cli.main(["p2", "formal", "check"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"

    monkeypatch.setattr(
        formal,
        "run_formal_matrix",
        lambda target: {
            "output_root": Path(f"fixture-{target}"),
            "run_rows": [],
            "batch_rows": [],
            "report": Path(f"fixture-{target}/report.md"),
            "figures": [],
            "overwrite_audit": {
                "previous_output": "absent",
                "scientific_results_match": None,
                "compared_files": [],
            },
        },
    )
    assert cli.main(["p2", "formal", "primary", "run"]) == 0
    assert json.loads(capsys.readouterr().out)["run_rows"] == 0
