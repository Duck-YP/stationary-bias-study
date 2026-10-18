"""Hash all public-release files, excluding only receipts/self and runtime caches."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from release_files import public_files, RUNTIME

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"docs/manifests/RELEASE_FILE_MANIFEST.csv", "docs/VALIDATION_RECEIPT.md"}


def files():
    return [path for path in sorted(public_files(ROOT))
            if path.relative_to(ROOT).as_posix() not in EXCLUDED]


def main():
    origins = {}
    for name in ("EXACT_COPY_MANIFEST.csv", "PUBLICATION_COPY_MANIFEST.csv", "TARGETED_COPY_MANIFEST.csv"):
        with (ROOT / "docs/manifests" / name).open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                origins[row["path"]] = row
    source_rows = []
    for path in files():
        relative = path.relative_to(ROOT).as_posix()
        if relative == "docs/SOURCE_MANIFEST.csv":
            continue
        origin = origins.get(relative, {})
        source_rows.append(dict(
            path=relative, bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            source=origin.get("source", "publication-maintenance"),
            source_sha256=origin.get("source_sha256", origin.get("sha256", "")),
            copy_relation=("exact" if origin.get("exact_copy") == "True" else "documented-variant")
                          if origin else "authored-publication-file"))
    with (ROOT / "docs/SOURCE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "source", "source_sha256", "copy_relation"])
        writer.writeheader()
        writer.writerows(source_rows)
    rows = [{"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in files()]
    with (ROOT / "docs/manifests/RELEASE_FILE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(dict(public_files=len(rows), source_manifest_files=len(source_rows),
                          public_bytes=sum(row["bytes"] for row in rows),
                          exclusions=sorted(EXCLUDED), runtime_directories_ignored=sorted(RUNTIME)), indent=2))


if __name__ == "__main__":
    main()
