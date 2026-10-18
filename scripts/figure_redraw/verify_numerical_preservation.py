"""Independent, read-only audit of seven presentation-only figure sidecars.

The expected records come from the original saved CSVs, never the renderer.
No experiment, fit, bootstrap, or saved scientific input is executed/modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


PANELS = (
    "hist_matched_H2",
    "hist_matched_H4",
    "hist_fixed_gamma_coord1",
    "hist_fixed_gamma_coord2",
    "real_R0_allocation",
    "hist_H4_smallstep",
    "hist_H4_loglog_residual",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_map(workspace: Path) -> dict[str, Path]:
    old = workspace / "review_exports/20261009/staging/REVIEW_CORE/historical_repository"
    roots = {
        "p3_primary": old / "p3/formal/p3-d2-matched-attribution-primary",
        "p3_smallstep": old / "p3/formal/p3-d2-matched-attribution-h4-small-step-confirmation",
        "p3_diagnostic": old / "p3/formal/p3-d2-matched-attribution-h4-diagnostic",
        "p2_plateau": old / "p2/formal/p2-d2-fixed-gamma-largeN-plateau",
        "supplement": workspace / "figure_redraws/20261009/baseline/supplementary_results/figure_data",
    }
    files = {
        "p3_primary": ["paired_setting_summary.csv", "paired_fit_summary.csv"],
        "p3_smallstep": ["paired_setting_summary.csv", "paired_fit_summary.csv"],
        "p3_diagnostic": ["pointwise_diagnostics.csv", "scaling_summary.csv"],
        "p2_plateau": ["setting_summary.csv", "plateau_fit_summary.csv", "plateau_fit_curve.csv"],
        "supplement": ["E3_allocation_signed_projection.csv"],
    }
    return {f"inputs/{key}/{name}": roots[key] / name for key in roots for name in files[key]}


def selected_rows(panel: str, inputs: dict[str, list[dict]]) -> tuple[str, list[int]]:
    if panel.startswith("hist_matched_") or panel == "hist_H4_smallstep":
        root = "p3_smallstep" if panel == "hist_H4_smallstep" else "p3_primary"
        h = 2 if panel == "hist_matched_H2" else 4
        name = f"inputs/{root}/paired_setting_summary.csv"
        return name, [i for i, row in enumerate(inputs[name], 1) if int(row["H"]) == h]
    if panel.startswith("hist_fixed_gamma_"):
        coord = 0 if panel.endswith("coord1") else 1
        name = "inputs/p2_plateau/setting_summary.csv"
        return name, [i for i, row in enumerate(inputs[name], 1)
                      if row["estimator"] == "stationary_mean_balance" and int(row["coordinate"]) == coord]
    if panel == "hist_H4_loglog_residual":
        name = "inputs/p3_diagnostic/pointwise_diagnostics.csv"
        return name, list(range(1, len(inputs[name]) + 1))
    name = "inputs/supplement/E3_allocation_signed_projection.csv"
    return name, [i for i, row in enumerate(inputs[name], 1)
                  if row["regime"] == "R0" and "allocation" in row["roles"].split(";")
                  and int(row["H"]) == 4 and abs(float(row["gamma"]) - 0.19607843137254902) <= 1e-15
                  and (int(row["N"]), int(row["m"])) in {(8, 32), (32, 8), (128, 2)}]


def fit_rows(panel: str, inputs: dict[str, list[dict]]) -> tuple[str, list[int]] | None:
    if panel.startswith("hist_matched_") or panel == "hist_H4_smallstep":
        root = "p3_smallstep" if panel == "hist_H4_smallstep" else "p3_primary"
        h = 2 if panel == "hist_matched_H2" else 4
        name = f"inputs/{root}/paired_fit_summary.csv"
        return name, [i for i, row in enumerate(inputs[name], 1) if int(row["H"]) == h]
    if panel.startswith("hist_fixed_gamma_"):
        coord = 0 if panel.endswith("coord1") else 1
        name = "inputs/p2_plateau/plateau_fit_summary.csv"
        return name, [i for i, row in enumerate(inputs[name], 1) if int(row["coordinate"]) == coord]
    return None


def active_graph(baseline: Path) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def walk(relative: str) -> None:
        if relative in seen:
            return
        seen.add(relative)
        ordered.append(relative)
        text = (baseline / relative).read_text(encoding="utf-8-sig")
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        for match in re.finditer(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            child = match.group(1)
            if not child.endswith(".tex"):
                child += ".tex"
            walk(child)

    walk("main.tex")
    return ordered


def capture(workspace: Path, out: Path) -> dict:
    baseline = workspace / "figure_redraws/20261009/baseline"
    mapping = source_map(workspace)
    protected_paths: set[Path] = set(mapping.values())
    for root in {path.parent for path in mapping.values()}:
        protected_paths.update(path for path in root.iterdir()
                               if path.suffix.lower() in {".csv", ".json", ".yaml", ".yml", ".npz"})
    protected_paths.update(path for path in (baseline / "supplementary_results").rglob("*")
                           if path.is_file() and path.suffix.lower() in {".csv", ".json", ".yaml", ".yml", ".npz"})
    manifest = {
        "scope": "Read-only original input protection; no simulations, refits, or resampling.",
        "original_files": {path.relative_to(workspace).as_posix(): sha256(path)
                           for path in sorted(protected_paths)},
        "input_mapping": {name: path.relative_to(workspace).as_posix() for name, path in mapping.items()},
        "active_tex_graph": active_graph(baseline),
        "protected_scientific_tex": {},
        "protected_tables": {},
        "protected_text_outside_figures": {},
    }
    for relative in manifest["active_tex_graph"]:
        text = (baseline / relative).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        if relative not in {"macros.tex", "sections/07_numerical_study.tex", "appendix/C_numerical_details.tex"}:
            manifest["protected_scientific_tex"][relative] = sha256(baseline / relative)
        tables = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", text, re.S)
        if tables:
            manifest["protected_tables"][relative] = [hashlib.sha256(table.encode("utf-8")).hexdigest()
                                                      for table in tables]
        if relative in {"sections/07_numerical_study.tex", "appendix/C_numerical_details.tex"}:
            nonfigures = re.sub(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", "", text, flags=re.S)
            manifest["protected_text_outside_figures"][relative] = hashlib.sha256(nonfigures.encode("utf-8")).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    (out / "original_protection_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify(workspace: Path, manuscript: Path, out: Path, source_input_root: Path | None = None) -> bool:
    portable = source_input_root is not None
    manifest_path = out / "original_protection_manifest.json"
    if not manifest_path.exists():
        manifest_path = Path(__file__).resolve().parent / "original_protection_manifest.json"
    if not manifest_path.exists() and not portable:
        raise RuntimeError("Capture must run before the presentation edits are audited.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    sources = source_map(workspace)
    if portable:
        sources = {name: source_input_root / name for name in sources}
    inputs = {name: read_csv(path) for name, path in sources.items()}
    checks: list[dict] = []

    def check(panel: str, identity: str, field: str, expected, actual, passed: bool | None = None) -> None:
        if passed is None:
            passed = expected == actual
        error = ""
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            error = actual - expected
        checks.append({"panel_id": panel, "record_id": identity, "field": field,
                       "expected": expected, "actual": actual, "absolute_error": abs(error) if error != "" else "",
                       "status": "PASS" if passed else "FAIL"})

    if portable:
        provenance_path = manuscript / "figures/redrawn/data/provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else {}
        provenance_inputs = provenance.get("inputs", {})
        check("PORTABLE_INPUTS", "provenance.json", "complete_input_registry", set(sources), set(provenance_inputs))
        for name, path in sources.items():
            saved = provenance_inputs.get(name, {})
            check("PORTABLE_INPUTS", name, "provenance_sha256", saved.get("sha256", "MISSING"), sha256(path))
            check("PORTABLE_INPUTS", name, "provenance_bytes", saved.get("bytes", "MISSING"), path.stat().st_size)
            original_relative = manifest.get("input_mapping", {}).get(name)
            digest = manifest.get("original_files", {}).get(original_relative)
            if digest:
                check("ARCHIVED_INPUT_RECEIPT", name, "original_input_sha256", digest, sha256(path))
    else:
        for relative, digest in manifest["original_files"].items():
            path = workspace / relative
            actual = sha256(path) if path.exists() else "MISSING"
            check("ORIGINAL_INPUTS", relative, "sha256", digest, actual)
        for name, path in sources.items():
            copied = workspace / "figure_redraws/20261009/pipeline" / name
            check("COPIED_INPUTS", name, "sha256", sha256(path), sha256(copied) if copied.exists() else "MISSING")
        for relative, digest in manifest["protected_scientific_tex"].items():
            path = manuscript / relative
            check("SCIENTIFIC_TEX", relative, "sha256", digest, sha256(path) if path.exists() else "MISSING")
        for relative, expected in manifest["protected_tables"].items():
            path = manuscript / relative
            text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n") if path.exists() else ""
            tables = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", text, re.S)
            actual = [hashlib.sha256(table.encode("utf-8")).hexdigest() for table in tables]
            check("SCIENTIFIC_TABLES", relative, "ordered_table_hashes", expected, actual)
        for relative, expected in manifest.get("protected_text_outside_figures", {}).items():
            path = manuscript / relative
            text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n") if path.exists() else ""
            nonfigures = re.sub(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", "", text, flags=re.S)
            actual = hashlib.sha256(nonfigures.encode("utf-8")).hexdigest()
            check("SCIENTIFIC_NONFIGURE_TEXT", relative, "sha256_without_figures", expected, actual)

    for panel in PANELS:
        sidecar = manuscript / f"figures/redrawn/data/{panel}.csv"
        if not sidecar.exists():
            check(panel, "sidecar", "availability", "PRESENT", "MISSING_SOURCE")
            continue
        records = read_csv(sidecar)
        point_file, selection = selected_rows(panel, inputs)
        points = [record for record in records if record["record_type"] == "point"]
        observed = Counter((record["source_file"], int(record["source_row"])) for record in points)
        check(panel, "selection", "complete_point_rows",
              Counter((point_file, i) for i in selection), observed)
        expected_count = 6 if panel == "real_R0_allocation" else 18 if panel == "hist_H4_loglog_residual" else 8 if panel == "hist_H4_smallstep" else 10 if panel.startswith("hist_matched_") else 5
        check(panel, "selection", "expected_point_count", expected_count, len(points))
        fitted = fit_rows(panel, inputs)
        if fitted:
            fit_file, fit_selection = fitted
            for kind in ("intercept", "target"):
                actual = Counter((record["source_file"], int(record["source_row"]))
                                 for record in records if record["record_type"] == kind)
                check(panel, "selection", f"complete_{kind}_rows",
                      Counter((fit_file, i) for i in fit_selection), actual)
            if panel.startswith("hist_fixed_gamma_"):
                curve_file = "inputs/p2_plateau/plateau_fit_curve.csv"
                coord = 0 if panel.endswith("coord1") else 1
                expected_vertices = [(curve_file, i, float(row["inverse_N"]))
                                     for i, row in enumerate(inputs[curve_file], 1) if int(row["coordinate"]) == coord]
                expected_vertices += [(fit_file, i, 0.0) for i in fit_selection]
            else:
                expected_vertices = []
                for i in fit_selection:
                    fit = inputs[fit_file][i - 1]
                    coord = int(fit["coordinate"])
                    xs = [float(inputs[point_file][j - 1]["delta"]) for j in selection
                          if int(inputs[point_file][j - 1]["coordinate"]) == coord]
                    expected_vertices += [(fit_file, i, x) for x in [0.0, *xs]]
            actual_vertices = [(record["source_file"], int(record["source_row"]), float(record["x_original"]))
                               for record in records if record["record_type"] == "fit_curve"]
            check(panel, "selection", "complete_saved_fit_vertices", Counter(expected_vertices), Counter(actual_vertices))
        else:
            check(panel, "selection", "no_introduced_fit_or_target", 0,
                  sum(record["record_type"] != "point" for record in records))

        for record_number, record in enumerate(records, 1):
            identity = f"{record_number}:{record.get('row_id', '')}:{record['record_type']}"
            name = record["source_file"]
            if name not in inputs:
                check(panel, identity, "source_file", "AUTHORITATIVE_MAPPING", name, False)
                continue
            source_row = int(record["source_row"])
            if not 1 <= source_row <= len(inputs[name]):
                check(panel, identity, "source_row", "VALID_ORIGINAL_ROW", source_row, False)
                continue
            source = inputs[name][source_row - 1]
            check(panel, identity, "source_sha256", sha256(sources[name]), record["source_sha256"])
            check(panel, identity, "panel_id", panel, record["panel_id"])
            check(panel, identity, "x_scale", 1.0, float(record["x_scale"]))
            check(panel, identity, "y_scale", 1000.0 if panel == "real_R0_allocation" else 1.0,
                  float(record["y_scale"]))
            check(panel, identity, "x_transform", "categorical" if panel == "real_R0_allocation" else "identity",
                  record["x_transform"])
            expected_y_transform = "scale" if panel == "real_R0_allocation" else "abs" if panel == "hist_H4_loglog_residual" else "identity"
            check(panel, identity, "y_transform", expected_y_transform, record["y_transform"])
            for metadata in ("H", "N", "m", "gamma"):
                if metadata in source and source[metadata]:
                    check(panel, identity, metadata, float(source[metadata]), float(record[metadata]))
            if "coordinate" in source:
                check(panel, identity, "coordinate", int(source["coordinate"]), int(record["coordinate"]))
                check(panel, identity, "display_coordinate", int(source["coordinate"]) + 1, int(record["display_coordinate"]))
            if "algorithm" in source:
                check(panel, identity, "algorithm", source["algorithm"], record["algorithm"])
            if "setting_id" in source and record["record_type"] == "point":
                check(panel, identity, "row_id_contains_setting", True, source["setting_id"] in record["row_id"])
            if "cell_id" in source and record["record_type"] == "point":
                check(panel, identity, "row_id_contains_cell", True, source["cell_id"] in record["row_id"])

            for value in ("x", "y", "ci_low", "ci_high", "target"):
                column = record.get(f"{value}_column", "")
                original = record.get(f"{value}_original", "")
                if not original:
                    continue
                if column in source:
                    check(panel, identity, f"{value}_original", float(source[column]), float(original))
                elif value == "y" and record["record_type"] == "target" and record.get("target_column") in source:
                    check(panel, identity, "target_y_original", float(source[record["target_column"]]), float(original))
                elif value == "y" and record["record_type"] == "fit_curve" and "beta0" in source:
                    expected = float(source["beta0"]) + float(source["beta1"]) * float(record["x_original"])
                    check(panel, identity, "saved_fit_y", expected, float(original))
                elif value == "x" and record["record_type"] in {"intercept", "target"}:
                    check(panel, identity, "reference_x", 0.0, float(original))
                elif value == "x" and record["record_type"] == "fit_curve" and "beta0" in source:
                    pass  # Complete permitted vertices were independently checked above.
                else:
                    check(panel, identity, f"{value}_column", "EXPLICIT_AUTHORITY", column, False)

                display = record.get(f"{value}_display", "")
                if display:
                    scale = float(record["x_scale"] if value == "x" else record["y_scale"])
                    transform = record["x_transform"] if value == "x" else record["y_transform"]
                    original_float = float(original)
                    if transform == "categorical" and value == "x":
                        expected_display = {8: 0.0, 32: 1.0, 128: 2.0}[int(original_float)]
                    else:
                        expected_display = (abs(original_float) if transform == "abs" else original_float) * scale
                    check(panel, identity, f"{value}_display_full_precision", expected_display, float(display))
                    if transform != "categorical":
                        restored = float(display) / scale
                        expected_restored = abs(original_float) if transform == "abs" else original_float
                        tolerance = math.ulp(expected_restored) if expected_restored else 0.0
                        check(panel, identity, f"{value}_transform_inversion", expected_restored, restored,
                              abs(restored - expected_restored) <= tolerance)
            for coefficient in ("beta0", "beta1"):
                if record.get(coefficient, ""):
                    if coefficient in source:
                        check(panel, identity, coefficient, float(source[coefficient]), float(record[coefficient]))
                    else:
                        check(panel, identity, coefficient, "SOURCE_COEFFICIENT", record[coefficient], False)
            if "paired_fit_summary" in name and int(source["H"]) == 4 and record["record_type"] == "intercept":
                target = float(source["B20_ctrl_component"])
                low, high = float(source["simultaneous_ci_low"]), float(source["simultaneous_ci_high"])
                check(panel, identity, "historical_H4_target_exclusion", True, not low <= target <= high)

    write_csv(out / "NUMERICAL_PRESERVATION_INDEPENDENT.csv", checks)
    failures = [row for row in checks if row["status"] != "PASS"]
    summary = {"status": "PASS" if not failures else "FAIL", "mode": "PORTABLE_NUMERICAL_RECHECK" if portable else "FULL_ORIGINAL_WORKSPACE_AUDIT",
               "checks": len(checks), "failed_checks": len(failures), "failure_details": failures,
               "original_files_protected": 0 if portable else len(manifest["original_files"]),
               "protected_scientific_tex": 0 if portable else len(manifest["protected_scientific_tex"]),
               "input_csvs_checked": len(sources),
               "broader_original_and_proof_preservation": {
                   "status": "ARCHIVED_RECEIPT_NOT_REEXECUTED" if portable else "REEXECUTED",
                   "receipt_available": bool(manifest),
                   "archived_original_file_count": len(manifest.get("original_files", {})),
                   "archived_scientific_tex_count": len(manifest.get("protected_scientific_tex", {})),
                   "reason": "Portable mode has only the ten bundled plotting-input CSVs; the broader original workspace/proof checks are not claimed as rerun." if portable else "Original workspace files and manuscript scientific content were checked in this execution.",
               },
               "panels": list(PANELS), "no_simulation": True, "no_refit": True, "no_resampling": True,
               "scope_limits": ["This audit checks numeric records and protected source content, not image pixels, final font sizes, or theorem correctness.",
                                "Exact binary comparisons use Python float conversion of original CSV strings; no rounded manuscript-table values.",
                                "Display inversion permits at most one source-value ULP to account for binary multiplication/division."]}
    (out / "NUMERICAL_AUDIT_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    return not failures


def main() -> None:
    parser = argparse.ArgumentParser()
    script_parents = Path(__file__).resolve().parents
    default_workspace = script_parents[3] if len(script_parents) > 3 else Path.cwd()
    parser.add_argument("--workspace", type=Path, default=default_workspace)
    parser.add_argument("--manuscript", type=Path)
    parser.add_argument("--input-root", "--source-input-root", dest="input_root", type=Path,
                        help="Portable mode: directory containing the bundled inputs/ subdirectory.")
    parser.add_argument("--output", type=Path, help="Write audit reports here instead of beside this script.")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    out = args.output.resolve() if args.output else Path(__file__).resolve().parent
    if args.capture:
        if args.input_root:
            parser.error("--capture cannot be combined with portable --input-root mode.")
        manifest = capture(workspace, out)
        print(f"Captured {len(manifest['original_files'])} original scientific files; no output figures validated yet.")
    else:
        manuscript = (args.manuscript or workspace / "manuscript").resolve()
        success = verify(workspace, manuscript, out, args.input_root.resolve() if args.input_root else None)
        print("Independent numerical audit: " + ("PASS" if success else "FAIL; inspect saved report."))
        if args.input_root:
            print("Portable scope: seven panel numerical records and ten bundled CSV hashes rechecked; broader original/proof preservation is archived evidence, not re-executed.")
        raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
