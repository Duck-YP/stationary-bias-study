from pathlib import Path

from stationary_bias.workstreams.p2_multidimensional_validation.protocols import (
    PROTOCOL_ARCHIVE_ROOT,
    WORKSTREAM_ROOT,
    audit_protocol_archive,
    resolve_recorded_protocol_path,
)


def test_protocol_markdown_is_confined_to_the_archive() -> None:
    assert sorted(path.name for path in WORKSTREAM_ROOT.glob("*.md")) == ["README.md"]
    assert audit_protocol_archive() == {"status": "PASS", "files": 4}


def test_legacy_protocol_path_resolves_to_archived_snapshot() -> None:
    legacy = WORKSTREAM_ROOT / "formal_protocol.md"

    assert resolve_recorded_protocol_path(str(legacy)) == (
        PROTOCOL_ARCHIVE_ROOT / "formal_protocol.md"
    )
    assert resolve_recorded_protocol_path(
        str(Path("workstreams") / WORKSTREAM_ROOT.name / legacy.name)
    ) == (PROTOCOL_ARCHIVE_ROOT / legacy.name)
