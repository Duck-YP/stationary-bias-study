"""Render all five manuscript figures (nine panels) from frozen saved outputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
CANONICAL = ROOT / "artifacts/canonical_paper_export/figure_redraw"
PANELS = MANUSCRIPT / "figures/redrawn"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs() -> dict[str, str]:
    provenance = json.loads((PANELS / "data/provenance.json").read_text())
    expected = {(CANONICAL / name).resolve(): item["sha256"]
                for name, item in provenance["inputs"].items()}
    if any(not path.is_relative_to(CANONICAL.resolve()) for path in expected):
        raise ValueError("Input path escaped canonical figure inputs")
    for sidecar in sorted((PANELS / "data").glob("hist_*.csv")) + [PANELS / "data/real_R0_allocation.csv"]:
        with sidecar.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                path = (CANONICAL / row["source_file"]).resolve()
                if not path.is_relative_to(CANONICAL.resolve()):
                    raise ValueError("Input path escaped canonical figure inputs")
                if expected.get(path) != row["source_sha256"]:
                    raise ValueError("Sidecar/provenance source hash disagreement")
    e4 = json.loads((PANELS / "data/e4_provenance.json").read_text())
    source = MANUSCRIPT / "supplementary_results/E4/BIAS_VARIANCE_MSE.csv"
    expected[source] = e4[0]["source_sha256"]
    assert len(expected) == 11
    for path, digest in expected.items():
        if not path.is_file() or sha(path) != digest:
            raise ValueError("Frozen input missing or changed: " + path.relative_to(ROOT).as_posix())
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in expected.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="A new or empty output directory; never the frozen manuscript figures")
    args = parser.parse_args()
    output = args.output.resolve()
    for frozen in (MANUSCRIPT, ROOT / "artifacts", ROOT / "configs", ROOT / "src"):
        if output == frozen.resolve() or output.is_relative_to(frozen.resolve()):
            parser.error("--output must be outside frozen manuscript/source/configuration/artifact directories")
    if output.exists() and any(output.iterdir()):
        parser.error("--output must be new or empty")
    source_hashes = verify_inputs()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", str(output.parent / ".mplconfig"))

    def run(*arguments):
        subprocess.run([sys.executable, "-B", *map(str, arguments)],
                       cwd=ROOT, env=env, check=True)

    run(ROOT / "manuscript/tools/figure_layout/redraw_figures.py",
        "--input-root", CANONICAL, "--output", output)
    # Preserve the original E4 renderer and its relative-layout assumptions.
    # Only its saved CSV and plotting source are copied into this scratch tree.
    with tempfile.TemporaryDirectory(prefix="e4_plot_", dir=output.parent) as temporary:
        scratch = Path(temporary) / "manuscript"
        (scratch / "tools").mkdir(parents=True)
        (scratch / "supplementary_results/E4").mkdir(parents=True)
        shutil.copy2(MANUSCRIPT / "tools/plot_e4_for_manuscript.py", scratch / "tools")
        shutil.copy2(MANUSCRIPT / "supplementary_results/E4/BIAS_VARIANCE_MSE.csv",
                     scratch / "supplementary_results/E4")
        run(scratch / "tools/plot_e4_for_manuscript.py")
        for path in sorted((scratch / "figures/redrawn").rglob("*")):
            if path.is_file():
                destination = output / path.relative_to(scratch / "figures/redrawn")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
    run(ROOT / "scripts/compare_figure_replay.py", "--group", "all",
        "--replay", output, "--output", output / "REPRODUCTION_REPORT.json")
    assert source_hashes == verify_inputs(), "Frozen figure inputs changed during rendering"
    print(json.dumps({"status": "PASS", "figure_groups": 5, "panels": 9,
                      "frozen_inputs": len(source_hashes), "output": str(output),
                      "no_simulation": True, "no_refit": True, "no_resampling": True}))


if __name__ == "__main__":
    main()
