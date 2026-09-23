"""Access and integrity checks for protocol snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ...core.io import REPO_ROOT


WORKSTREAM_ROOT = REPO_ROOT / "workstreams" / "p2_multidimensional_validation"
PROTOCOL_ARCHIVE_ROOT = WORKSTREAM_ROOT / "artifacts" / "archive" / "protocols"
PROTOCOL_ARCHIVE_MANIFEST = PROTOCOL_ARCHIVE_ROOT.parent / "protocol_manifest.json"
PROTOCOL_FILENAMES = {
    "formal_protocol.md",
    "rotation_protocol.md",
    "d2_fixed_gamma_largeN_plateau_protocol.md",
    "d5_protocol.md",
}


def archived_protocol_path(filename: str) -> Path:
    if filename not in PROTOCOL_FILENAMES:
        raise ValueError(f"Unknown protocol snapshot: {filename}")
    return PROTOCOL_ARCHIVE_ROOT / filename


def resolve_recorded_protocol_path(value: str) -> Path:
    """Resolve protocol references to their stored snapshots."""

    recorded = Path(value)
    candidate = recorded if recorded.is_absolute() else REPO_ROOT / recorded
    if candidate.is_file():
        return candidate
    if candidate.parent == WORKSTREAM_ROOT and candidate.name in PROTOCOL_FILENAMES:
        archived = archived_protocol_path(candidate.name)
        if archived.is_file():
            return archived
    raise FileNotFoundError(f"Recorded protocol snapshot is unavailable: {value}")


def audit_protocol_archive() -> dict[str, Any]:
    """Verify the inventory and hashes of archived protocol snapshots."""

    manifest = json.loads(PROTOCOL_ARCHIVE_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("Protocol archive schema is unsupported")
    if manifest.get("role") != "protocol_archive":
        raise RuntimeError("Protocol archive role is invalid")
    files = manifest.get("files", {})
    if set(files) != PROTOCOL_FILENAMES:
        raise RuntimeError("Protocol archive inventory is incomplete")
    for filename, expected_hash in files.items():
        payload = archived_protocol_path(filename).read_bytes().replace(
            b"\r\n", b"\n"
        )
        observed_hash = hashlib.sha256(payload).hexdigest()
        if observed_hash != expected_hash:
            raise RuntimeError(f"Protocol archive hash mismatch: {filename}")
    return {"status": "PASS", "files": len(files)}
