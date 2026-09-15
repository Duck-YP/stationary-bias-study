"""Reusable transactions for canonical research-artifact directories."""

from __future__ import annotations

import csv
import json
import math
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def scientific_csv_content(
    path: Path, *, excluded_fields: Iterable[str] = ()
) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    """Read deterministic CSV fields while excluding run provenance."""

    excluded = set(excluded_fields)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise RuntimeError(f"Controlled overwrite found an empty CSV: {path}")
        fields = tuple(field for field in reader.fieldnames if field not in excluded)
        rows = [tuple(row[field] for field in fields) for row in reader]
    return fields, rows


def validate_controlled_overwrite(
    staged_root: Path,
    current_root: Path,
    *,
    raw_result_files: Sequence[str],
    provenance_filename: str,
    identity_fields: Sequence[str],
    excluded_row_fields: Iterable[str] = (),
    numeric_tolerances: Mapping[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Require an existing canonical result to match staged scientific output."""

    if not current_root.exists() or not any(current_root.iterdir()):
        return {
            "previous_output": "absent",
            "scientific_results_match": None,
            "compared_files": [],
        }

    required = [*raw_result_files, provenance_filename]
    missing = [
        str(root / name)
        for root in (current_root, staged_root)
        for name in required
        if not (root / name).is_file()
    ]
    if missing:
        raise RuntimeError(
            "Controlled overwrite requires complete current and staged raw outputs; "
            "missing: " + ", ".join(missing)
        )

    current_provenance = json.loads(
        (current_root / provenance_filename).read_text(encoding="utf-8")
    )
    staged_provenance = json.loads(
        (staged_root / provenance_filename).read_text(encoding="utf-8")
    )
    for field in identity_fields:
        if current_provenance.get(field) != staged_provenance.get(field):
            raise RuntimeError(
                "Controlled overwrite rejected a different formal result identity: "
                f"{field}"
            )

    tolerances = dict(numeric_tolerances or {})
    for name in raw_result_files:
        current_fields, current_rows = scientific_csv_content(
            current_root / name, excluded_fields=excluded_row_fields
        )
        staged_fields, staged_rows = scientific_csv_content(
            staged_root / name, excluded_fields=excluded_row_fields
        )
        if current_fields != staged_fields or len(current_rows) != len(staged_rows):
            raise RuntimeError(
                "Controlled overwrite rejected changed scientific results in " + name
            )
        for current_row, staged_row in zip(current_rows, staged_rows, strict=True):
            for field, current_value, staged_value in zip(
                current_fields, current_row, staged_row, strict=True
            ):
                if current_value == staged_value:
                    continue
                tolerance = tolerances.get(field)
                if tolerance is None:
                    raise RuntimeError(
                        "Controlled overwrite rejected changed scientific results in "
                        + name
                    )
                try:
                    current_number = float(current_value)
                    staged_number = float(staged_value)
                except ValueError as exc:
                    raise RuntimeError(
                        "Controlled overwrite rejected changed scientific results in "
                        + name
                    ) from exc
                relative, absolute = tolerance
                if not (
                    math.isfinite(current_number)
                    and math.isfinite(staged_number)
                    and math.isclose(
                        current_number,
                        staged_number,
                        rel_tol=float(relative),
                        abs_tol=float(absolute),
                    )
                ):
                    raise RuntimeError(
                        "Controlled overwrite rejected changed scientific results in "
                        + name
                    )

    return {
        "previous_output": "replaced",
        "scientific_results_match": True,
        "compared_files": list(raw_result_files),
        "numeric_tolerances": {
            field: {"relative": values[0], "absolute": values[1]}
            for field, values in tolerances.items()
        },
    }


def require_complete_existing_output(
    current_root: Path, *, required_files: Sequence[str]
) -> None:
    """Reject a partial canonical directory before expensive reproduction work."""

    if not current_root.exists() or not any(current_root.iterdir()):
        return
    missing = [name for name in required_files if not (current_root / name).is_file()]
    if missing:
        raise RuntimeError(
            "Controlled overwrite requires a complete current raw output; missing: "
            + ", ".join(missing)
        )


def create_staging_directory(target_root: Path) -> Path:
    """Create an ignored sibling staging directory for one canonical target."""

    target_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(prefix=f".{target_root.name}.staging-", dir=target_root.parent)
    )


def replace_output_directory(staged_root: Path, target_root: Path) -> None:
    """Atomically replace a canonical directory, restoring it if the swap fails."""

    target_root.parent.mkdir(parents=True, exist_ok=True)
    backup_container: Path | None = None
    backup_root: Path | None = None
    if target_root.exists():
        backup_container = Path(
            tempfile.mkdtemp(
                prefix=f".{target_root.name}.previous-", dir=target_root.parent
            )
        )
        backup_root = backup_container / target_root.name
        target_root.replace(backup_root)
    try:
        staged_root.replace(target_root)
    except BaseException:
        if backup_root is not None and backup_root.exists() and not target_root.exists():
            backup_root.replace(target_root)
        if backup_container is not None and backup_container.exists():
            shutil.rmtree(backup_container)
        raise
    else:
        if backup_container is not None and backup_container.exists():
            shutil.rmtree(backup_container)


def stage_existing_directory(target_root: Path) -> Path:
    """Copy a canonical directory into a sibling staging directory."""

    if not target_root.is_dir():
        raise FileNotFoundError(f"Canonical artifact directory does not exist: {target_root}")
    staged_root = create_staging_directory(target_root)
    try:
        shutil.copytree(target_root, staged_root, dirs_exist_ok=True)
    except BaseException:
        shutil.rmtree(staged_root)
        raise
    return staged_root


def rebase_staged_paths(value: Any, staged_root: Path, target_root: Path) -> Any:
    """Rewrite returned staging paths to their installed canonical locations."""

    if isinstance(value, Path):
        try:
            return target_root / value.relative_to(staged_root)
        except ValueError:
            return value
    if isinstance(value, dict):
        return {
            key: rebase_staged_paths(item, staged_root, target_root)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [rebase_staged_paths(item, staged_root, target_root) for item in value]
    if isinstance(value, tuple):
        return tuple(
            rebase_staged_paths(item, staged_root, target_root) for item in value
        )
    return value
