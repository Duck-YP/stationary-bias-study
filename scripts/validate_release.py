"""Validate compact release hashes and records without rerunning experiments."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_files import public_files
LOCAL_PATH = re.compile(r"[A-Z]:[\\/]|/(?:Users|home)/[A-Za-z0-9._-]+/")
PANELS = {"hist_matched_H2", "hist_matched_H4", "hist_fixed_gamma_coord1",
          "hist_fixed_gamma_coord2", "real_R0_allocation", "hist_H4_smallstep",
          "hist_H4_loglog_residual"}


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_path(relative):
    path = (ROOT / relative).resolve()
    assert path.is_relative_to(ROOT.resolve()) and path.is_file(), relative
    return path


def check_copy_manifest(name):
    """Verify public bytes and the claimed relationship to source bytes.

    Sources are checked when the original workspace is present. A portable
    release instead checks source hashes against the retained provenance.
    Archive-member source labels are provenance, not filesystem paths.
    """
    rows = csv_rows(ROOT / "docs/manifests" / name)
    assert rows and len({r["path"] for r in rows}) == len(rows), name
    local_sources = 0
    for row in rows:
        path = public_path(row["path"])
        assert path.stat().st_size == int(row["bytes"]), row["path"]
        assert file_sha(path) == row["sha256"], row["path"]
        assert re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"]), row["path"]
        if row["exact_copy"] == "True":
            assert row["source_sha256"] == row["sha256"], row["path"]
        else:
            assert row["exact_copy"] == "False", row["path"]
            if "reason" in row:
                assert row["reason"].strip(), "Unexplained public variant: " + row["path"]
        if "!" in row["source"]:
            archive_name, member = row["source"].split("!", 1)
            archive_path = (ROOT.parent / archive_name).resolve()
            assert archive_path.is_relative_to(ROOT.parent.resolve()), archive_name
            if archive_path.is_file():
                with zipfile.ZipFile(archive_path) as archive:
                    assert hashlib.sha256(archive.read(member)).hexdigest() == row["source_sha256"], row["source"]
                local_sources += 1
        else:
            source = (ROOT.parent / row["source"]).resolve()
            assert source.is_relative_to(ROOT.parent.resolve()), row["source"]
            if source.is_file() and not source.is_relative_to(ROOT.resolve()):
                assert file_sha(source) == row["source_sha256"], "Source changed: " + row["source"]
                local_sources += 1
    return rows, local_sources


def check_tex_assets(entry):
    """Check literal TeX inputs/assets without compiling or executing TeX."""
    manuscript = ROOT / "manuscript"
    pending, visited, assets = [public_path(entry)], set(), set()
    commands = re.compile(r"\\(input|include|includegraphics\*?|bibliography|addbibresource)\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}")
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        text = re.sub(r"(?<!\\)%[^\n]*", "", path.read_text(encoding="utf-8"))
        for command, argument in commands.findall(text):
            names = argument.split(",") if command == "bibliography" else [argument]
            for name in names:
                name = name.strip()
                assert not any(c in name for c in "#\\"), "Unresolved dynamic TeX asset: " + name
                extensions = (".tex",) if command in {"input", "include"} else ((".bib",) if command in {"bibliography", "addbibresource"} else (".pdf", ".png", ".jpg", ".jpeg", ".eps"))
                candidates = []
                for base in (manuscript, path.parent):
                    candidate = base / name
                    candidates.extend([candidate] if candidate.suffix else [candidate.with_suffix(suffix) for suffix in extensions])
                resolved = next((p.resolve() for p in candidates if p.is_file()), None)
                assert resolved is not None and resolved.is_relative_to(manuscript.resolve()), (path.relative_to(ROOT), name)
                assets.add(resolved)
                if command in {"input", "include"}:
                    pending.append(resolved)
    return {"active_tex_files": len(visited), "referenced_assets": len(assets),
            "paths": sorted(p.relative_to(ROOT).as_posix() for p in visited | assets)}


def check_targeted_records(base):
    """Check completeness of saved targeted evidence, without refitting it."""
    protocol = json.loads((base / "PROTOCOL_FROZEN.json").read_text(encoding="utf-8"))
    cells, seeds = protocol["cells"], protocol["production_seeds"]
    conditions = {"rho_minus_symmetric", "rho_zero_symmetric", "rho_plus_symmetric", "rho_plus_asymmetric"}
    expected_cells = {(c, n, g) for c in conditions for n in (64, 128) for g in (1/512, 1/1024, 1/2048)}
    actual_cells = {(c["condition"], c["N"], c["gamma"]) for c in cells}
    assert len(cells) == len(actual_cells) == 24 and actual_cells == expected_cells
    assert protocol["H"] == 4 and len(seeds) == len(set(seeds)) == 12
    assert set(seeds).isdisjoint(protocol["pilot_seeds"])
    assert protocol["bootstrap_draws"] >= 2000
    assert protocol["cpu_cap_seconds"] == 6 * 3600
    assert all(c["schedule"]["batches"] == 64 for c in cells)
    results = base / "results"
    observables, estimators = {"SCAFFOLD", "FedAvg", "difference"}, {"balance", "raw"}
    expected_runs = {(c, n, g, seed) for c, n, g in expected_cells for seed in seeds}
    runs = csv_rows(results / "per_run_vectors.csv")
    keys = {(r["condition"], int(r["N"]), float(r["gamma"]), int(r["seed"]), r["estimator"], r["observable"], int(r["coordinate"])) for r in runs}
    expected = {(*run, e, a, j) for run in expected_runs for e in estimators for a in observables for j in (1, 2)}
    assert len(runs) == len(keys) == 3456 and keys == expected, "Incomplete targeted per-run vectors"
    assert all(all(r[name] != "" for name in ("coefficient", "first_half", "last_half", "last_minus_first")) for r in runs)

    grid = csv_rows(results / "full_grid.csv")
    grid_keys = {(r["condition"], int(r["N"]), float(r["gamma"]), r["estimator"], r["observable"], int(r["coordinate"])) for r in grid}
    assert len(grid) == len(grid_keys) == 288
    assert grid_keys == {(*cell, e, a, j) for cell in expected_cells for e in estimators for a in observables for j in (1, 2)}
    assert all(int(r["count"]) == 12 for r in grid)

    fits = csv_rows(results / "intercepts_and_contrasts.csv")
    primary = csv_rows(results / "primary_family_36.csv")
    family = {(kind, comparison, a, j)
              for kind, comparisons in (("intercept", conditions),
                  ("law_contrast", {"rho_plus_symmetric minus rho_plus_asymmetric"}),
                  ("signed_covariance_contrast", {"rho_plus_symmetric minus rho_minus_symmetric"}))
              for comparison in comparisons for a in observables for j in (1, 2)}
    groups = {(r["estimator"], r["grid"]) for r in fits}
    assert groups == {(e, g) for e in estimators for g in ("full", "omit_largest_gamma")}
    assert len(fits) == 144 and len(primary) == 36
    for estimator, grid_name in groups:
        part = [r for r in fits if (r["estimator"], r["grid"]) == (estimator, grid_name)]
        assert len(part) == 36 and {(r["kind"], r["comparison"], r["observable"], int(r["coordinate"])) for r in part} == family
    assert primary == [r for r in fits if r["estimator"] == "balance" and r["grid"] == "full"]
    # Unfavourable intervals/statuses remain part of the immutable evidence;
    # release validation deliberately does not demand scientific "PASS" rows.
    assert all(r["status"] in {"SUPPORTS_WITHIN_REPORTED_RESOLUTION", "INCONCLUSIVE_PRECISION",
                               "DISCREPANCY_REQUIRES_AUDIT", "IMPLEMENTATION_ERROR", "RESOURCE_LIMITED"} for r in fits)

    costs = csv_rows(results / "simulation_costs.csv")
    assert len(costs) == 288
    assert {(r["condition"], int(r["N"]), float(r["gamma"]), int(r["seed"])) for r in costs} == expected_runs
    execution = json.loads((results / "execution_diagnostics.json").read_text(encoding="utf-8"))
    assert execution["completed_runs"] == 288
    assert abs(sum(float(r["cpu_seconds"]) for r in costs) / 3600 - execution["production_cpu_hours"]) < 1e-12
    identity = csv_rows(results / "finite_window_identity.csv")
    identity_keys = {(r["condition"], int(r["N"]), float(r["gamma"]), int(r["seed"]), r["window"], r["observable"], int(r["coordinate"])) for r in identity}
    assert len(identity) == len(identity_keys) == 5184
    assert identity_keys == {(*run, window, a, j) for run in expected_runs for window in ("primary", "first_half", "last_half") for a in observables for j in (1, 2)}
    return dict(targeted_configurations=24, targeted_paired_runs=288,
                targeted_primary_summaries=36, targeted_estimator_grid_families=len(groups),
                targeted_finite_window_identity_rows=len(identity))


def check_presentation_revision(record, graphics):
    """Bind the imported layout QA to the current PDF and all nine panel assets.

    This checks saved QA receipts and saved values; it does not compile TeX,
    remeasure fonts, refit coefficients or rerun the archived baseline audit.
    """
    revision = record["presentation_revision"]
    assert revision["date"] == "2026-10-18"
    build = json.loads(public_path(revision["build_report"]).read_text(encoding="utf-8"))
    fonts = json.loads(public_path(revision["font_audit"]).read_text(encoding="utf-8"))
    numeric = json.loads(public_path(revision["numeric_invariance"]).read_text(encoding="utf-8"))
    from pypdf import PdfReader
    assert len(PdfReader(public_path(revision["comparison"])).pages) > 0
    pdf = record["main_pdf"]
    assert build["sha256"] == fonts["pdf_sha256"] == pdf["sha256"]
    assert build["pages"] == fonts["pages"] == pdf["pages"] == 40
    assert build["bytes"] == pdf["bytes"]
    assert build["unresolved_references"] is False and build["duplicate_labels"] is False
    assert build["overfull_boxes"] == 0 and build["build_sequence"].strip()
    assert set(build["warnings"]) <= {"Package epstopdf Warning: Shell escape feature is not enabled."}

    expected = PANELS | {"e4_averaging_scaffold", "e4_averaging_fedavg"}
    assert graphics == {f"figures/redrawn/{panel}.pdf" for panel in expected}
    assert fonts["status"] == "PASS" and not fonts["failures"]
    assert len(fonts["panels"]) == 9 and {r["panel"] for r in fonts["panels"]} == expected
    required = {"one_source_page", "all_source_text_present_at_inclusion",
                "effective_font_at_least_9_TeX_pt", "text_matrix_matches_placement_scale",
                "all_fonts_embedded", "no_raster_images", "no_text_clipped_by_canvas"}
    for row in fonts["panels"]:
        path = public_path(f"manuscript/figures/redrawn/{row['panel']}.pdf")
        assert file_sha(path) == row["source_sha256"]
        assert row["pass"] is True and required <= set(row["checks"])
        assert all(value is True for value in row["checks"].values())
        assert row["fonts"] and all(face["embedded"] is True for face in row["fonts"])
        assert float(row["minimum_effective_TeX_pt"]) >= 9.-.005
        assert 1 <= int(row["page"]) <= pdf["pages"] and row["glyph_count"] > 0

    assert numeric["status"] == "PASS" and numeric["checks"] == len(numeric["results"])
    assert numeric["results"] and all(row["pass"] is True for row in numeric["results"])
    sidecars = [r for r in numeric["results"] if r["check"] == "complete_baseline_sidecar_records"]
    assert len(sidecars) == 9 and {r["panel"] for r in sidecars} == expected
    for row in sidecars:
        path = public_path(f"manuscript/figures/redrawn/data/{row['panel']}.csv")
        assert row["byte_identical"] is True and len(csv_rows(path)) == row["rows"]

    # Historical seven-panel values are checked by check_publication(). Check
    # the two E4 sidecars directly against the retained saved interval columns.
    source = public_path("manuscript/supplementary_results/E4/BIAS_VARIANCE_MSE.csv")
    saved = csv_rows(source)
    e4_checks = 0
    for algorithm, slug in (("SCAFFOLD", "scaffold"), ("FedAvg", "fedavg")):
        actual = csv_rows(public_path(f"manuscript/figures/redrawn/data/e4_averaging_{slug}.csv"))
        selected = sorted((r for r in saved if r["cell_id"] == "E3_R0_p0_H4_N128_g0.196078431373"
                           and r["algorithm"] == algorithm), key=lambda r: int(r["K"]))
        assert len(actual) == len(selected) == 7
        assert [int(r["K"]) for r in actual] == [1, 2, 4, 8, 16, 32, 64]
        for row, original in zip(actual, selected):
            for key, value in row.items():
                if key in {"cell_id", "algorithm"}:
                    assert value == original[key]
                else:
                    assert float(value) == float(original[key]), (algorithm, row["K"], key)
                e4_checks += 1
    return dict(current_layout_receipts_verified=True, current_final_font_panels=9,
                current_minimum_panel_font_TeX_pt=min(r["minimum_effective_TeX_pt"] for r in fonts["panels"]),
                current_layout_numeric_receipt_checks=numeric["checks"], current_e4_saved_column_checks=e4_checks,
                current_layout_receipt_scope="Imported October 18 clean-build/numeric/font QA, bound to current file hashes; no new compile, font measurement or baseline audit by this validator")


def check_current_manuscript():
    record = json.loads((ROOT / "docs/manifests/CURRENT_MANUSCRIPT_SYNC.json").read_text(encoding="utf-8"))
    source_archives = {
        "20261015": "SCAFFOLD_Targeted_Mechanism_Integrated_20261015.zip",
        "20261018_V2": "Characterizing_Client_Independent_Stationary_Bias_for_SCAFFOLD_and_FedAvg_in_Federated_Learning_V2.zip",
        "20261018_FIGURE_LAYOUT": "Characterizing_Client_Independent_Stationary_Bias_for_SCAFFOLD_and_FedAvg_in_Federated_Learning_V2.zip",
    }
    assert record["schema_version"] == 1 and record["manuscript_version"] in source_archives
    assert record["scientific_recomputation"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", record["source_archive"]["sha256"])
    assert record["source_archive"]["name"] == source_archives[record["manuscript_version"]]
    assert record["historical_receipt_scope"].strip()
    publication = {r["path"]: r for r in csv_rows(public_path(record["publication_manifest"]))}
    for key in ("main_tex", "main_pdf"):
        entry = record[key]
        path = public_path(entry["path"])
        assert path.stat().st_size == int(entry["bytes"])
        assert file_sha(path) == entry["sha256"]
        row = publication[entry["path"]]
        assert row["exact_copy"] == "True" and row["source_sha256"] == row["sha256"] == entry["sha256"]
    from pypdf import PdfReader
    assert len(PdfReader(public_path(record["main_pdf"]["path"])).pages) == record["main_pdf"]["pages"] == 40
    graph = check_tex_assets(record["main_tex"]["path"])
    graphics = {p.removeprefix("manuscript/") for p in graph["paths"] if Path(p).suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".eps"}}
    assert len(record["active_graphics"]) == len(set(record["active_graphics"])) == 9
    assert graphics == set(record["active_graphics"]), "Current active TeX graphics differ from sync receipt"
    for name in graph["paths"]:
        row = publication[name]
        assert row["exact_copy"] == "True" and row["sha256"] == file_sha(public_path(name)), name
    build_scope = "Copied source PDF; TeX was not recompiled by release validation"
    pdf_status = {}
    if record["manuscript_version"] == "20261018_V2":
        pdf = record["main_pdf"]
        # This is the recorded October 15 PDF hash, not a build of V2 TeX.
        assert pdf["sha256"] == "1bea9883e8f828f3a4c7029ed26fdcced6808d3420470a09ccbcdd346232be1f"
        assert pdf["unchanged_from_previous"] is True
        assert pdf["source_tex_correspondence_verified"] is False
        assert pdf["matches_current_tex"] is False and pdf["note"].strip()
        retained = record["retained_local_files"]
        assert len(retained) == 1 and retained[0]["path"] == "manuscript/main.bbl"
        bibliography = retained[0]
        assert bibliography["reason"].strip()
        assert file_sha(public_path(bibliography["path"])) == bibliography["sha256"]
        assert publication[bibliography["path"]]["sha256"] == bibliography["sha256"]
        build_scope = ("Supplied PDF is the unchanged October 15 build and does not reflect V2 TeX edits; "
                       "PDF/TeX correspondence is not verified; no recompilation")
        pdf_status = dict(current_pdf_unchanged_from_previous=True,
                          current_pdf_source_tex_correspondence_verified=False,
                          current_pdf_matches_current_tex=False,
                          current_retained_local_files=len(retained))
    elif record["manuscript_version"] == "20261018_FIGURE_LAYOUT":
        pdf = record["main_pdf"]
        assert pdf["sha256"] == "81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c"
        assert pdf["unchanged_from_previous"] is False
        assert pdf["source_tex_correspondence_verified"] is True
        assert pdf["matches_current_tex"] is True and pdf["note"].strip()
        assert graph["active_tex_files"] == 13
        retained = record["retained_local_files"]
        assert len(retained) == 1 and retained[0]["path"] == "manuscript/main.bbl"
        bibliography = retained[0]
        assert bibliography["reason"].strip()
        assert file_sha(public_path(bibliography["path"])) == bibliography["sha256"]
        assert publication[bibliography["path"]]["sha256"] == bibliography["sha256"]
        build_scope = ("Copied verified October 18 V2 figure/layout clean build; "
                       "PDF/TeX correspondence and nine-panel QA are retained receipts, not a new compile by release validation")
        pdf_status = dict(current_pdf_unchanged_from_previous=False,
                          current_pdf_source_tex_correspondence_verified=True,
                          current_pdf_matches_current_tex=True,
                          current_retained_local_files=len(retained),
                          **check_presentation_revision(record, graphics))
    return dict(current_manuscript_copy_verified=True, current_manuscript_version=record["manuscript_version"],
                current_manuscript_pages=record["main_pdf"]["pages"], current_active_tex_files=graph["active_tex_files"],
                current_active_graphics=len(graphics), current_build_scope=build_scope, **pdf_status)


def check_targeted_transcription(base):
    """Match all selected saved numbers to their actual manuscript rows."""
    selection_path = ROOT / "manuscript/revision_audit/targeted_mechanism_20261015/new_numeric_selections.json"
    selections = json.loads(selection_path.read_text(encoding="utf-8"))
    rows = csv_rows(base / "results/primary_family_36.csv")
    lookup = {(r["comparison"], r["observable"], int(r["coordinate"])): r for r in rows}
    keys = [(r["comparison"], r["observable"], r["coordinate"]) for r in selections]
    assert len(keys) == len(set(keys)) == 36 and set(keys) == set(lookup)
    main = (ROOT / "manuscript/sections/07_numerical_study.tex").read_text(encoding="utf-8")
    appendix = (ROOT / "manuscript/appendix/C_numerical_details.tex").read_text(encoding="utf-8")
    def block(text, label):
        assert text.count("\\label{" + label + "}") == 1, label
        return text.split("\\label{" + label + "}", 1)[1].split("\\end{table}", 1)[0]
    controls = block(main, "tab:mechanism-controls")
    complement = block(appendix, "tab:mechanism-complement")
    conditions = {"rho_minus_symmetric": ("$-1/4$", "Symmetric", "$-1/4$, sym."),
                  "rho_zero_symmetric": ("$0$", "Symmetric", "$0$, sym."),
                  "rho_plus_symmetric": ("$+1/4$", "Symmetric", "$+1/4$, sym."),
                  "rho_plus_asymmetric": ("$+1/4$", "Asymmetric", "$+1/4$, asym.")}
    checked = 0
    for selection in selections:
        key = (selection["comparison"], selection["observable"], selection["coordinate"])
        source = lookup[key]
        digits, scale = selection["digits"], selection["scale"]
        expected = [f"{float(source[field]) * scale:.{digits}f}" for field in ("estimate", "simultaneous_lower", "simultaneous_upper")]
        if selection["table"] == "tab:mechanism-controls":
            if selection["comparison"] in conditions:
                rho, law, _ = conditions[selection["comparison"]]
                lines = [line for line in controls.splitlines() if line.strip().startswith(rho + " & " + law + " &")]
            else:
                lines = [line for line in controls.splitlines() if "Symmetric minus asymmetric" in line and "&" in line]
            target = float(source["target"])
            expected.insert(0, f"{target if target else 0.:.{selection['target_digits']}f}")
        elif selection["table"] == "tab:mechanism-complement":
            label = conditions[selection["comparison"]][2] if selection["comparison"] in conditions else (
                "Law contrast" if "asymmetric" in selection["comparison"] else "Covariance contrast")
            algorithm = {"SCAFFOLD": "S", "FedAvg": "F", "difference": "D"}[selection["observable"]]
            lines = [line for line in complement.splitlines() if line.strip().startswith(label + " & " + algorithm + " &")]
        else:
            assert selection["table"] == "app:targeted-results prose"
            prose = appendix.split("\\label{app:targeted-results}", 1)[1].split("\\begin{table}", 1)[0]
            lines = [line for line in prose.splitlines() if line.strip().startswith(f"j={selection['coordinate']}:&")]
        assert len(lines) == 1, (selection, "Missing or ambiguous displayed row")
        displayed = re.findall(r"(?<![\d.])-?\d+\.\d+(?![\d.])", lines[0])
        if selection["table"] == "tab:mechanism-complement" and selection["observable"] != "difference":
            assert len(displayed) == 6
            start = (selection["coordinate"] - 1) * 3
            displayed = displayed[start:start+3]
        assert displayed == expected, (key, displayed, expected)
        checked += len(expected)
    assert checked == 113
    return checked


def check_targeted():
    copied, checked_sources = check_copy_manifest("TARGETED_COPY_MANIFEST.csv")
    base = ROOT / "artifacts/canonical_paper_export/targeted_mechanism"
    source = ROOT / "src/targeted_mechanism_snapshot"
    protocol = json.loads((base / "PROTOCOL_FROZEN.json").read_text(encoding="utf-8"))
    mapped = {r["path"]: r for r in copied}
    for rel, expected in protocol["simulation_source_hashes"].items():
        # Frozen simulation code is an archival source snapshot; do not import it.
        for parent in (base, source):
            path = parent / rel
            row = mapped[path.relative_to(ROOT).as_posix()]
            assert row["exact_copy"] == "True" and row["source_sha256"] == expected == file_sha(path), rel
    for row in copied:
        path = ROOT / row["path"]
        if path.is_relative_to(base / "results"):
            assert row["exact_copy"] == "True", "Targeted scientific result changed: " + row["path"]
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=row["path"])
    result = check_targeted_records(base)
    result.update(targeted_copy_files=len(copied), targeted_local_source_hashes_checked=checked_sources,
                  targeted_manuscript_numeric_tokens=check_targeted_transcription(base))
    return result


def check_publication():
    publication_rows, checked_sources = check_copy_manifest("PUBLICATION_COPY_MANIFEST.csv")
    for row in publication_rows:
        path = ROOT / row["path"]
        pilot_manifest = "manuscript/supplementary_results/E4/pilots/PILOT_RUN_MANIFEST.csv"
        if row["path"] == pilot_manifest and row["exact_copy"] == "False":
            variants = csv_rows(ROOT / "docs/manifests/PUBLIC_METADATA_VARIANTS.csv")
            assert any(v["path"] == pilot_manifest and v["reason"].strip() for v in variants)
            original = (ROOT.parent / row["source"]).resolve()
            current_rows = csv_rows(path)
            assert current_rows and "source_path" in current_rows[0]
            if original.is_file():
                old_rows = csv_rows(original)
                assert len(old_rows) == len(current_rows)
                assert [{k: v for k, v in r.items() if k != "source_path"} for r in old_rows] == [
                    {k: v for k, v in r.items() if k != "source_path"} for r in current_rows]
        elif row["path"] == "manuscript/supplementary_results/source_review_snapshot/tools/export_review.py" and row["exact_copy"] == "False":
            variants = csv_rows(ROOT / "docs/manifests/PUBLIC_METADATA_VARIANTS.csv")
            assert any(v["path"] == row["path"] and v["reason"].strip() for v in variants)
            ast.parse(path.read_text(encoding="utf-8"), filename=row["path"])
        elif path.suffix in {".tex", ".bib", ".bbl", ".csv", ".npz", ".py"}:
            assert row["exact_copy"] == "True", "Scientific content changed: " + row["path"]

    panels = ROOT / "manuscript/figures/redrawn"
    source_root = ROOT / "artifacts/canonical_paper_export/figure_redraw"
    provenance = json.loads((panels / "data/provenance.json").read_text(encoding="utf-8"))
    assert set(provenance["panels"]) == PANELS
    cached = {}
    checks = 0
    for panel in sorted(PANELS):
        assert (panels / f"{panel}.pdf").is_file() and (panels / f"{panel}.png").is_file()
        sidecar = csv_rows(panels / "data" / f"{panel}.csv")
        assert len(sidecar) == provenance["panels"][panel]
        for row in sidecar:
            source = (source_root / row["source_file"]).resolve()
            assert source.is_relative_to(source_root.resolve())
            assert file_sha(source) == row["source_sha256"]
            cached.setdefault(source, csv_rows(source))
            original = cached[source][int(row["source_row"])-1]
            for side, column in [("x_original", "x_column"), ("y_original", "y_column"),
                                 ("ci_low_original", "ci_low_column"), ("ci_high_original", "ci_high_column"),
                                 ("target_original", "target_column")]:
                if row[column] and row[side]:
                    if row[column] == "beta0+beta1*x":
                        # Evaluate the already-saved line, never estimate coefficients.
                        saved = float(original["beta0"]) + float(original["beta1"]) * float(row["x_original"])
                    else:
                        saved = float(original[row[column]])
                    assert float(row[side]) == saved, (panel, side)
                    checks += 1
            for side in ("y", "ci_low", "ci_high", "target"):
                if row[f"{side}_original"]:
                    value = float(row[f"{side}_original"])
                    transformed = abs(value) if row["y_transform"] == "abs" else value
                    display = transformed * float(row["y_scale"])
                    assert float(row[f"{side}_display"]) == display, (panel, side, "display transformation")
                    checks += 1
            for coefficient in ("beta0", "beta1"):
                if row[coefficient]:
                    assert float(row[coefficient]) == float(original[coefficient]), (panel, coefficient)
                    checks += 1

    qa = ROOT / "docs/figure_audit"
    numeric = json.loads((qa / "qa_independent/NUMERICAL_AUDIT_SUMMARY.json").read_text(encoding="utf-8"))
    assert numeric["status"] == "PASS" and numeric["failed_checks"] == 0
    assert numeric["no_simulation"] and numeric["no_refit"] and numeric["no_resampling"]
    assert set(numeric["panels"]) == PANELS
    fonts = csv_rows(qa / "qa_fonts/FINAL_FONT_AUDIT.csv")
    assert len(fonts) == 14
    assert {(row["document"], row["panel_id"]) for row in fonts} == {(doc, p) for doc in ("manuscript", "gallery") for p in PANELS}
    for row in fonts:
        assert row["status"] == "PASS"
        assert float(row["minimum_final_TeX_pt"]) >= max(9., float(row["body_TeX_pt"])-2.)-.005
        assert int(row["source_raster_images"]) == 0 and int(row["clipped_text"]) == 0
        assert int(row["source_pages"]) == 1
        assert row["all_fonts_embedded"] == "True"
    subcaptions = []
    for file in (qa / "qa_fonts").glob("*_SUBCAPTION_FONT_AUDIT.csv"):
        subcaptions.extend(csv_rows(file))
    assert len(subcaptions) == 12
    assert all(row["status"] == "PASS" and float(row["subcaption_minimum_TeX_pt"]) >= 9.-.005 for row in subcaptions)
    captions = []
    for file in (qa / "qa_fonts").glob("*_CAPTION_FONT_AUDIT.csv"):
        captions.extend(csv_rows(file))
    assert captions, "Missing final parent-caption audit"
    assert all(row["status"] == "PASS" and float(row["minimum_final_TeX_pt"]) >= 9.-.005 for row in captions)
    latex = json.loads((qa / "qa_latex/LATEX_VALIDATION.json").read_text(encoding="utf-8"))
    assert latex["checks_passed"] and latex["active_panels"] == 7 and latex["subfigure_blocks"] == 6
    # This receipt is the unchanged October 9 build. Its 33-page PDF hash and
    # measured final fonts must never be asserted for the newer manuscript.
    historical = latex["compiled_manuscript"]
    assert historical["pages"] == 33 and re.fullmatch(r"[0-9a-f]{64}", historical["sha256"])
    gallery = latex["compiled_gallery"]
    assert gallery["pages"] == 4 and re.fullmatch(r"[0-9a-f]{64}", gallery["sha256"])
    portable = json.loads((qa / "portable_numeric/NUMERICAL_AUDIT_SUMMARY.json").read_text(encoding="utf-8"))
    assert portable["status"] == "PASS" and portable["failed_checks"] == 0
    assert portable["checks"] == 2646 and portable["input_csvs_checked"] == 10
    assert portable["broader_original_and_proof_preservation"]["status"] == "ARCHIVED_RECEIPT_NOT_REEXECUTED"
    replay = json.loads((qa / "RELEASE_REPLAY.json").read_text(encoding="utf-8"))
    assert replay["status"] in {"PASS", "PASS_RENDER_EQUIVALENT"} and replay["panels"] == 7
    assert replay["canonical_provenance_identical"]
    for row in replay["comparisons"]:
        assert all(row[key] for key in ("sidecar_byte_identical", "png_byte_identical", "raster_pixels_identical",
                   "pdf_content_operators_identical", "pdf_font_names_equal_ignoring_subset_prefix",
                   "pdf_media_box_identical", "pdf_raster_pixels_identical_216dpi"))
    return dict(historical_redrawn_panels=7, sidecar_value_checks=checks, original_independent_numeric_checks=numeric["checks"],
                portable_numeric_checks=portable["checks"], replay_status=replay["status"],
                replay_pdf_byte_mismatches=replay["pdf_byte_mismatches"],
                historical_final_font_inclusions=14, historical_minimum_final_font_TeX_pt=min(float(r["minimum_final_TeX_pt"]) for r in fonts),
                historical_subcaption_inclusions=len(subcaptions), historical_parent_caption_checks=len(captions),
                historical_build_receipt_scope="2026-10-09; not a build or final-font validation of the current manuscript",
                publication_local_source_hashes_checked=checked_sources)


def check_closure():
    excluded = {"docs/manifests/RELEASE_FILE_MANIFEST.csv", "docs/VALIDATION_RECEIPT.md"}
    table = csv_rows(ROOT / "docs/manifests/RELEASE_FILE_MANIFEST.csv")
    listed = {row["path"] for row in table}
    actual = {path.relative_to(ROOT).as_posix() for path in public_files(ROOT)
              if path.relative_to(ROOT).as_posix() not in excluded}
    assert len(table) == len(listed) and listed == actual, "Release manifest closure mismatch"
    for row in table:
        path = ROOT / row["path"]
        assert path.stat().st_size == int(row["bytes"]) and file_sha(path) == row["sha256"], row["path"]
        if path.suffix in {".py", ".md", ".csv", ".json", ".yaml", ".toml", ".txt", ".tex", ".diff", ".cff", ".ps1", ".sh", ".bib"}:
            assert not LOCAL_PATH.search(path.read_text(encoding="utf-8")), row["path"]
    source_manifest = csv_rows(ROOT / "docs/SOURCE_MANIFEST.csv")
    assert {r["path"] for r in source_manifest} == actual - {"docs/SOURCE_MANIFEST.csv"}
    assert len(source_manifest) == len({r["path"] for r in source_manifest})
    for row in source_manifest:
        path = public_path(row["path"])
        assert int(row["bytes"]) == path.stat().st_size and row["sha256"] == file_sha(path), row["path"]
    assert (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()[0] == "* -text"
    git_audit = json.loads((ROOT / "docs/manifests/GIT_BYTE_AUDIT.json").read_text(encoding="utf-8"))
    assert git_audit["status"] == "PASS" and git_audit["representative_filter_checks"] == 9
    assert all(row["git_blob_raw"] == row["git_blob_filtered"] for row in git_audit["samples"])
    return len(table)


def check_publication_readiness():
    """Check current exhibit numbering, policies, dependencies and frozen bytes."""
    import importlib.util
    import tomllib
    import yaml
    from table_regeneration.catalog import TABLES, FIGURES, PDF_SHA256
    frozen = csv_rows(ROOT / "docs/manifests/FROZEN_BASELINE_MANIFEST.csv")
    assert frozen and len(frozen) == len({r["path"] for r in frozen})
    for row in frozen:
        path = public_path(row["path"])
        assert file_sha(path) == row["sha256"] and path.stat().st_size == int(row["bytes"]), row["path"]
    assert file_sha(ROOT / "manuscript/main.pdf") == PDF_SHA256
    graph = check_tex_assets("manuscript/main.tex")
    active_text = "\n".join(re.sub(r"(?<!\\)%[^\n]*", "", public_path(p).read_text(encoding="utf-8"))
                            for p in graph["paths"] if p.endswith(".tex"))
    labels = set(re.findall(r"\\label\{((?:tab|fig):[^}]+)\}", active_text))
    active_tables = [t for t in TABLES if t["active"]]
    assert [t["number"] for t in active_tables] == list(range(1, 23))
    # The consolidated attribution table retains two historical reference aliases.
    aliases = {"tab:E-control", "tab:E-fa"}
    assert {t["label"] for t in active_tables} | aliases == {v for v in labels if v.startswith("tab:")}
    table_blocks = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", active_text, flags=re.S)
    assert len(table_blocks) == 22
    for table in active_tables:
        block = [b for b in table_blocks if "\\label{" + table["label"] + "}" in b]
        assert len(block) == 1
        if table["number"] == 11:
            assert all("\\label{" + name + "}" in block[0] for name in aliases)
    assert {f["label"] for f in FIGURES} | {"fig:E-h4diag"} == {v for v in labels if v.startswith("fig:")}
    figure_blocks = re.findall(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", active_text, flags=re.S)
    assert len(figure_blocks) == 5
    final_figure = [b for b in figure_blocks if "\\label{fig:E-control-h4}" in b]
    assert len(final_figure) == 1 and "\\label{fig:E-h4diag}" in final_figure[0]
    assert len(FIGURES) == 5 and sum(len(f["panels"]) for f in FIGURES) == 9
    for item in TABLES:
        text = public_path(item["manuscript_source"]).read_text(encoding="utf-8")
        assert "\\label{" + item["label"] + "}" in text
    required = ("README.md", "AGENTS.md", "docs/MANUSCRIPT_REPRODUCIBILITY_MATRIX.md",
                "docs/TABLE_REGENERATION.md", "docs/DATA_AND_ARCHIVES.md",
                "docs/FIGURE_PROVENANCE.md", "docs/METHOD_TO_CODE_MAP.md",
                "docs/RESULT_PROVENANCE.md", "docs/REPRODUCIBILITY_SCOPE.md",
                "docs/PUBLICATION_RELEASE_MANIFEST.md",
                "scripts/regenerate_paper_figures.py", "scripts/regenerate_paper_tables.py",
                "scripts/run_representative_example.py",
                "configs/environments/publication_20261018.requirements.lock")
    for name in required:
        assert public_path(name).stat().st_size > 0
    citation = yaml.safe_load(public_path("CITATION.cff").read_text(encoding="utf-8"))
    url = "https://github.com/Duck-YP/stationary-bias-study"
    assert citation["cff-version"] == "1.2.0" and citation["repository-code"].rstrip("/") == url
    assert [a["family-names"] for a in citation["authors"]] == ["Tang", "Peng"]
    assert citation["preferred-citation"]["title"] == citation["title"]
    assert "2608.26765" in json.dumps(citation)
    assert not any(k in citation for k in ("license", "version", "doi"))
    availability = public_path("manuscript/sections/10_code_availability.tex").read_text(encoding="utf-8")
    assert url in availability
    project = tomllib.loads(public_path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["urls"]["Repository"] == url and "license" not in project
    dependencies = ("numpy", "scipy", "numba", "pandas", "yaml", "matplotlib",
                    "pypdf", "pdfplumber", "pypdfium2", "PIL", "pytest")
    assert all(importlib.util.find_spec(name) is not None for name in dependencies), "Install declared dependencies"
    replay = json.loads(public_path("docs/manifests/PUBLICATION_FIGURE_REPLAY.json").read_text(encoding="utf-8"))
    assert replay["status"] in {"PASS", "PASS_RENDER_EQUIVALENT"} and replay["panels"] == 9
    assert replay["canonical_provenance_identical"] and len(replay["comparisons"]) == 9
    for row in replay["comparisons"]:
        assert all(row[k] for k in ("sidecar_byte_identical", "png_byte_identical", "raster_pixels_identical",
                   "pdf_content_operators_identical", "pdf_font_names_equal_ignoring_subset_prefix",
                   "pdf_media_box_identical", "pdf_raster_pixels_identical_216dpi"))
    tables_base = ROOT / "artifacts/canonical_paper_export/tables"
    table_receipt = json.loads((tables_base / "VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    coverage = json.loads((tables_base / "coverage.json").read_text(encoding="utf-8"))
    assert table_receipt["status"] == "PASS_WITH_DISCLOSED_GAPS"
    assert table_receipt["active_numbered_tables"] == 22 and table_receipt["source_table_environments"] == 23
    assert table_receipt["data_exports"] == 21 and table_receipt["exact_decimal_tables"] == 14
    assert table_receipt["exact_decimal_cells"] == 453
    assert all(not table_receipt["scientific_recomputation"][k] for k in ("simulation", "refit", "resampling"))
    assert [t["label"] for t in coverage["tables"]] == [t["label"] for t in TABLES]
    assert {t["number"] for t in coverage["tables"] if t["status"] == "partial"} == {8, 18, 19, 20}
    assert coverage["manuscript_pdf_sha256"] == PDF_SHA256 and coverage["figures"] == FIGURES
    for name, item in table_receipt["inputs"].items():
        path = public_path(name)
        assert file_sha(path) == item["sha256"] and path.stat().st_size == item["bytes"], name
    for name, digest in table_receipt["source_code"].items():
        assert file_sha(public_path(name)) == digest, name
    for name, item in table_receipt["outputs"].items():
        path = public_path("artifacts/canonical_paper_export/tables/" + name)
        assert file_sha(path) == item["sha256"] and path.stat().st_size == item["bytes"], name
    for number, check in table_receipt["display_validation"].items():
        assert check["status"] != "FAIL", number
    assert table_receipt["display_validation"]["18"]["status"] == "DISCLOSED_PARTIAL"
    assert table_receipt["author_attention"], "Do not suppress known table limitations"
    return dict(publication_frozen_files=len(frozen), active_numbered_tables=22,
                inactive_source_tables=1, numbered_figures=5, publication_figure_replay=replay["status"],
                table_data_exports=21, exact_decimal_tables=14, exact_decimal_cells=453,
                partially_reconstructed_tables=[8, 18, 19, 20],
                declared_dependencies_available=True, repository_url_matches_manuscript=True)


def validate() -> dict:
    manifest = ROOT / "docs/manifests/EXACT_COPY_MANIFEST.csv"
    with manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError("Empty exact-copy manifest")
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        assert path.is_relative_to(ROOT), row["path"]
        assert path.is_file(), row["path"]
        assert path.stat().st_size == int(row["bytes"]), row["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], row["path"]
        assert row["exact_copy"] == "True", row["path"]
        if path.suffix in {".py", ".md", ".csv", ".json", ".yaml", ".toml", ".txt"}:
            assert not LOCAL_PATH.search(path.read_text(encoding="utf-8")), row["path"]
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=row["path"])
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        if path.suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                assert next(csv.reader(handle), None), row["path"]
        if path.suffix == ".npz":
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None, row["path"]
                assert archive.namelist() and all(name.endswith(".npy") for name in archive.namelist())

    data = ROOT / "artifacts/canonical_paper_export/supplementary"
    protocol = json.loads((data / "PROTOCOL_FROZEN.json").read_text(encoding="utf-8"))
    assert len(protocol["cells"]) == 69
    assert protocol["production_seeds"] == list(range(20001, 20013))
    assert {2, 4, 8}.issubset({cell["H"] for cell in protocol["cells"] if cell["family"] == "E1"})
    with (data / "EXPERIMENT_REGISTRY.csv").open(encoding="utf-8", newline="") as handle:
        registry = list(csv.DictReader(handle))
    production = [row for row in registry if row["phase"] == "production"]
    assert len(production) == 69
    assert {row["cell_id"] for row in production} == {cell["id"] for cell in protocol["cells"]}
    with (data / "per_run_estimates.csv").open(encoding="utf-8", newline="") as handle:
        runs = list(csv.DictReader(handle))
    keys = {(row["cell_id"], int(row["seed"]), row["algorithm"]) for row in runs}
    expected = {(cell["id"], seed, algorithm) for cell in protocol["cells"]
                for seed in protocol["production_seeds"] for algorithm in ("scaffold", "fedavg")}
    assert len(runs) == len(keys) == 1656
    assert keys == expected, "Incomplete per-run evidence or duplicate rows"
    python_files = list((ROOT / "src").rglob("*.py"))
    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(ROOT)))
    forbidden = {"raw", "checkpoints"}
    for path in public_files(ROOT):
        relative = path.relative_to(ROOT)
        assert not forbidden.intersection(relative.parts), str(relative)
        if path.is_file():
            assert path.suffix not in {".zip", ".z01", ".001"}, str(relative)
            assert path.stat().st_size < 100_000_000, str(relative)
    publication = check_publication()
    current = check_current_manuscript()
    targeted = check_targeted()
    readiness = check_publication_readiness()
    manifest_files = check_closure()
    return dict(status="PASS", exact_copy_files=len(rows), parsed_source_files=len(python_files),
                production_cells=len(production), registry_rows=len(registry),
                production_algorithm_runs=len(runs),
                production_seeds=len(protocol["production_seeds"]),
                complete_manifest_files=manifest_files, **publication, **current, **targeted, **readiness,
                scientific_recomputation="NONE", checks="hashes, active TeX assets, saved numeric transcription, record completeness, syntax, local-path hygiene")


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), indent=2))
    except Exception as error:
        print(f"Release validation failed: {error}", file=sys.stderr)
        raise
