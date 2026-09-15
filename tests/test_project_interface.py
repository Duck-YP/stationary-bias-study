import re
from pathlib import Path

from stationary_bias.cli import P0_PUBLIC_TO_EXPERIMENT, WORKSTREAMS, check_all


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_experiment_names_are_descriptive() -> None:
    assert set(P0_PUBLIC_TO_EXPERIMENT) == {
        "coefficient-convergence",
        "client-count-scaling",
        "negative-controls",
    }
    assert set(P0_PUBLIC_TO_EXPERIMENT.values()) == {
        "coefficient_convergence",
        "client_count_scaling",
        "negative_controls",
    }
    assert set(WORKSTREAMS) == {"p0", "p1", "p2"}


def test_project_has_one_obvious_entry_point() -> None:
    assert (PROJECT_ROOT / "run.py").is_file()
    assert (PROJECT_ROOT / "README.md").is_file()


def test_implemented_workstreams_have_matching_project_areas() -> None:
    for slug in (
        "p0_scaffold_bias",
        "p1_matched_fedavg",
        "p2_multidimensional_validation",
    ):
        assert (PROJECT_ROOT / "workstreams" / slug / "README.md").is_file()
        assert (PROJECT_ROOT / "workstreams" / slug / "study.yaml").is_file()
        assert (PROJECT_ROOT / "src" / "stationary_bias" / "workstreams" / slug).is_dir()
        assert (PROJECT_ROOT / "tests" / "workstreams" / slug).is_dir()


def test_frozen_run_matrices_pass() -> None:
    checked = check_all()
    assert checked["status"] == "PASS"
    assert set(checked["p2"]) == {
        "status",
        "workstream",
        "smoke",
        "formal_d2",
        "rotation_d2",
        "formal_d5",
        "fixed_gamma_large_N_d2",
        "artifacts",
    }
    assert checked["p2"]["artifacts"]["status"] == "PASS"


def test_reader_facing_documents_describe_only_current_project_state() -> None:
    document_paths = [PROJECT_ROOT / "README.md"]
    document_paths.extend((PROJECT_ROOT / "docs").rglob("*.md"))
    document_paths.extend(
        path
        for path in (PROJECT_ROOT / "workstreams").rglob("*.md")
        if "artifacts" not in path.parts
    )
    prohibited = re.compile(
        r"\b(?:status|todo|tbd|pending|planned|active|conditional|"
        r"complete|completed|incomplete|gpt|ai|codex)\b|"
        r"狀態|待補|待辦|未完成|已完成|下一步|接下來",
        re.IGNORECASE,
    )
    violations = {
        str(path.relative_to(PROJECT_ROOT)): sorted(set(prohibited.findall(text)))
        for path in document_paths
        if (text := path.read_text(encoding="utf-8")) and prohibited.search(text)
    }
    assert violations == {}


def test_editable_narrative_uses_descriptive_workstream_names() -> None:
    paths = [PROJECT_ROOT / "README.md"]
    paths.extend((PROJECT_ROOT / "docs").rglob("*.md"))
    paths.extend(
        [
            PROJECT_ROOT / "workstreams" / "README.md",
            PROJECT_ROOT / "workstreams" / "ROADMAP.md",
            PROJECT_ROOT / "workstreams" / "p0_scaffold_bias" / "README.md",
            PROJECT_ROOT / "workstreams" / "p1_matched_fedavg" / "README.md",
            PROJECT_ROOT
            / "workstreams"
            / "p2_multidimensional_validation"
            / "README.md",
            PROJECT_ROOT
            / "workstreams"
            / "p1_matched_fedavg"
            / "artifacts"
            / "archive"
            / "README.md",
        ]
    )
    paths.extend((PROJECT_ROOT / "src").rglob("*.py"))
    paths.extend((PROJECT_ROOT / "tests").rglob("*.py"))
    numbered_label = re.compile(r"\bP[0-9]+\b")

    violations = [
        str(path.relative_to(PROJECT_ROOT))
        for path in paths
        if numbered_label.search(path.read_text(encoding="utf-8"))
    ]
    assert violations == []


def test_deprecated_leading_coefficient_label_is_absent() -> None:
    deprecated = "B" + "10"
    text_suffixes = {
        ".csv",
        ".json",
        ".lock",
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    violations: list[str] = []
    excluded_directories = {".git", ".pytest_cache", ".venv", "__pycache__"}
    for path in PROJECT_ROOT.rglob("*"):
        if excluded_directories.intersection(path.parts) or not path.is_file():
            continue
        relative = str(path.relative_to(PROJECT_ROOT))
        if deprecated in relative:
            violations.append(relative)
            continue
        if path.suffix in text_suffixes and deprecated in path.read_text(
            encoding="utf-8"
        ):
            violations.append(relative)
    assert violations == []
