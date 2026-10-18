"""Copy recorded scientific source and compact evidence without numerical work.

This is an export builder, not an experiment runner. Inputs are read-only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_PATH = re.compile(r"[A-Z]:[\\/]|/(?:Users|home)/[A-Za-z0-9._-]+/")
TEXT = {".py", ".md", ".csv", ".json", ".yaml", ".toml", ".txt"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(workspace: Path) -> dict:
    sources = []
    omissions = []

    def copy(source: Path, destination: Path, category: str) -> None:
        destination = destination.resolve()
        if not destination.is_relative_to(ROOT):
            raise ValueError("Export destination escaped release directory")
        if source.suffix in TEXT and LOCAL_PATH.search(source.read_text(encoding="utf-8")):
            omissions.append(dict(source=source.relative_to(workspace).as_posix(),
                                  bytes=source.stat().st_size, sha256=sha(source),
                                  reason="Local machine paths; originals retained outside public release"))
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        sources.append(dict(path=destination.relative_to(ROOT).as_posix(),
                            source=source.relative_to(workspace).as_posix(),
                            category=category, bytes=destination.stat().st_size,
                            sha256=sha(source), exact_copy=sha(source) == sha(destination)))

    for source in sorted((workspace / "src").rglob("*.py")):
        copy(source, ROOT / source.relative_to(workspace), "original_scientific_source")
    for source in sorted((workspace / "supplementary_study/study").glob("*.py")):
        copy(source, ROOT / "src/study" / source.name, "supplementary_scientific_source")
    for source in sorted((workspace / "tests").rglob("*.py")):
        copy(source, ROOT / "tests/archived_original" / source.relative_to(workspace / "tests"),
             "archived_tests_not_default_executed")
    for source in sorted((workspace / "workstreams").rglob("*.yaml")):
        copy(source, ROOT / "configs/original" / source.relative_to(workspace / "workstreams"),
             "original_config_and_snapshot")
    copy(workspace / "shared/configs/simulation_defaults.yaml",
         ROOT / "configs/original/shared/simulation_defaults.yaml", "shared_config")
    copy(workspace / "requirements.lock", ROOT / "configs/environments/original.requirements.lock",
         "recorded_environment")
    copy(workspace / "supplementary_study/requirements.lock",
         ROOT / "configs/environments/supplementary.requirements.lock", "recorded_environment")
    for source in sorted((workspace / "workstreams").rglob("*.md")):
        copy(source, ROOT / "docs/original" / source.relative_to(workspace / "workstreams"),
             "original_protocol_and_diagnostic")

    for source in sorted((workspace / "workstreams").rglob("*")):
        if not source.is_file() or "artifacts" not in source.parts:
            continue
        if source.suffix not in {".csv", ".json"}:
            continue
        relative = source.relative_to(workspace / "workstreams")
        if "batch_summary" in source.name or "bootstrap_intercepts" in source.name:
            omissions.append(dict(source=source.relative_to(workspace).as_posix(),
                                  bytes=source.stat().st_size, sha256=sha(source),
                                  reason="Compact export: historical batches/bootstrap draws remain in audit archives"))
            continue
        copy(source, ROOT / "artifacts/canonical_paper_export/original" / relative,
             "original_saved_summary")

    baseline = workspace / "figure_redraws/20261009/baseline/supplementary_results"
    for source in sorted(baseline.rglob("*")):
        if not source.is_file() or source.suffix == ".zip":
            continue
        relative = source.relative_to(baseline)
        copy(source, ROOT / "artifacts/canonical_paper_export/supplementary" / relative,
             "integrated_baseline_saved_evidence")
    copy(baseline / "PROTOCOL_FROZEN.json", ROOT / "configs/supplementary/PROTOCOL_FROZEN.json",
         "supplementary_frozen_protocol_and_seeds")
    copy(workspace / "supplementary_study/results/SUPPLEMENTARY_EXPERIMENTS_HANDOFF/tests/gate.json",
         ROOT / "artifacts/canonical_paper_export/supplementary/validation/E0_gate.json",
         "saved_E0_validation_not_rerun")

    manifests = ROOT / "docs/manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    with (manifests / "EXACT_COPY_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "source", "category", "bytes", "sha256", "exact_copy"])
        writer.writeheader()
        writer.writerows(sources)
    with (manifests / "COMPACT_OMISSIONS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "bytes", "sha256", "reason"])
        writer.writeheader()
        writer.writerows(omissions)
    report = dict(copied_files=len(sources), copied_bytes=sum(row["bytes"] for row in sources),
                  omitted_files=len(omissions), no_training_or_refitting=True,
                  original_git_commit="7f6de2cea1f20db958163af0c4e020ae57ff2b65",
                  scope="Compact publication source/evidence export, not a published version tag")
    (manifests / "EXPORT_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=ROOT.parent)
    print(json.dumps(build(parser.parse_args().workspace.resolve()), indent=2))
