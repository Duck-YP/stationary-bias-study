import json
from pathlib import Path

import stationary_bias.cli as cli
import stationary_bias.workstreams.p2_multidimensional_validation.simulation as p2_simulation


REQUIRED_COORDINATE_COLUMNS = {
    "study",
    "phase",
    "setting_id",
    "run_id",
    "seed",
    "d",
    "coordinate",
    "H",
    "N",
    "gamma",
    "estimator",
    "b_component",
    "B11_d_component",
    "C_component",
    "B20_component",
    "normalized_error_component",
}


def test_p2_check_and_smoke_config_are_frozen() -> None:
    check = p2_simulation.check_p2()
    assert check == {
        "status": "PASS",
        "workstream": "p2",
        "phase": "smoke",
        "setting_id": "d2-controlled-smoke",
        "d": 2,
        "H": 2,
        "N": 4,
        "gamma": 0.05,
        "seeds": [801, 802, 803],
        "chains": 3,
        "batches": 4,
        "lyapunov_residual": check["lyapunov_residual"],
    }
    assert check["lyapunov_residual"] <= 1.0e-12


def test_p2_simulation_is_reproducible_and_coordinate_normalized() -> None:
    first = p2_simulation.simulate_p2_smoke()
    second = p2_simulation.simulate_p2_smoke()
    assert first["run_rows"] == second["run_rows"]
    assert first["batch_rows"] == second["batch_rows"]
    assert first["diagnostic_rows"] == second["diagnostic_rows"]
    assert len(first["run_rows"]) == 12
    assert len(first["batch_rows"]) == 48
    assert len(first["diagnostic_rows"]) == 3
    assert REQUIRED_COORDINATE_COLUMNS <= set(first["run_rows"][0])
    assert {row["estimator"] for row in first["run_rows"]} == {
        "direct_sample_mean",
        "stationary_mean_balance",
    }
    assert all(row["finite_state_pass"] for row in first["diagnostic_rows"])
    assert max(
        row["zero_sum_control_error"] for row in first["diagnostic_rows"]
    ) <= 1.0e-10


def test_p2_smoke_artifacts_are_isolated_and_reproducible(tmp_path: Path) -> None:
    first_root = tmp_path / "workstreams" / "p2_multidimensional_validation" / "artifacts" / "smoke-a"
    second_root = tmp_path / "workstreams" / "p2_multidimensional_validation" / "artifacts" / "smoke-b"
    first = p2_simulation.run_p2_smoke(first_root)
    second = p2_simulation.run_p2_smoke(second_root)
    names = {
        "run_summary.csv",
        "batch_summary.csv",
        "diagnostic_summary.csv",
        "p2_smoke_manifest.json",
    }
    assert {path.name for path in first_root.iterdir()} == names
    assert {path.name for path in second_root.iterdir()} == names
    for name in names:
        assert (first_root / name).read_bytes() == (second_root / name).read_bytes()
    manifest = json.loads(first["manifest"].read_text(encoding="utf-8"))
    assert manifest["scientific_interpretation"] == "NOT_APPLICABLE_ENGINEERING_SMOKE"
    assert manifest["rows"] == {
        "coordinate_runs": 12,
        "coordinate_batches": 48,
        "chain_diagnostics": 3,
    }
    assert "p0_scaffold_bias" not in str(first["output_root"])
    assert "p1_matched_fedavg" not in str(first["output_root"])


def test_p2_cli_check_and_smoke_routes(capsys, monkeypatch) -> None:
    assert cli.main(["p2", "check"]) == 0
    check_output = json.loads(capsys.readouterr().out)
    assert check_output["status"] == "PASS"

    fake_root = Path("p2-smoke-output")
    monkeypatch.setattr(
        p2_simulation,
        "run_p2_smoke",
        lambda: {
            "run_rows": [{}] * 12,
            "batch_rows": [{}] * 48,
            "diagnostic_rows": [{"finite_state_pass": True}] * 3,
            "output_root": fake_root,
            "manifest": fake_root / "p2_smoke_manifest.json",
        },
    )
    assert cli.main(["p2", "smoke"]) == 0
    smoke_output = json.loads(capsys.readouterr().out)
    assert smoke_output["status"] == "PASS"
    assert smoke_output["scientific_interpretation"] == "NOT_APPLICABLE_ENGINEERING_SMOKE"
