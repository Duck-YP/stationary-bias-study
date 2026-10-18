"""Read-only integrity audit for multidimensional formal evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from ...core.io import REPO_ROOT
from . import formal, matched_diagnostic, matched_formal


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


def _latest_artifact_commit(path: Path) -> str | None:
    relative = path.relative_to(REPO_ROOT).as_posix()
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={REPO_ROOT}",
            "log",
            "-1",
            "--format=%H",
            "--",
            relative,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = completed.stdout.strip()
    return commit or None


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


def _audit_diagnostic_directory(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(f"Missing diagnostic artifact directory: {root}")
    manifest_path = root / "diagnostic_manifest.json"
    manifest = _load_strict_json(manifest_path)
    provenance_name = str(manifest.get("rebuild_start_provenance_file", ""))
    provenance = _load_strict_json(root / provenance_name)
    provenance_hash = hashlib.sha256((root / provenance_name).read_bytes()).hexdigest()
    if manifest.get("rebuild_start_provenance_sha256") != provenance_hash:
        raise RuntimeError("Diagnostic rebuild-start provenance hash mismatch")
    if manifest.get("matrix_id") != matched_diagnostic.DIAGNOSTIC_MATRIX_ID:
        raise RuntimeError("Diagnostic manifest matrix identifier is invalid")
    if provenance.get("matrix_id") != manifest.get("matrix_id"):
        raise RuntimeError("Diagnostic manifest/provenance matrix mismatch")

    inventory = [str(name) for name in manifest.get("artifact_filenames", [])]
    actual = sorted(path.name for path in root.iterdir() if path.is_file())
    if not inventory or sorted(inventory) != actual:
        raise RuntimeError("Diagnostic artifact inventory is incomplete or contains extras")

    recorded_hashes = {
        str(name): str(digest)
        for name, digest in manifest.get("artifact_sha256", {}).items()
    }
    expected_hashed_files = sorted(name for name in inventory if name != manifest_path.name)
    if sorted(recorded_hashes) != expected_hashed_files:
        raise RuntimeError("Diagnostic artifact hash inventory is incomplete")
    for name, expected in recorded_hashes.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Diagnostic artifact hash mismatch: {name}")

    expected_config_hash = str(provenance.get("config_sha256", ""))
    snapshot_name = str(manifest.get("config_snapshot", ""))
    if (
        not expected_config_hash
        or hashlib.sha256((root / snapshot_name).read_bytes()).hexdigest()
        != expected_config_hash
        or manifest.get("config_sha256") != expected_config_hash
    ):
        raise RuntimeError("Diagnostic config provenance closure failed")

    source_snapshot = {
        str(name): str(digest)
        for name, digest in provenance.get("source_snapshot_sha256", {}).items()
    }
    if not source_snapshot:
        raise RuntimeError("Diagnostic provenance lacks a source snapshot")
    artifact_commit = _latest_artifact_commit(manifest_path)
    for name, expected in source_snapshot.items():
        observed_bytes = (
            _source_blob(artifact_commit, name)
            if artifact_commit is not None
            else (REPO_ROOT / name).read_bytes()
        )
        if hashlib.sha256(observed_bytes).hexdigest() != expected:
            raise RuntimeError(f"Diagnostic source snapshot mismatch: {name}")

    protected = {
        str(name): str(digest)
        for name, digest in manifest.get("protected_output_sha256", {}).items()
    }
    snapshot_config = matched_diagnostic.load_yaml(root / snapshot_name)
    snapshot_protected = {
        str(name): str(digest)
        for name, digest in snapshot_config.get("protected_output_sha256", {}).items()
    }
    if protected != snapshot_protected:
        raise RuntimeError("Diagnostic protected-output policy differs from its snapshot")
    for name, expected in protected.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Protected diagnostic output changed: {name}")

    for source in manifest.get("source_artifacts", {}).values():
        source_root = REPO_ROOT / str(source["artifact_root"])
        if hashlib.sha256(
            (source_root / str(source["raw_result"])).read_bytes()
        ).hexdigest() != str(source["raw_sha256"]):
            raise RuntimeError("Diagnostic raw source artifact hash mismatch")
        if hashlib.sha256(
            (source_root / "run_start_provenance.json").read_bytes()
        ).hexdigest() != str(source["provenance_sha256"]):
            raise RuntimeError("Diagnostic source provenance hash mismatch")

    return {
        "present": True,
        "matrix_id": manifest["matrix_id"],
        "artifact_count": len(inventory),
        "strict_json": True,
        "config_sha256": expected_config_hash,
        "source_snapshot_verified": True,
        "source_snapshot_basis": artifact_commit or "current_worktree",
        "source_dirty_at_rebuild_start": provenance.get(
            "source_dirty_at_rebuild_start"
        ),
        "protected_outputs_verified": True,
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
    diagnostic_root = matched_diagnostic.DIAGNOSTIC_ROOT
    matrices["matched_attribution_h4_diagnostic"] = (
        _audit_diagnostic_directory(diagnostic_root)
        if diagnostic_root.is_dir() and any(diagnostic_root.iterdir())
        else {
            "present": False,
            "matrix_id": matched_diagnostic.DIAGNOSTIC_MATRIX_ID,
        }
    )
    return {"status": "PASS", "matrices": matrices}
