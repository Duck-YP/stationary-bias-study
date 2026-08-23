from pathlib import Path

import numpy as np
import pandas as pd

import stationary_bias.small_step_confirmation as small_step_confirmation
from stationary_bias.small_step_confirmation import (
    ORIGINAL_STUDY_REPORT,
    CONFIRMATION_RESULT_ROOT,
    audit_confirmation_matrix,
    adjudicate,
    build_confirmation_matrix,
    error_to_theory,
    original_report_sha256,
    load_confirmation_config,
    scaled_error,
    write_report_file,
)
from stationary_bias.theoretical_bias import b20_total


def test_p3a2_matrix_exactly_32_runs() -> None:
    audit = audit_confirmation_matrix(build_confirmation_matrix())
    assert audit["actual_runs"] == 32
    assert audit["unique_run_keys"] == 32
    assert audit["settings"] == 4
    assert audit["all_unique"] is True


def test_p3a2_fresh_seeds() -> None:
    runs = build_confirmation_matrix()
    seeds = {run.seed for run in runs}
    assert seeds == set(range(201, 209))
    assert seeds.isdisjoint(set(range(101, 109)))


def test_p3a2_theory_target_H4() -> None:
    assert b20_total(4) == -0.59375
    assert {run.H for run in build_confirmation_matrix()} == {4}


def test_p3a2_error_definition() -> None:
    C = np.array([-0.59, -0.60])
    np.testing.assert_array_equal(error_to_theory(C, -0.59375), C + 0.59375)


def test_p3a2_scaled_error_definition() -> None:
    C = -0.59
    gamma = 1.0 / 64.0
    assert scaled_error(C, -0.59375, gamma) == (C + 0.59375) / gamma


def test_p3a2_does_not_overwrite_original_p3(tmp_path: Path, monkeypatch) -> None:
    original_report = tmp_path / "original" / "final_report.md"
    original_report.parent.mkdir(parents=True)
    original_report.write_text(
        "P3A_STATUS = CONTRADICTION_CANDIDATE\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(small_step_confirmation, "ORIGINAL_P3_REPORT", original_report)

    before = original_report_sha256()
    output = write_report_file("isolated P3-A2 test\n", tmp_path / "p3a2")
    after = original_report_sha256()
    assert output != original_report
    assert CONFIRMATION_RESULT_ROOT != ORIGINAL_STUDY_REPORT.parent
    assert before == after
    assert "P3A_STATUS = CONTRADICTION_CANDIDATE" in original_report.read_text(encoding="utf-8")


def _synthetic_settings(errors: list[float], *, ci_half: float = 1.0e-4) -> pd.DataFrame:
    gammas = np.array([1 / 64, 1 / 96, 1 / 128, 1 / 192], dtype=float)
    B = -0.59375
    error_array = np.asarray(errors)
    return pd.DataFrame(
        {
            "gamma": gammas,
            "N": [64, 96, 128, 192],
            "B_theory": B,
            "error_to_theory": error_array,
            "error_ci_low": error_array - ci_half,
            "error_ci_high": error_array + ci_half,
            "C_se": ci_half / 2.36462425159,
            "scaled_error": error_array / gammas,
            "scaled_error_ci_low": (error_array - ci_half) / gammas,
            "scaled_error_ci_high": (error_array + ci_half) / gammas,
            "finite_state_status": "pass",
            "control_invariant_status": "pass",
            "estimator_agreement_status": "pass",
            "stationarity_status": "pass",
            "precision_status": "reached",
        }
    )


def test_p3a2_consistent_gate_logic() -> None:
    gammas = np.array([1 / 64, 1 / 96, 1 / 128, 1 / 192], dtype=float)
    _, statuses = adjudicate(_synthetic_settings(list(0.8 * gammas)), load_confirmation_config())
    assert statuses["directional_convergence"] == "PASS"
    assert statuses["smallest_step_proximity"] == "PASS"
    assert statuses["O_gamma_compatibility"] == "PASS"
    assert statuses["P3A2_STATUS"] == "CONSISTENT_WITH_ASYMPTOTIC_COEFFICIENT"


def test_p3a2_persistent_discrepancy_gate_logic() -> None:
    _, statuses = adjudicate(
        _synthetic_settings([0.02, 0.025, 0.03, 0.035]), load_confirmation_config()
    )
    assert statuses["directional_convergence"] == "FAIL"
    assert statuses["smallest_step_proximity"] == "FAIL"
    assert statuses["P3A2_STATUS"] == "PERSISTENT_DISCREPANCY"
    assert statuses["TRIGGER_H4_THEOREM_REAUDIT"] == "YES"


def test_p3a2_near_zero_scaled_error_is_not_failed() -> None:
    settings = _synthetic_settings([0.01, 0.007, 0.004, 0.00001], ci_half=0.0001)
    _, statuses = adjudicate(settings, load_confirmation_config())
    assert statuses["O_gamma_compatibility"] == "INCONCLUSIVE_NEAR_ZERO"
