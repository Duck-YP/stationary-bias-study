import numpy as np
import pytest

import stationary_bias.workstreams.p1_matched_fedavg.simulation as p1_simulation
from stationary_bias.workstreams.p1_matched_fedavg.fedavg import fedavg_round, fedavg_round_many
from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
from stationary_bias.core.io import load_configs
from stationary_bias.core.algorithms.scaffold import scaffold_round_many
from stationary_bias.workstreams.p0_scaffold_bias.simulation import build_run_matrix, matrix_audit
from stationary_bias.core.inference.statistics import balance_round_value


def test_p1_formal_matrix_is_exact_and_original_matrix_stays_frozen() -> None:
    audit = p1_simulation.audit_p1_run_matrix()
    assert audit == {
        "total_pairs": 112,
        "primary_pairs": 80,
        "small_step_h4_pairs": 32,
        "settings": 14,
        "unique_pair_ids": 112,
        "all_unique": True,
        "primary_seeds": list(range(301, 309)),
        "small_step_h4_seeds": list(range(401, 409)),
    }
    assert matrix_audit(build_run_matrix())["total"] == 168


def test_p1_seed_blocks_are_isolated_from_p0() -> None:
    seeds = {run.seed for run in p1_simulation.build_p1_run_matrix()}
    assert seeds.isdisjoint(set(range(101, 109)))
    assert seeds.isdisjoint(set(range(201, 209)))


def test_formal_runner_keeps_archive_outside_controlled_output(tmp_path, monkeypatch) -> None:
    current = tmp_path / "formal"
    archived = tmp_path / "archive"
    archived.mkdir()
    marker = archived / "p1_manifest.json"
    marker.write_bytes(b"preserve-me")
    monkeypatch.setattr(p1_simulation, "P1_RESULT_ROOT", current)
    monkeypatch.setattr(p1_simulation, "P1_ARCHIVED_RESULT_ROOT", archived)
    captured: dict = {}

    def fake_controlled_run(*args, **kwargs):
        captured.update(kwargs)
        return {"output_root": kwargs["target_root"]}

    monkeypatch.setattr(
        p1_simulation, "_run_controlled_formal_matrix", fake_controlled_run
    )
    result = p1_simulation.run_p1_experiment()

    assert captured["target_root"] == current
    assert result["output_root"] == current
    assert marker.read_bytes() == b"preserve-me"
    assert not current.exists()


def test_formal_runner_requires_clean_source_before_creating_output(
    tmp_path, monkeypatch
) -> None:
    config = p1_simulation.load_p1_config()
    runs = p1_simulation.build_p1_run_matrix(config, smoke=True)
    target = tmp_path / "formal"

    monkeypatch.setattr(
        p1_simulation,
        "environment_manifest",
        lambda: {
            "python": "3.test",
            "platform": "test-platform",
            "packages": {},
            "git_commit": "test-commit",
            "git_dirty": True,
        },
    )
    with pytest.raises(RuntimeError, match="clean committed source tree"):
        p1_simulation._run_controlled_formal_matrix(
            runs,
            target_root=target,
            config=config,
            config_path=p1_simulation.P1_CONFIG_PATH,
            matrix_audit=p1_simulation.audit_p1_run_matrix,
            finalize=lambda _: {},
        )

    assert not target.exists()


def _write_controlled_raw_result(root, *, metric: str, commit: str) -> None:
    root.mkdir()
    provenance = {
        "config_sha256": "config-file-hash",
        "config_hash": "resolved-config-hash",
        "experiment_matrix_identifier": "matrix-id",
        "git_commit": commit,
        "source_git_dirty_at_run_start": False,
    }
    p1_simulation.write_json(
        provenance, root / p1_simulation.P1_RUN_START_PROVENANCE
    )
    for name in p1_simulation.P1_RAW_RESULT_FILES:
        (root / name).write_text(
            "metric,git_commit,source_git_dirty_at_run_start\n"
            f"{metric},{commit},False\n",
            encoding="utf-8",
        )


def test_controlled_overwrite_accepts_identical_scientific_results(tmp_path) -> None:
    current = tmp_path / "formal"
    staged = tmp_path / "staged"
    _write_controlled_raw_result(current, metric="1.25", commit="old-commit")
    (current / "stale-derived.txt").write_bytes(b"old")
    _write_controlled_raw_result(staged, metric="1.25", commit="new-commit")
    (staged / "derived.txt").write_bytes(b"new")

    audit = p1_simulation._validate_controlled_overwrite(staged, current)
    p1_simulation._replace_output_directory(staged, current)

    assert audit["scientific_results_match"] is True
    assert (current / "derived.txt").read_bytes() == b"new"
    assert not (current / "stale-derived.txt").exists()
    assert not staged.exists()


