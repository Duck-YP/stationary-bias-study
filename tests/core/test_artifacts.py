import json
from pathlib import Path

import pytest

from stationary_bias.core.artifacts import (
    replace_output_directory,
    validate_controlled_overwrite,
)
from stationary_bias.core.io import write_json


def _write_result(root: Path, value: str, *, commit: str) -> None:
    root.mkdir(parents=True)
    (root / "raw.csv").write_text(
        f"value,source_commit\n{value},{commit}\n", encoding="utf-8"
    )
    (root / "provenance.json").write_text(
        json.dumps({"matrix_id": "matrix", "config_sha256": "config"}),
        encoding="utf-8",
    )


def test_controlled_overwrite_ignores_provenance_but_rejects_science(
    tmp_path: Path,
) -> None:
    current = tmp_path / "current"
    staged = tmp_path / "staged"
    _write_result(current, "1.25", commit="old")
    _write_result(staged, "1.25", commit="new")
    audit = validate_controlled_overwrite(
        staged,
        current,
        raw_result_files=("raw.csv",),
        provenance_filename="provenance.json",
        identity_fields=("matrix_id", "config_sha256"),
        excluded_row_fields=("source_commit",),
    )
    assert audit["scientific_results_match"] is True

    (staged / "raw.csv").write_text(
        "value,source_commit\n2.5,new\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="changed scientific results"):
        validate_controlled_overwrite(
            staged,
            current,
            raw_result_files=("raw.csv",),
            provenance_filename="provenance.json",
            identity_fields=("matrix_id", "config_sha256"),
            excluded_row_fields=("source_commit",),
        )


def test_controlled_overwrite_allows_only_declared_numeric_roundoff(
    tmp_path: Path,
) -> None:
    current = tmp_path / "current"
    staged = tmp_path / "staged"
    _write_result(current, "1.250000000001", commit="old")
    _write_result(staged, "1.250000000002", commit="new")

    with pytest.raises(RuntimeError, match="changed scientific results"):
        validate_controlled_overwrite(
            staged,
            current,
            raw_result_files=("raw.csv",),
            provenance_filename="provenance.json",
            identity_fields=("matrix_id", "config_sha256"),
            excluded_row_fields=("source_commit",),
        )

    audit = validate_controlled_overwrite(
        staged,
        current,
        raw_result_files=("raw.csv",),
        provenance_filename="provenance.json",
        identity_fields=("matrix_id", "config_sha256"),
        excluded_row_fields=("source_commit",),
        numeric_tolerances={"value": (0.0, 2.0e-12)},
    )
    assert audit["scientific_results_match"] is True
    assert audit["numeric_tolerances"] == {
        "value": {"relative": 0.0, "absolute": 2.0e-12}
    }

    (staged / "raw.csv").write_text(
        "value,source_commit\n1.250001,new\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="changed scientific results"):
        validate_controlled_overwrite(
            staged,
            current,
            raw_result_files=("raw.csv",),
            provenance_filename="provenance.json",
            identity_fields=("matrix_id", "config_sha256"),
            excluded_row_fields=("source_commit",),
            numeric_tolerances={"value": (0.0, 2.0e-12)},
        )


def test_replace_output_directory_installs_staging(tmp_path: Path) -> None:
    current = tmp_path / "current"
    staged = tmp_path / "staged"
    current.mkdir()
    staged.mkdir()
    (current / "value").write_text("old", encoding="utf-8")
    (staged / "value").write_text("new", encoding="utf-8")
    replace_output_directory(staged, current)
    assert (current / "value").read_text(encoding="utf-8") == "new"
    assert not staged.exists()


def test_replace_output_directory_restores_current_when_install_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = tmp_path / "current"
    staged = tmp_path / "staged"
    current.mkdir()
    staged.mkdir()
    (current / "value").write_text("old", encoding="utf-8")
    (staged / "value").write_text("new", encoding="utf-8")
    original_replace = Path.replace

    def fail_staging_install(path: Path, target: Path) -> Path:
        if path == staged and Path(target) == current:
            raise OSError("simulated install failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_staging_install)
    with pytest.raises(OSError, match="simulated install failure"):
        replace_output_directory(staged, current)

    assert (current / "value").read_text(encoding="utf-8") == "old"
    assert (staged / "value").read_text(encoding="utf-8") == "new"


def test_write_json_rejects_non_standard_numbers(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        write_json({"value": float("nan")}, tmp_path / "invalid.json")
