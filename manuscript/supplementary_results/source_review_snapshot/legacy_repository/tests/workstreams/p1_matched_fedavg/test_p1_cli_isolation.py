import stationary_bias.cli as cli
import stationary_bias.workstreams.p0_scaffold_bias.confirmation as p0_confirmation
import stationary_bias.workstreams.p0_scaffold_bias.simulation as p0_simulation
import stationary_bias.workstreams.p1_matched_fedavg.simulation as p1_simulation


def test_p1_run_does_not_write_the_p0_manifest(monkeypatch) -> None:
    called: list[bool] = []
    monkeypatch.setattr(
        p1_simulation,
        "run_p1_experiment",
        lambda: (called.append(True) or {"overwrite_audit": {}}),
    )
    monkeypatch.setattr(
        cli,
        "_write_p0_manifest",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("One workstream attempted to write another manifest")
        ),
    )
    assert cli.main(["p1", "run"]) == 0
    assert called == [True]


def test_existing_all_dispatch_excludes_p1(monkeypatch) -> None:
    original_calls: list[str] = []
    confirmation_calls: list[bool] = []
    p1_calls: list[bool] = []
    monkeypatch.setattr(p0_simulation, "run_experiment", original_calls.append)
    monkeypatch.setattr(
        p0_confirmation, "run_confirmation", lambda: confirmation_calls.append(True)
    )
    monkeypatch.setattr(
        p1_simulation, "run_p1_experiment", lambda: p1_calls.append(True)
    )
    cli.run_p0_experiment("all")
    assert original_calls == list(cli.P0_PUBLIC_TO_EXPERIMENT.values())
    assert confirmation_calls == [True]
    assert p1_calls == []
