from pathlib import Path

import numpy as np
import pandas as pd
import stationary_bias.workstreams.p1_matched_fedavg.plateau as plateau
import stationary_bias.workstreams.p1_matched_fedavg.simulation as simulation
from stationary_bias.core.inference.statistics import student_t_summary
from stationary_bias.core.theory.one_dimensional import b20_total
from stationary_bias.workstreams.p1_matched_fedavg.analysis import (
    build_pair_setting_summary,
)
from stationary_bias.workstreams.p1_matched_fedavg.theory import (
    b20_fedavg,
    delta_b20_scaffold_minus_fedavg,
)


def test_plateau_formal_matrix_is_exact() -> None:
    runs = plateau.build_plateau_run_matrix()
    assert plateau.audit_plateau_run_matrix(runs) == plateau.expected_plateau_audit()
    assert {(run.H, run.gamma) for run in runs} == {(2, 1.0 / 24.0)}
    assert {run.N for run in runs} == {8, 16, 32, 64, 128}
    assert len(runs) == 5 * 8 == 40
    for N in (8, 16, 32, 64, 128):
        setting = [run for run in runs if run.N == N]
        assert len(setting) == 8
        assert {run.seed for run in setting} == set(range(601, 609))


def test_plateau_theory_constants_are_fixed() -> None:
    config = plateau.load_plateau_config()
    theory = config["theory"]
    assert b20_fedavg(2) == float(theory["B20_fedavg"]) == -0.125
    assert b20_total(2) == float(theory["B20_scaffold"]) == -0.1875
    assert (
        delta_b20_scaffold_minus_fedavg(2)
        == float(theory["Delta_B20_scaffold_minus_fedavg"])
        == -0.0625
    )


def test_plateau_uses_common_noise_object(monkeypatch) -> None:
    captured: list[tuple[str, np.ndarray]] = []
    scaffold_original = simulation.scaffold_round_many
    fedavg_original = simulation.fedavg_round_many

    def capture_scaffold(*args, **kwargs):
        captured.append(("scaffold", kwargs["epsilon_steps"]))
        return scaffold_original(*args, **kwargs)

    def capture_fedavg(*args, **kwargs):
        captured.append(("fedavg", kwargs["epsilon_steps"]))
        return fedavg_original(*args, **kwargs)

    monkeypatch.setattr(simulation, "scaffold_round_many", capture_scaffold)
    monkeypatch.setattr(simulation, "fedavg_round_many", capture_fedavg)
    simulation._advance_matched_block(
        np.array([-1.0, 1.0]),
        np.zeros((2, 8)),
        np.array([-1.0, 1.0]),
        [np.random.default_rng(601), np.random.default_rng(602)],
        rounds=2,
        gamma=1.0 / 24.0,
        H=2,
        N=8,
        objective_name="nonlinear_main",
        noise_name="rademacher",
        collect=True,
    )
    for index in range(0, len(captured), 2):
        assert captured[index][0] == "scaffold"
        assert captured[index + 1][0] == "fedavg"
        assert captured[index][1] is captured[index + 1][1]


def test_plateau_delta_summary_is_pair_level() -> None:
    delta = np.array([-0.07, -0.06, -0.05, -0.04, -0.08, -0.03, -0.06, -0.05])
    fedavg = np.arange(8, dtype=float) * 10.0
    frame = pd.DataFrame(
        {
            "pair_id": [f"pair-{seed}" for seed in range(8)],
            "seed": range(8),
            "grid_name": "fixed_gamma_large_n",
            "H": 2,
            "N": 128,
            "gamma": 1.0 / 24.0,
            "C_scaffold": fedavg + delta,
            "C_fedavg": fedavg,
            "Delta_C": delta,
            "Delta_B20_target": -0.0625,
            "pair_gate_pass": True,
        }
    )
    observed = build_pair_setting_summary(frame).iloc[0]
    expected = student_t_summary(delta)
    assert observed["Delta_C_mean"] == expected.mean
    assert observed["Delta_C_ci_low"] == expected.ci_low
    assert observed["Delta_C_ci_high"] == expected.ci_high


def test_plateau_formal_runner_uses_controlled_output(tmp_path: Path, monkeypatch) -> None:
    formal = tmp_path / "plateau-formal"
    formal.mkdir()
    marker = formal / "plateau_manifest.json"
    marker.write_bytes(b"preserve-me")
    monkeypatch.setattr(plateau, "PLATEAU_RESULT_ROOT", formal)
    captured: dict = {}

    def fake_controlled_run(*args, **kwargs):
        captured.update(kwargs)
        return {"output_root": kwargs["target_root"]}

    monkeypatch.setattr(plateau, "_run_controlled_formal_matrix", fake_controlled_run)
    result = plateau.run_plateau_experiment()

    assert captured["target_root"] == formal
    assert result["output_root"] == formal
    assert marker.read_bytes() == b"preserve-me"
