"""Integrity checks for the archived configuration supplement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ...core.io import P1_ARTIFACT_ROOT


ARCHIVE_ROOT = P1_ARTIFACT_ROOT / "archive" / "original_formal_snapshot"
PROVENANCE_FILE = "run_start_provenance.json"
SUPPLEMENT_MANIFEST_FILE = "supplement_manifest.json"
CONFIG_FILE = "supplement/original_run_config.yaml"
NOTES_FILE = "ARCHIVE_NOTES.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_archived_config_closure(root: Path = ARCHIVE_ROOT) -> dict[str, Any]:
    """Verify that the archived run includes its exact recorded configuration."""

    required = [PROVENANCE_FILE, SUPPLEMENT_MANIFEST_FILE, CONFIG_FILE, NOTES_FILE]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("Archive supplement is incomplete: " + ", ".join(missing))

    provenance = json.loads((root / PROVENANCE_FILE).read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / SUPPLEMENT_MANIFEST_FILE).read_text(encoding="utf-8")
    )
    source = manifest.get("source", {})
    files = manifest.get("files", {})
    observed_hash = _sha256(root / CONFIG_FILE)
    expected_hash = provenance.get("config_sha256")

    if manifest.get("schema_version") != 1:
        raise RuntimeError("Archive supplement schema is unsupported")
    if manifest.get("role") != "post_run_archive_supplement":
        raise RuntimeError("Archive supplement role is invalid")
    if manifest.get("historical_artifacts_modified") is not False:
        raise RuntimeError("Archive supplement must preserve historical artifacts")
    if source.get("git_commit") != provenance.get("git_commit"):
        raise RuntimeError("Archived configuration source commit does not match provenance")
    recorded_path = str(provenance.get("config_path", "")).replace("\\", "/")
    if not recorded_path.endswith(str(source.get("repository_path", ""))):
        raise RuntimeError("Archived configuration source path does not match provenance")
    if not (
        observed_hash
        == expected_hash
        == source.get("sha256")
        == files.get(CONFIG_FILE)
    ):
        raise RuntimeError("Archived configuration hash does not match provenance")

    return {
        "status": "PASS",
        "config_sha256": observed_hash,
        "source_commit": source["git_commit"],
        "historical_artifacts_modified": False,
    }
