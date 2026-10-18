import json

import pandas as pd
import pytest

from stationary_bias import cli
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution import formal
from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.simulation import (
    run_smoke,
    simulate_smoke,
)


def test_formal_protocol_is_exact_and_frozen() -> None:
    check = formal.check_formal_protocol()
    assert check["status"] == "PASS"
    assert check["component"] == "fedavg_coefficient"
    assert check["control_state"] is False
    assert check["primary"]["N_values"] == [12, 16, 24, 32, 48]
    assert check["primary"]["H_values"] == [2, 4]
    assert check["primary"]["seeds"] == list(range(1101, 1109))
    assert check["h4_small_step"]["N_values"] == [64, 96, 128, 192]
    assert check["h4_small_step"]["H_values"] == [4]
    assert check["h4_small_step"]["seeds"] == list(range(1201, 1209))
    assert check["bootstrap"] == {
        "primary_seed": 3901,
        "h4_small_step_seed": 3902,
        "repetitions": 2000,
    }


def test_formal_run_ids_and_initialization_are_stable() -> None:
    first = formal.build_formal_run_matrix("primary")
    second = formal.build_formal_run_matrix("primary")
    assert [item.run_id for item in first] == [item.run_id for item in second]
    assert all(item.gamma == 1.0 / item.N for item in first)
    assert all(item.x0.tolist() == [0.0, 0.0] for item in first)


def test_smoke_simulation_is_deterministic_and_signed_coordinatewise() -> None:
    first = simulate_smoke()
    second = simulate_smoke()
    assert first["run_rows"] == second["run_rows"]
    assert first["batch_rows"] == second["batch_rows"]
    assert len(first["run_rows"]) == 3 * 2 * 2
    assert {row["coordinate"] for row in first["run_rows"]} == {0, 1}
    assert {row["estimator"] for row in first["run_rows"]} == {
        "direct_sample_mean",
        "stationary_mean_balance",
    }
    assert all(row["finite_state_pass"] for row in first["diagnostic_rows"])
    assert all(row["no_control_state"] for row in first["diagnostic_rows"])


def test_smoke_artifact_schema_is_valid(tmp_path) -> None:
    outputs = run_smoke(tmp_path)
    expected = {
        "run_summary.csv",
        "batch_summary.csv",
        "diagnostic_summary.csv",
        "p3_smoke_manifest.json",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    run = pd.read_csv(tmp_path / "run_summary.csv")
    batches = pd.read_csv(tmp_path / "batch_summary.csv")
    diagnostics = pd.read_csv(tmp_path / "diagnostic_summary.csv")
    assert {"coordinate", "C_component", "B11_d_component", "B20_FA_component"} <= set(run)
    assert "batch_index" in batches
    assert "no_control_state" in diagnostics
    assert not any("control" in column.lower() or column == "xi" for column in run.columns)
    manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
    assert manifest["algorithm"] == {"name": "FedAvg", "control_state": False}
    assert manifest["scientific_interpretation"] == "NOT_APPLICABLE_ENGINEERING_SMOKE"


def test_cli_registration_and_checks(capsys) -> None:
    assert cli.main(["list"]) == 0
    listing = json.loads(capsys.readouterr().out)
    assert listing["p3"]["slug"] == "p3_multidimensional_fedavg_attribution"
    assert cli.main(["p3", "fedavg-coefficient", "formal", "check"]) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["status"] == "PASS"
    assert checked["component"] == "fedavg_coefficient"


def test_formal_execution_refuses_dirty_source_without_writing(monkeypatch) -> None:
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
