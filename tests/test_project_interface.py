from pathlib import Path

from stationary_bias.cli import PUBLIC_TO_INTERNAL, RUN_CHOICES, check_study


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_experiment_names_are_descriptive() -> None:
    assert set(PUBLIC_TO_INTERNAL) == {
        "coefficient-convergence",
        "client-count-scaling",
        "negative-controls",
    }
    assert "small-step-confirmation" in RUN_CHOICES
    assert all("p3" not in name.lower() for name in RUN_CHOICES)


def test_project_has_one_obvious_entry_point() -> None:
    assert (PROJECT_ROOT / "run.py").is_file()
    assert (PROJECT_ROOT / "README.md").is_file()


def test_public_paths_do_not_use_historical_short_labels() -> None:
    ignored = {
        ".git",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
    }
    paths = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in PROJECT_ROOT.rglob("*")
        if not any(part in ignored or part.endswith(".egg-info") for part in path.parts)
    ]
    historical_paths = [path for path in paths if "p3" in path.lower()]
    assert historical_paths == []


def test_frozen_run_matrices_pass() -> None:
    assert check_study()["status"] == "PASS"
