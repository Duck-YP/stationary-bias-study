"""Integrate finalized manuscript/rendering records; no experimental computation."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
from public_metadata import portable_metadata

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
LOCAL = re.compile(r"[A-Z]:[\\/]|/(?:Users|home)/[A-Za-z0-9._-]+/")
TEXT = {".py", ".md", ".json", ".csv", ".tex", ".diff", ".ps1", ".yaml", ".toml", ".txt", ".lock", ".sh", ".cff"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_document(data: bytes, name: str) -> bytes:
    """Adapt only public paths; the original document hash remains in the manifest."""
    text = data.decode("utf-8")
    audit = "../docs/figure_audit/layout_20261018/"
    replacements = {
        "../figure_layout_revision_20261018/baseline/manuscript/main.pdf": audit + "BASELINE_main.pdf",
        "../figure_layout_revision_20261018/baseline/SUPPLIED_OLDER_main.pdf": audit + "SUPPLIED_OLDER_main.pdf",
        "../figure_layout_revision_20261018/comparisons/BEFORE_AFTER.pdf": audit + "BEFORE_AFTER.pdf",
        "../figure_layout_revision_20261018/final/": audit,
        "../figure_layout_revision_20261018/qa/": audit,
        "../figure_layout_revision_20261018/": audit,
        "figure_layout_revision_20261018/final/manuscript/main.pdf": "manuscript/main.pdf",
        "figure_layout_revision_20261018/qa/": "docs/figure_audit/layout_20261018/",
        "figure_redraws/20261009/pipeline": "artifacts/canonical_paper_export/figure_redraw",
        "**本次實際使用**": "**公開匯出對應位置**",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    context = (
        "> Public export context: paths below are adapted from the local revision record. "
        "Use ../docs/FIGURE_REPRODUCTION.md for the portable commands. "
        "The release-unchanged statement and source guard describe the preceding layout task, "
        "before this separately authorized synchronization. Full-page PNG render sets and "
        "workspace-baseline audit rerun dependencies remain in the local handoff; the public "
        "export includes the compiled baseline, current PDF, vector comparison and saved QA receipts.\n\n"
    )
    return (context + text).encode("utf-8")


def main():
    copied, variants, omitted = [], [], []

    def save(data, target, origin, *, public_data=None, reason=""):
        target = target.resolve()
        assert target.is_relative_to(ROOT)
        final = data if public_data is None else public_data
        if target.suffix in TEXT and LOCAL.search(final.decode("utf-8")):
            final = portable_metadata(final)
            public_data = final
            reason = "Replace machine-local path strings only; preserve all scientific values and historical receipt scope"
            assert not LOCAL.search(final.decode("utf-8"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(final)
        record = dict(path=target.relative_to(ROOT).as_posix(), source=origin,
                      bytes=len(final), source_sha256=digest(data), sha256=digest(final),
                      exact_copy=data == final)
        copied.append(record)
        if public_data is not None:
            variants.append({**record, "reason": reason})

    def copy(source, target, *, public_data=None, reason=""):
        save(source.read_bytes(), target, source.relative_to(WORKSPACE).as_posix(),
             public_data=public_data, reason=reason)

    for source in sorted((WORKSPACE / "manuscript").rglob("*")):
        if not source.is_file() or {"__pycache__", "build", ".pytest_cache"}.intersection(source.parts):
            continue
        relative = source.relative_to(WORKSPACE / "manuscript")
        if source.suffix in {".zip", ".aux", ".blg", ".log", ".out", ".toc", ".pyc"}:
            omitted.append(dict(source=source.relative_to(WORKSPACE).as_posix(), bytes=source.stat().st_size,
                                sha256=digest(source.read_bytes()), reason="Archive/build output not part of public tree"))
            continue
        if relative.as_posix() == "supplementary_results/RUN_COMMANDS.md":
            omitted.append(dict(source=source.relative_to(WORKSPACE).as_posix(), bytes=source.stat().st_size,
                                sha256=digest(source.read_bytes()), reason="Machine-local study commands; public portable workflows documented separately"))
            continue
        if relative.as_posix() == "README.md":
            note = ("\n## Public export note\n\nThis export follows the 2026-10-18 final figure/layout revision of V2.\n"
                    "The included 40-page main.pdf is the clean compiled current source; main.bbl is its generated bibliography.\n"
                    "This public copy omits `SOURCE_REVIEW.zip` and machine-local `RUN_COMMANDS.md`;\n"
                    "source-review snapshots are provided unpacked under\n"
                    "`supplementary_results/source_review_snapshot/`. Metadata-only path variants\n"
                    "and omissions are listed in `../docs/manifests/`. Scientific TeX, numerical\n"
                    "results and estimators are unchanged; the E4 pilot manifest has portable path strings.\n"
                    "Targeted evidence is unpacked under `../artifacts/canonical_paper_export/targeted_mechanism/`\n"
                    "and its source snapshot under `../src/targeted_mechanism_snapshot/`. These snapshots\n"
                    "preserve provenance and may require the original study layout for execution.\n"
                    "Use `../docs/FIGURE_REPRODUCTION.md` for supported public commands.\n")
            copy(source, ROOT / "manuscript" / relative,
                 public_data=source.read_bytes()+note.encode(), reason="Document public archive/privacy policy")
        elif relative.as_posix() in {"FIGURE_PROVENANCE.md", "FIGURE_LAYOUT_CHANGELOG.md"}:
            copy(source, ROOT / "manuscript" / relative,
                 public_data=current_document(source.read_bytes(), relative.name),
                 reason="Map local figure input/audit paths to the public export and clarify historical receipt scope; preserve numerical content")
        else:
            copy(source, ROOT / "manuscript" / relative)

    archive = WORKSPACE / "manuscript/supplementary_results/SOURCE_REVIEW.zip"
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        for entry in handle.infolist():
            if entry.is_dir():
                continue
            relative = Path(entry.filename).relative_to("SOURCE_REVIEW")
            assert ".." not in relative.parts and not relative.is_absolute()
            data = handle.read(entry)
            origin = archive.relative_to(WORKSPACE).as_posix()+"!"+entry.filename
            destination = ROOT / "manuscript/supplementary_results/source_review_snapshot" / relative
            if relative.as_posix() == "ENVIRONMENT_ORIGINAL.txt":
                record = json.loads(data.decode("utf-8"))
                record["executable"] = "python"
                save(data, destination, origin, public_data=(json.dumps(record, indent=2)+"\n").encode(),
                     reason="Replace machine-local interpreter path; preserve versions and numerical hardware metadata")
            else:
                save(data, destination, origin)

    pipeline = WORKSPACE / "figure_redraws/20261009/pipeline"
    for name in ("figure_style.py", "redraw_figures.py", "audit_final_fonts.py"):
        source = WORKSPACE / "manuscript/tools/figure_layout" / name if name != "audit_final_fonts.py" else pipeline / name
        copy(source, ROOT / "scripts/figure_redraw" / name)
    copy(WORKSPACE / "figure_redraws/20261009/qa_independent/verify_numerical_preservation.py",
         ROOT / "scripts/figure_redraw/verify_numerical_preservation.py")
    copy(WORKSPACE / "figure_redraws/20261009/qa_independent/original_protection_manifest.json",
         ROOT / "scripts/figure_redraw/original_protection_manifest.json")
    for source in sorted((pipeline / "inputs").rglob("*")):
        if source.is_file():
            copy(source, ROOT / "artifacts/canonical_paper_export/figure_redraw/inputs" / source.relative_to(pipeline / "inputs"))

    qa = WORKSPACE / "figure_redraws/20261009"
    groups = {
        "qa_independent": ["NUMERICAL_AUDIT_SUMMARY.json", "NUMERICAL_PRESERVATION_INDEPENDENT.csv",
                           "SCIENTIFIC_DATA_MAPPING_AUDIT.md", "original_protection_manifest.json"],
        "qa_latex": ["LATEX_BUILD_REPORT.md", "LATEX_REVISION.diff", "LATEX_VALIDATION.json",
                     "PROTECTED_SOURCE_CHECK.csv", "SUPPLEMENTARY_COPY_CHECK.csv", "TYPOGRAPHY_MEASURED.json"],
        "qa_fonts": sorted(source.name for source in (qa / "qa_fonts").glob("*.csv")),
    }
    for group, names in groups.items():
        for name in names:
            source = qa / group / name
            destination = ROOT / "docs/figure_audit" / group / name
            if name == "LATEX_VALIDATION.json":
                record = json.loads(source.read_text(encoding="utf-8"))
                record["compiled_manuscript"]["path"] = "manuscript/main.pdf"
                record["compiled_gallery"]["path"] = "manuscript/figures_gallery.pdf"
                copy(source, destination, public_data=(json.dumps(record, indent=2)+"\n").encode(),
                     reason="Replace machine-local PDF paths with public relative paths only")
            elif name == "LATEX_BUILD_REPORT.md":
                note = ("# Public receipt context\n\nThe following is a recorded local compilation receipt.\n"
                        "Full baseline/build logs remain in the local handoff, not this compact\n"
                        "public tree. Baseline-specific recheck commands require that original\n"
                        "handoff; supported public commands are in `docs/FIGURE_REPRODUCTION.md`.\n\n")
                copy(source, destination, public_data=note.encode()+source.read_bytes(),
                     reason="Clarify archival log and baseline recheck scope")
            else:
                copy(source, destination)
    for source in sorted((qa / "qa_visual").glob("*.png")):
        copy(source, ROOT / "docs/figure_audit/previews" / source.name)

    revision = WORKSPACE / "figure_layout_revision_20261018"
    current_audit = ROOT / "docs/figure_audit/layout_20261018"
    for name in ("BASELINE_PDF_FONT_AUDIT.json", "FINAL_PDF_FONT_AUDIT.json",
                 "NUMERIC_INVARIANCE.json", "ARTIST_GEOMETRY_CHECKS.json",
                 "VECTOR_DRAWING_BOUNDS.json", "SOURCE_HASH_GUARD.json",
                 "INDEPENDENT_QA_REVIEW.md", "ALL_NINE_PANELS_GRAYSCALE.png"):
        copy(revision / "qa" / name, current_audit / name)
    for origin, name in {
        "baseline/logs/BUILD_REPORT.json": "BASELINE_BUILD_REPORT.json",
        "final/logs/BUILD_REPORT.json": "BUILD_REPORT.json",
        "baseline/manuscript/main.pdf": "BASELINE_main.pdf",
        "baseline/SUPPLIED_OLDER_main.pdf": "SUPPLIED_OLDER_main.pdf",
        "comparisons/BEFORE_AFTER.pdf": "BEFORE_AFTER.pdf",
        "comparisons/INDEX.json": "COMPARISON_SOURCE_INDEX.json",
        "comparisons/QA_SUMMARY.json": "COMPARISON_QA.json",
        "FIGURE_LAYOUT_REVISION.patch": "FIGURE_LAYOUT_REVISION.patch",
        "CHANGE_MANIFEST.json": "CHANGE_MANIFEST.json",
    }.items():
        copy(revision / origin, current_audit / name)

    public_replay = WORKSPACE / "release_sync_20261018_figure_layout"
    for name in ("FIGURE_REPLAY.json", "RECOMPILE_COMPARE.json"):
        copy(public_replay / name, current_audit / name)
    copy(public_replay / "build/logs/BUILD_REPORT.json", current_audit / "PUBLIC_BUILD_REPORT.json")

    base = ROOT / "docs/manifests"
    for name, rows, fields in [
        ("PUBLICATION_COPY_MANIFEST.csv", copied, ["path", "source", "bytes", "source_sha256", "sha256", "exact_copy"]),
        ("PUBLIC_METADATA_VARIANTS.csv", variants, ["path", "source", "bytes", "source_sha256", "sha256", "exact_copy", "reason"]),
        ("PUBLICATION_OMISSIONS.csv", omitted, ["source", "bytes", "sha256", "reason"]),
    ]:
        with (base / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps(dict(copied=len(copied), bytes=sum(row["bytes"] for row in copied),
                          metadata_variants=len(variants), omissions=len(omitted), scientific_changes="NONE"), indent=2))


if __name__ == "__main__":
    main()
