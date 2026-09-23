import json
from pathlib import Path

import pandas as pd
import pytest

from stationary_bias import cli
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution import matched_formal
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.artifact_audit import (
    audit_saved_p3_artifacts,
)
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.matched_simulation import (
    MATCHED_SMOKE_ARTIFACT_ROOT,
    run_matched_smoke,
    simulate_p3_smoke,
)


def test_matched_formal_matrices_and_paired_inference_are_frozen() -> None:
    check = matched_formal.check_matched_formal_protocol()
    assert check["status"] == "PASS"
    assert check["component"] == "matched_attribution"
    assert check["primary"]["H_values"] == [2, 4]
    assert check["primary"]["N_values"] == [12, 16, 24, 32, 48]
    assert check["primary"]["seeds"] == list(range(2101, 2109))
    assert check["h4_small_step"]["H_values"] == [4]
    assert check["h4_small_step"]["N_values"] == [64, 96, 128, 192]
    assert check["h4_small_step"]["seeds"] == list(range(2201, 2209))
    assert check["bootstrap"] == {
        "primary_seed": 4901,
        "h4_small_step_seed": 4902,
        "repetitions": 2000,
    }
    primary = matched_formal.load_formal_config("primary")
    assert primary["pairs"]["count_per_setting"] == 8
    assert primary["per_setting_uncertainty"]["degrees_of_freedom"] == 7
    assert primary["bootstrap"]["unit"] == "paired_seed_label_block"


def test_smoke_is_deterministic_and_validates_paired_schema() -> None:
    first = simulate_p3_smoke()
    second = simulate_p3_smoke()
    assert first["run_rows"] == second["run_rows"]
    assert first["batch_rows"] == second["batch_rows"]
    assert len(first["run_rows"]) == 6
    assert all(row["crn_integrity_pass"] for row in first["diagnostic_rows"])
    assert all(row["zero_sum_control_pass"] for row in first["diagnostic_rows"])
    assert all(row["scaffold_control_state_exists"] for row in first["diagnostic_rows"])
    assert not any(row["fedavg_control_state_exists"] for row in first["diagnostic_rows"])
    assert all(row["separate_algorithm_state"] for row in first["diagnostic_rows"])


def test_smoke_artifacts_are_confined_to_matched_namespace(tmp_path: Path) -> None:
    outputs = run_matched_smoke(tmp_path)
    assert MATCHED_SMOKE_ARTIFACT_ROOT.as_posix().endswith(
        "artifacts/smoke/matched-attribution"
    )
    assert {path.name for path in tmp_path.iterdir()} == {
        "paired_run_summary.csv",
        "paired_batch_summary.csv",
        "paired_diagnostic_summary.csv",
        "p3_matched_smoke_manifest.json",
    }
    run = pd.read_csv(tmp_path / "paired_run_summary.csv")
    assert {
        "pair_id", "scaffold_primary_coefficient", "fedavg_primary_coefficient",
        "paired_primary_difference", "paired_cancellation_difference",
    } <= set(run)
    manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
    assert manifest["scientific_interpretation"] == "NOT_APPLICABLE_ENGINEERING_SMOKE"
    assert manifest["crn_design"] == "index_keyed_seed_round_client_local_step"


def test_cli_registration_exposes_descriptive_components(capsys) -> None:
    assert cli.main(["p3", "fedavg-coefficient", "formal", "check"]) == 0
    fedavg = json.loads(capsys.readouterr().out)
    assert fedavg["status"] == "PASS"
    assert cli.main(["p3", "matched-attribution", "formal", "check"]) == 0
    matched = json.loads(capsys.readouterr().out)
    assert matched["status"] == "PASS"
    assert matched["component"] == "matched_attribution"


def test_matched_formal_execution_refuses_dirty_source(monkeypatch) -> None:
    monkeypatch.setattr(
        matched_formal,
        "environment_manifest",
        lambda: {
            "python": "fixture", "platform": "fixture", "packages": {},
            "git_commit": "fixture", "git_dirty": True,
        },
    )
    with pytest.raises(RuntimeError, match="clean committed source tree"):
        matched_formal.run_formal_matrix("primary")


def test_saved_p3_artifacts_retain_source_provenance() -> None:
    audit = audit_saved_p3_artifacts()
    assert audit["status"] == "PASS"
    assert len(audit["matrices"]) == 4
    for matrix in audit["matrices"].values():
        assert matrix["source_dirty_at_run_start"] is False
        assert matrix["source_config_verified"] is True
        assert matrix["snapshot_verified"] is True
