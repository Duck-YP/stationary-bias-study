"""Unpack supplied targeted evidence with dual hashes; never run experiments."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from public_metadata import portable_metadata

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".py", ".md", ".json", ".csv", ".tex", ".diff", ".patch", ".ps1", ".yaml", ".toml", ".txt", ".lock", ".sh", ".cff", ".bib"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materials", type=Path, required=True,
                        help="Extracted repository_materials/targeted_mechanism from the supplied manuscript ZIP")
    args = parser.parse_args()
    rows, archives = [], []

    def save(data, target, source):
        target = target.resolve()
        if not target.is_relative_to(ROOT):
            raise ValueError("Target outside release")
        final = portable_metadata(data) if target.suffix in TEXT else data
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(final)
        rows.append(dict(path=target.relative_to(ROOT).as_posix(), source=source,
                         bytes=len(final), source_sha256=sha(data), sha256=sha(final),
                         exact_copy=data == final,
                         reason="" if data == final else "Machine-local path strings only; scientific values unchanged. Original hashes retained for provenance."))

    mapping = {
        "TARGETED_MECHANISM_REVIEW.zip": "artifacts/canonical_paper_export/targeted_mechanism",
        "SOURCE_TARGETED_MECHANISM.zip": "src/targeted_mechanism_snapshot",
        "SCAFFOLD_Targeted_Mechanism_Independent_Audit_20261015.zip": "docs/targeted_mechanism/independent_audit",
    }
    for filename, destination in mapping.items():
        source = args.materials / filename
        with zipfile.ZipFile(source) as archive:
            assert archive.testzip() is None
            members = [entry for entry in archive.infolist() if not entry.is_dir()]
            assert len({entry.filename for entry in members}) == len(members)
            for entry in members:
                relative = PurePosixPath(entry.filename)
                assert not relative.is_absolute() and ".." not in relative.parts and ":" not in entry.filename
                save(archive.read(entry), ROOT / destination / relative,
                     "repository_materials/targeted_mechanism/" + filename + "!" + entry.filename)
            archives.append(dict(name=filename, bytes=source.stat().st_size,
                                 sha256=sha(source.read_bytes()), entries=len(members),
                                 destination=destination, crc_verified=True))
    for name in ["README.md", "SCAFFOLD_Targeted_Mechanism_Independent_Review_20261015.md"]:
        save((args.materials / name).read_bytes(), ROOT / "docs/targeted_mechanism" / name,
             "repository_materials/targeted_mechanism/" + name)
    manifests = ROOT / "docs/manifests"
    with (manifests / "TARGETED_COPY_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "source", "bytes", "source_sha256", "sha256", "exact_copy", "reason"])
        writer.writeheader()
        writer.writerows(rows)
    record = dict(archives=archives, files=len(rows), metadata_variants=sum(not r["exact_copy"] for r in rows),
                  scientific_recomputation=False,
                  original_internal_manifests="Preserved historical source hashes; TARGETED_COPY_MANIFEST.csv describes current public bytes and metadata variants.")
    (manifests / "TARGETED_IMPORT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
