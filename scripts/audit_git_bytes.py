"""Check newline preservation using Git hash filters, without staging/committing."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from release_files import public_files

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {".py", ".md", ".tex", ".toml", ".csv", ".json", ".yaml", ".bbl", ".lock"}


def command(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def main():
    repository = Path(command("rev-parse", "--show-toplevel")).resolve()
    files = [path for path in sorted(public_files(ROOT)) if path.suffix in SUFFIXES]
    crlf = [path for path in files if b"\r\n" in path.read_bytes()]
    samples = []
    for extension in sorted(SUFFIXES):
        candidates = [path for path in files if path.suffix == extension]
        if not candidates:
            continue
        path = next((path for path in candidates if path in crlf), candidates[0])
        relative = path.relative_to(repository).as_posix()
        raw = command("hash-object", "--no-filters", relative, cwd=repository)
        filtered = command("hash-object", f"--path={relative}", relative, cwd=repository)
        assert raw == filtered, relative
        samples.append(dict(path=path.relative_to(ROOT).as_posix(), contains_CRLF=path in crlf,
                            git_blob_raw=raw, git_blob_filtered=filtered,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), matches=True))
    report = dict(status="PASS", examined_text_files=len(files), historical_CRLF_files=len(crlf),
                  representative_filter_checks=len(samples), samples=samples,
                  attribute_policy="* -text; only PDF/PNG/NPZ explicitly binary",
                  method="git hash-object with path filters compared against --no-filters; no index writes, staging or commit")
    destination = ROOT / "docs/manifests/GIT_BYTE_AUDIT.json"
    destination.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}, indent=2))


if __name__ == "__main__":
    main()
