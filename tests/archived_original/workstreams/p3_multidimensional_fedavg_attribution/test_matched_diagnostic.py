import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stationary_bias import cli
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.artifact_audit import (
    audit_saved_p3_artifacts,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_diagnostic import (
    DIAGNOSTIC_ROOT,
    PROTECTED_OUTPUT_SHA256,
    _validate_diagnostic_overwrite,
    _load_h4_rows,
    build_model_comparison,
    build_nested_window_summary,
    build_pointwise_diagnostics,
    classify_diagnostic,
    coordinate_equivariance_audit,
    fixed_seed_reference_audit,
    rebuild_h4_diagnostic,
)


def _saved() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, _ = _load_h4_rows()
    return rows, build_pointwise_diagnostics(rows)


def test_saved_pointwise_estimator_and_residual_identities_are_exact() -> None:
    _, pointwise = _saved()
    assert len(pointwise) == 18
    for column in (
        "D_identity_error",
        "residual_identity_error",
        "bias_difference_normalization_error",
        "scaffold_normalization_error",
        "fedavg_normalization_error",
        "delta_identity_error",
        "gamma_inverse_N_error",
    ):
        assert pointwise[column].abs().max() <= 1.0e-12
    np.testing.assert_allclose(
        pointwise["e_Delta"],
        pointwise["e_SCAF"] - pointwise["e_FA"],
        rtol=0.0,
        atol=1.0e-12,
    )


def test_pointwise_audit_stops_on_misaligned_paired_estimator() -> None:
    rows, _ = _load_h4_rows()
    corrupted = rows.copy()
    corrupted.loc[corrupted.index[0], "paired_primary_difference"] += 1.0e-5
    with pytest.raises(RuntimeError, match="identity audit failed"):
        build_pointwise_diagnostics(corrupted)


def test_nested_windows_are_deterministic_complete_suffixes() -> None:
    rows, pointwise = _saved()
    first = build_nested_window_summary(rows, pointwise)
    second = build_nested_window_summary(rows, pointwise)
    pd.testing.assert_frame_equal(first, second)
    for (source, coordinate), group in first.groupby(["source", "coordinate"]):
        expected_count = 2 if source == "smaller_step" else 7
        assert len(group) == expected_count
        ordered = group.sort_values("drop_count")
        assert ordered["drop_count"].tolist() == list(range(expected_count))
        assert ordered["point_count"].tolist() == list(
            range(expected_count + 2, 2, -1)
        )
        assert ordered["max_delta"].is_monotonic_decreasing


def test_quadratic_results_remain_explicitly_post_hoc_and_warn_when_unstable() -> None:
    rows, pointwise = _saved()
    models = build_model_comparison(rows, pointwise)
    assert set(models["model"]) == {"linear", "quadratic"}
    assert models["interpretation"].eq(
        "POST_HOC_DIAGNOSTIC_ONLY_DOES_NOT_REDEFINE_GATE"
    ).all()


def test_descriptive_classification_is_computed_from_observations() -> None:
    rows, pointwise = _saved()
    from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_diagnostic import (
        build_implementation_audit,
        build_scaling_summary,
    )

    scaling = build_scaling_summary(pointwise)
    nested = build_nested_window_summary(rows, pointwise)
    models = build_model_comparison(rows, pointwise)
    reference, _ = fixed_seed_reference_audit()
    equivariance = coordinate_equivariance_audit()
    audit = build_implementation_audit(rows, pointwise, reference, equivariance)
    observed = classify_diagnostic(scaling, nested, models, audit)
    assert observed["label"] == "finite_grid_higher_order_curvature_consistent"
    changed = scaling.copy()
    changed.loc[changed.index[0], "abs_e_Delta_monotone_with_delta"] = False
    assert classify_diagnostic(changed, nested, models, audit)["label"] == "unresolved"
    smaller_quadratic = models[
        (models["source"] == "smaller_step") & (models["model"] == "quadratic")
    ]
    assert smaller_quadratic["stability_warning"].eq(
        "LOW_DF_OR_HIGH_CONDITION_INTERPRET_CAUTIOUSLY"
    ).all()


def test_reference_kernel_noise_controls_and_coordinate_equivariance_pass() -> None:
    reference, trace = fixed_seed_reference_audit()
    equivariance = coordinate_equivariance_audit()
    assert reference["status"] == "PASS"
    assert reference["max_residual"] <= 1.0e-12
    assert len(trace) == 3 * 4 * 12 * 2
    assert equivariance["status"] == "PASS"
    assert equivariance["max_residual"] <= 1.0e-10


def test_diagnostic_tables_and_fits_regenerate_deterministically(tmp_path: Path) -> None:
    first = rebuild_h4_diagnostic(tmp_path / "first")
    second = rebuild_h4_diagnostic(tmp_path / "second")
    for name in (
        "pointwise_diagnostics",
        "scaling_summary",
        "nested_window_linear_summary",
        "linear_quadratic_comparison",
        "same_pair_attribution",
        "implementation_audit",
        "fixed_seed_reference_trace",
    ):
        pd.testing.assert_frame_equal(first[name], second[name])
    manifest = json.loads(
        (tmp_path / "first" / "diagnostic_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["historical_gate_status"]["H4_primary"] == "FAIL_RETAINED"
    assert manifest["classification"]["label"] == (
        "finite_grid_higher_order_curvature_consistent"
    )
    for name, expected_hash in PROTECTED_OUTPUT_SHA256.items():
        first_bytes = (tmp_path / "first" / name).read_bytes()
        second_bytes = (tmp_path / "second" / name).read_bytes()
        assert first_bytes == second_bytes
        assert hashlib.sha256(first_bytes).hexdigest() == expected_hash
    report = (tmp_path / "first" / "p3_h4_paired_diagnostic_report.md").read_text(
        encoding="utf-8"
    )
    assert "Descriptive classification" in report
    assert "Next action" not in report
    assert "Repository discovery record" not in report
    assert "this ticket" not in report


def test_controlled_overwrite_rejects_changed_protected_output(tmp_path: Path) -> None:
    staged = tmp_path / "staged"
    current = tmp_path / "current"
    staged.mkdir()
    current.mkdir()
    for name in PROTECTED_OUTPUT_SHA256:
        shutil.copyfile(DIAGNOSTIC_ROOT / name, staged / name)
        shutil.copyfile(DIAGNOSTIC_ROOT / name, current / name)
    assert _validate_diagnostic_overwrite(staged, current)[
        "protected_outputs_match"
    ]
    (current / "pointwise_diagnostics.csv").write_bytes(b"changed\n")
    with pytest.raises(RuntimeError, match="changed protected numerical data"):
        _validate_diagnostic_overwrite(staged, current)


def test_p3_artifact_audit_covers_diagnostic_provenance_and_hashes() -> None:
    diagnostic = audit_saved_p3_artifacts()["matrices"][
        "matched_attribution_h4_diagnostic"
    ]
    assert diagnostic["present"] is True
    assert diagnostic["protected_outputs_verified"] is True
    assert diagnostic["source_snapshot_verified"] is True
    assert diagnostic["artifact_count"] == 14


def test_diagnostic_cli_is_registered(monkeypatch, tmp_path: Path, capsys) -> None:
    from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution import (
        matched_diagnostic,
    )

    monkeypatch.setattr(matched_diagnostic, "DIAGNOSTIC_ROOT", tmp_path / "diagnostic")
    assert cli.main(["p3", "matched-attribution", "diagnostic"]) == 0
    assert '"new_production_simulation": false' in capsys.readouterr().out
