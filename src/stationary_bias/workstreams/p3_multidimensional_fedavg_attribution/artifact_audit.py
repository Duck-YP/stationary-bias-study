"""Read-only integrity audit for multidimensional formal evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from ...core.io import REPO_ROOT
from . import formal, matched_formal


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def _load_strict_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(
        path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
    )
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return loaded


def _source_blob(commit: str, recorded_path: str) -> bytes:
    repository_path = recorded_path.replace("\\", "/")
    return subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPO_ROOT}",
            "show",
            f"{commit}:{repository_path}",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _source_blob_by_oid(blob_oid: str) -> bytes:
    return subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPO_ROOT}",
            "cat-file",
            "blob",
            blob_oid,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _audit_directory(
    root: Path,
    *,
    provenance_name: str,
    manifest_name: str,
    snapshot_name: str,
) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(f"Missing formal artifact directory: {root}")
    provenance = _load_strict_json(root / provenance_name)
    manifest = _load_strict_json(root / manifest_name)

    if provenance.get("source_dirty_at_run_start") is not False:
        raise RuntimeError(f"Evidence lacks clean-source provenance: {root}")
    source_commit = str(provenance.get("source_commit", ""))
    if source_commit in ("", "NO_COMMIT"):
        raise RuntimeError(f"Evidence lacks a source commit: {root}")
    if manifest.get("source_commit") != source_commit:
        raise RuntimeError(f"Manifest/provenance source mismatch: {root}")
    if manifest.get("matrix_id") != provenance.get("matrix_id"):
        raise RuntimeError(f"Manifest/provenance matrix mismatch: {root}")

    expected_hash = str(provenance.get("config_sha256", ""))
    snapshot_hash = hashlib.sha256((root / snapshot_name).read_bytes()).hexdigest()
    source_expected_hash = str(
        provenance.get("source_config_sha256", expected_hash)
    )
    source_blob_oid = str(provenance.get("source_config_blob", ""))
    source_bytes = (
        _source_blob_by_oid(source_blob_oid)
        if source_blob_oid
        else _source_blob(source_commit, str(provenance["config_path"]))
    )
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if (
        not expected_hash
        or snapshot_hash != expected_hash
        or not source_expected_hash
        or source_hash != source_expected_hash
    ):
        raise RuntimeError(f"Config provenance closure failed: {root}")

    inventory = [str(name) for name in manifest.get("artifact_filenames", [])]
    missing = [name for name in inventory if not (root / name).is_file()]
    if not inventory or missing:
        raise RuntimeError(
            f"Manifest artifact inventory is incomplete at {root}: {missing}"
        )
    return {
        "present": True,
        "matrix_id": provenance["matrix_id"],
        "source_commit": source_commit,
        "source_dirty_at_run_start": False,
        "artifact_count": len(inventory),
        "strict_json": True,
        "config_sha256": expected_hash,
        "source_config_sha256": source_expected_hash,
        "source_config_verified": True,
        "snapshot_verified": True,
    }


def audit_saved_p3_artifacts() -> dict[str, Any]:
    """Validate each available formal tree without changing artifacts."""

    matrices = {
        "fedavg_coefficient_primary": _audit_directory(
            formal.formal_artifact_root("primary"),
            provenance_name=formal.RUN_START_PROVENANCE,
            manifest_name=formal.FORMAL_MANIFEST,
            snapshot_name="p3_primary_config_snapshot.yaml",
        ),
        "fedavg_coefficient_h4_small_step": _audit_directory(
            formal.formal_artifact_root("h4-small-step"),
            provenance_name=formal.RUN_START_PROVENANCE,
            manifest_name=formal.FORMAL_MANIFEST,
            snapshot_name="p3_h4_small_step_config_snapshot.yaml",
        ),
        "matched_attribution_primary": _audit_directory(
            matched_formal.formal_artifact_root("primary"),
            provenance_name=matched_formal.RUN_START_PROVENANCE,
            manifest_name=matched_formal.FORMAL_MANIFEST,
            snapshot_name="p3_matched_primary_config_snapshot.yaml",
        ),
    }
    h4_root = matched_formal.formal_artifact_root("h4-small-step")
    matrices["matched_attribution_h4_small_step"] = (
        _audit_directory(
            h4_root,
            provenance_name=matched_formal.RUN_START_PROVENANCE,
            manifest_name=matched_formal.FORMAL_MANIFEST,
            snapshot_name="p3_matched_h4_small_step_config_snapshot.yaml",
        )
        if h4_root.is_dir() and any(h4_root.iterdir())
        else {"present": False, "matrix_id": "p3-d2-matched-attribution-h4-small-step-confirmation"}
    )
    return {"status": "PASS", "matrices": matrices}