def test_controlled_overwrite_rejects_changed_scientific_results(tmp_path) -> None:
    current = tmp_path / "formal"
    staged = tmp_path / "staged"
    _write_controlled_raw_result(current, metric="1.25", commit="old-commit")
    _write_controlled_raw_result(staged, metric="1.50", commit="new-commit")

    with pytest.raises(RuntimeError, match="changed scientific results"):
        p1_simulation._validate_controlled_overwrite(staged, current)

    assert (current / "run_summary.csv").read_text(encoding="utf-8").startswith(
        "metric,"
    )


def test_controlled_formal_run_builds_off_path_then_publishes(tmp_path, monkeypatch) -> None:
    config = p1_simulation.load_p1_config()
    runs = p1_simulation.build_p1_run_matrix(config, smoke=True)
    target = tmp_path / "formal"
    capture_before_staging: list[bool] = []

    def fake_environment_manifest() -> dict:
        capture_before_staging.append(not list(tmp_path.glob(".*.staging-*")))
        return {
            "python": "3.test",
            "platform": "test-platform",
            "packages": {},
            "git_commit": "test-commit",
            "git_dirty": False,
        }

    def fake_run_matrix(*args, **kwargs):
        output_root = kwargs["output_root"]
        p1_simulation.write_json(
            kwargs["run_start_provenance"],
            output_root / p1_simulation.P1_RUN_START_PROVENANCE,
        )
        for name in p1_simulation.P1_RAW_RESULT_FILES:
            (output_root / name).write_text("metric\n1.25\n", encoding="utf-8")
        return {
            "output_root": output_root,
            "run_rows": [],
            "pair_rows": [],
            "batch_rows": [],
        }

    def finalize(output_root):
        report = output_root / "report.md"
        report.write_text("scientific report\n", encoding="utf-8")
        return {"report": report}

    monkeypatch.setattr(
        p1_simulation, "environment_manifest", fake_environment_manifest
    )
    monkeypatch.setattr(p1_simulation, "_run_matrix", fake_run_matrix)
    outputs = p1_simulation._run_controlled_formal_matrix(
        runs,
        target_root=target,
        config=config,
        config_path=p1_simulation.P1_CONFIG_PATH,
        matrix_audit=p1_simulation.audit_p1_run_matrix,
        finalize=finalize,
    )

    assert capture_before_staging == [True]
    assert outputs["output_root"] == target
    assert outputs["analysis"]["report"] == target / "report.md"
    assert (
        target / "report.md"
    ).read_text(encoding="utf-8") == "scientific report\n"
    assert not list(tmp_path.glob(".*.staging-*"))


def test_matched_rounds_receive_the_same_noise_object(monkeypatch) -> None:
    captured: list[tuple[str, np.ndarray]] = []
    scaffold_original = p1_simulation.scaffold_round_many
    fedavg_original = p1_simulation.fedavg_round_many

    def capture_scaffold(*args, **kwargs):
        captured.append(("scaffold", kwargs["epsilon_steps"]))
        return scaffold_original(*args, **kwargs)

    def capture_fedavg(*args, **kwargs):
        captured.append(("fedavg", kwargs["epsilon_steps"]))
        return fedavg_original(*args, **kwargs)

    monkeypatch.setattr(p1_simulation, "scaffold_round_many", capture_scaffold)
    monkeypatch.setattr(p1_simulation, "fedavg_round_many", capture_fedavg)
    p1_simulation._advance_matched_block(
        np.array([-1.0, 1.0]),
        np.zeros((2, 4)),
        np.array([-1.0, 1.0]),
        [np.random.default_rng(501), np.random.default_rng(502)],
        rounds=3,
        gamma=0.05,
        H=2,
        N=4,
        objective_name="nonlinear_main",
        noise_name="rademacher",
        collect=True,
    )
    assert len(captured) == 6
    for index in range(0, len(captured), 2):
        scaffold_name, scaffold_noise = captured[index]
        fedavg_name, fedavg_noise = captured[index + 1]
        assert scaffold_name == "scaffold"
        assert fedavg_name == "fedavg"
        assert scaffold_noise is fedavg_noise
        np.testing.assert_array_equal(scaffold_noise, fedavg_noise)


def test_explicit_fresh_noise_is_bitwise_unchanged_by_both_kernels() -> None:
    fresh_noise = np.array(
        [
            [[1, -1, 1], [-1, 1, -1]],
            [[-1, -1, 1], [1, 1, -1]],
        ],
        dtype=np.int8,
    )
    original = fresh_noise.copy()
    original_bytes = original.tobytes(order="C")
    x = np.array([0.2, -0.4])

    scaffold_round_many(
        x,
        np.zeros((2, 3)),
        gamma=0.05,
        H=2,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=fresh_noise,
    )
    np.testing.assert_array_equal(fresh_noise, original)
    assert fresh_noise.tobytes(order="C") == original_bytes

    fedavg_round_many(
        x,
        gamma=0.05,
        H=2,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=fresh_noise,
    )
    np.testing.assert_array_equal(fresh_noise, original)
    assert fresh_noise.tobytes(order="C") == original_bytes


