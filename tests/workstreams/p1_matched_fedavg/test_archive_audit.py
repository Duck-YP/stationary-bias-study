import json

import pytest

from stationary_bias.workstreams.p1_matched_fedavg.artifact_audit import (
    ARCHIVE_ROOT,
    CONFIG_FILE,
    NOTES_FILE,
    PROVENANCE_FILE,
    SUPPLEMENT_MANIFEST_FILE,
    audit_archived_config_closure,
)


def test_committed_archive_has_exact_recorded_configuration() -> None:
    audit = audit_archived_config_closure()

    assert audit == {
        "status": "PASS",
        "config_sha256": "5fb248b245200ea85da1622ea30303b2cd9121e7a302bc2ae788e3bc5579b85a",
        "source_commit": "6db4b66cf1e542108be0d03cf98cb8a58643bb11",
        "historical_artifacts_modified": False,
    }


def test_archive_audit_rejects_changed_configuration(tmp_path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    for name in (PROVENANCE_FILE, SUPPLEMENT_MANIFEST_FILE, NOTES_FILE):
        source = ARCHIVE_ROOT / name
        target = root / name
        target.write_bytes(source.read_bytes())
    config = root / CONFIG_FILE
    config.parent.mkdir()
    config.write_text("changed: true\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="hash does not match provenance"):
        audit_archived_config_closure(root)


def test_archive_audit_rejects_source_mismatch(tmp_path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    for name in (PROVENANCE_FILE, CONFIG_FILE, NOTES_FILE):
        source = ARCHIVE_ROOT / name
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    manifest = json.loads(
        (ARCHIVE_ROOT / SUPPLEMENT_MANIFEST_FILE).read_text(encoding="utf-8")
    )
    manifest["source"]["git_commit"] = "different"
    (root / SUPPLEMENT_MANIFEST_FILE).write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="source commit"):
        audit_archived_config_closure(root)
