"""Read-only integrity audit for committed formal evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ...core.io import REPO_ROOT
from .formal import (
    P2_FORMAL_MANIFEST,
    P2_RUN_START_PROVENANCE,
    formal_artifact_root,
)
from .rotation import (
    P2_ROTATION_MANIFEST,
    P2_ROTATION_PROVENANCE,
    rotation_artifact_root,
)
from .plateau import P2_PLATEAU_MANIFEST, plateau_artifact_root
from .protocols import audit_protocol_archive, resolve_recorded_protocol_path


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def load_strict_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(
        path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
    )
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return loaded


def _repository_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _sha256(path: Path) -> str:
    payload = path.read_bytes()
    if path.suffix in {".md", ".txt", ".yaml", ".yml"}:
        payload = payload.replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def _audit_directory(
    root: Path, *, provenance_name: str, manifest_name: str
) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(f"Missing formal artifact directory: {root}")
    provenance = load_strict_json(root / provenance_name)
    manifest = load_strict_json(root / manifest_name)
    if provenance.get("source_dirty_at_run_start") is not False:
        raise RuntimeError(f"Evidence lacks clean-source provenance: {root}")
    source_commit = provenance.get("source_commit")
    if source_commit in (None, "", "NO_COMMIT"):
        raise RuntimeError(f"Evidence lacks a source commit: {root}")
    if manifest.get("source_commit") != source_commit:
        raise RuntimeError(f"Manifest/provenance source mismatch: {root}")
    if manifest.get("matrix_id") != provenance.get("matrix_id"):
        raise RuntimeError(f"Manifest/provenance matrix mismatch: {root}")

    for key in ("config", "protocol"):
        recorded_path = str(provenance[f"{key}_path"])
        path = (
            resolve_recorded_protocol_path(recorded_path)
            if key == "protocol"
            else _repository_path(recorded_path)
        )
        observed = _sha256(path)
        if observed != provenance.get(f"{key}_sha256"):
            raise RuntimeError(f"Saved {key} hash differs from current source: {root}")

    inventory = [str(name) for name in manifest.get("artifact_filenames", [])]
    missing = [name for name in inventory if not (root / name).is_file()]
    if not inventory or missing:
        raise RuntimeError(
            f"Manifest artifact inventory is incomplete at {root}: {missing}"
        )
    return {
        "matrix_id": provenance["matrix_id"],
        "source_commit": source_commit,
        "source_dirty_at_run_start": False,
        "artifact_count": len(inventory),
        "strict_json": True,
        "config_sha256": provenance["config_sha256"],
        "protocol_sha256": provenance["protocol_sha256"],
    }


def audit_saved_p2_artifacts() -> dict[str, Any]:
    matrices = {
        target: _audit_directory(
            formal_artifact_root(target),
            provenance_name=P2_RUN_START_PROVENANCE,
            manifest_name=P2_FORMAL_MANIFEST,
        )
        for target in ("primary", "h4-small-step", "d5")
    }
    matrices["rotation"] = _audit_directory(
        rotation_artifact_root(),
        provenance_name=P2_ROTATION_PROVENANCE,
        manifest_name=P2_ROTATION_MANIFEST,
    )
    plateau_root = plateau_artifact_root()
    matrices["plateau"] = (
        _audit_directory(
            plateau_root,
            provenance_name=P2_RUN_START_PROVENANCE,
            manifest_name=P2_PLATEAU_MANIFEST,
        )
        if plateau_root.is_dir()
        else {
            "matrix_id": "p2-d2-fixed-gamma-largeN-plateau",
            "saved_artifact_status": "NOT_RUN",
        }
    )
    return {
        "status": "PASS",
        "protocol_archive": audit_protocol_archive(),
        "matrices": matrices,
    }