def test_run_start_provenance_is_captured_before_any_output(
    tmp_path, monkeypatch
) -> None:
    config = p1_simulation.load_p1_config()
    runs = p1_simulation.build_p1_run_matrix(config, smoke=True)
    capture_observations: list[bool] = []
    captured_provenance: list[dict] = []

    def fake_environment_manifest() -> dict:
        capture_observations.append(not any(tmp_path.iterdir()))
        return {
            "python": "3.test",
            "platform": "test-platform",
            "packages": {
                "numpy": "test",
                "pandas": "test",
                "PyYAML": "test",
                "matplotlib": "test",
            },
            "git_commit": "test-commit",
            "git_dirty": False,
        }

    def fake_simulation(*args, **kwargs):
        captured_provenance.append(kwargs["run_start_provenance"])
        return ([{"num_batches": 1}], [{"pair_gate_pass": True}], [])

    monkeypatch.setattr(
        p1_simulation, "environment_manifest", fake_environment_manifest
    )
    monkeypatch.setattr(
        p1_simulation, "simulate_matched_setting", fake_simulation
    )
    p1_simulation._run_matrix(runs, output_root=tmp_path)

    assert capture_observations == [True]
    assert captured_provenance[0]["capture_point"] == "before_any_p1_output_write"
    assert captured_provenance[0]["git_commit"] == "test-commit"
    assert captured_provenance[0]["source_git_dirty_at_run_start"] is False
    assert (tmp_path / p1_simulation.P1_RUN_START_PROVENANCE).is_file()


def test_fedavg_balance_identity_uses_only_preupdate_qbars() -> None:
    x = 0.4
    gamma = 0.07
    H = 3
    # Each local-step noise has exactly zero client mean, so the averaged
    # realized recursion exposes the control-free balance algebra directly.
    epsilon = np.array([[1.0, -1.0], [-1.0, 1.0], [1.0, -1.0]])
    result = fedavg_round(
        x,
        gamma=gamma,
        H=H,
        objective=MAIN_OBJECTIVE,
        epsilon_steps=epsilon,
    )
    lam = 1.0 - MAIN_OBJECTIVE.a * gamma
    weights = lam ** np.arange(H - 1, -1, -1)
    expected_x_new = lam**H * x - gamma * (result.qbar @ weights)
    assert result.x_new == expected_x_new
    expected_stationary_balance = -(
        result.qbar @ weights
    ) / (MAIN_OBJECTIVE.a * np.sum(lam ** np.arange(H)))
    assert balance_round_value(result.qbar, gamma=gamma, a=MAIN_OBJECTIVE.a) == expected_stationary_balance


def test_tiny_matched_setting_produces_required_raw_columns() -> None:
    config = p1_simulation.load_p1_config()
    specs = p1_simulation.build_p1_run_matrix(config, smoke=True)
    override = {
        "burn_in_rounds": 2,
        "batch_length": 2,
        "min_batches": 4,
        "max_batches": 4,
        "extension_batches": 1,
    }
    run_rows, pair_rows, batch_rows = p1_simulation.simulate_matched_setting(
        specs,
        load_configs()["base"],
        config,
        protocol_override=override,
    )
    assert len(run_rows) == 4
    assert len(pair_rows) == 2
    assert len(batch_rows) == 16
    assert {row["algorithm"] for row in run_rows} == {"scaffold", "fedavg"}
    assert all(row["noise_match_verified"] for row in run_rows)
    assert all(row["noise_match_verified"] for row in pair_rows)
    assert all(row["finite_state_pass"] for row in run_rows)
    scaffold_rows = [row for row in run_rows if row["algorithm"] == "scaffold"]
    assert max(row["control_sum_max_abs"] for row in scaffold_rows) <= 1.0e-10
    assert {
        "algorithm",
        "pair_id",
        "seed",
        "H",
        "N",
        "gamma",
        "objective",
        "noise",
        "b_direct",
        "b_balance",
        "C_direct",
        "C_balance",
        "B20_target",
        "error_to_target",
        "gate_pass",
        "config_hash",
        "config_sha256",
        "git_commit",
        "source_git_dirty_at_run_start",
        "experiment_matrix_identifier",
    } <= set(run_rows[0])
    assert {
        "C_scaffold",
        "C_fedavg",
        "B20_FA_target",
        "error_FA",
        "scaled_error_FA",
        "Delta_C",
        "Delta_B20_target",
        "error_delta",
        "scaled_error_delta",
        "pair_gate_pass",
    } <= set(pair_rows[0])
    fedavg_rows = [row for row in run_rows if row["algorithm"] == "fedavg"]
    assert all(row["control_invariant_pass"] == "NOT_APPLICABLE" for row in fedavg_rows)
    assert all(row["control_sum_max_abs"] == "" for row in fedavg_rows)
