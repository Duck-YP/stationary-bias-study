"""Rebuild paper table data from saved results, without simulation or inference.

Numerical table builders never read the manuscript. The independent final step
compares regenerated decimal cells to displayed TeX; extraction is validation
only and cannot supply a missing result. See docs/TABLE_REGENERATION.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from table_regeneration.catalog import TABLES, FIGURES, PDF_SHA256
from table_regeneration.historical_tables import build_historical_tables
from table_regeneration.recent_tables import build_recent_tables
from table_regeneration.config_tables import build_config_tables

DECIMALS = re.compile(r"(?<![\d.])-?\d+\.\d+(?![\d.])")
DECIMAL_TABLES = {2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 21, 22}
# Validation-only allowlist of the independently audited display gaps. These
# values are NEVER used to fill regenerated table cells or compute uncertainty.
KNOWN_TABLE18_GENERATED_DIFFERENCE = {"-0.1080237": 1}
KNOWN_TABLE18_DISPLAY_DIFFERENCE = {
    "-0.1080240": 1, "0.00331567": 1, "0.00115744": 1,
    "0.00334677": 1, "0.00110953": 1,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SavedInputs:
    """Read-only, root-confined loaders and hashes of every actual input."""
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.records = {}

    def path(self, relative, role="saved_input"):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError(f"Missing or escaping input: {relative}")
        key = path.relative_to(self.root).as_posix()
        self.records[key] = {"sha256": sha(path), "bytes": path.stat().st_size, "role": role}
        return path

    def csv(self, relative):
        with self.path(relative).open(encoding="utf-8-sig", newline="") as handle:
            return [dict(row, _source_row=i + 1) for i, row in enumerate(csv.DictReader(handle))]

    def json(self, relative):
        return json.loads(self.path(relative).read_text(encoding="utf-8-sig"))

    def yaml(self, relative):
        import yaml
        return yaml.safe_load(self.path(relative).read_text(encoding="utf-8-sig"))

    def text(self, relative):
        return self.path(relative).read_text(encoding="utf-8-sig")


def build_tables(inputs):
    tables = {}
    for built in (build_historical_tables(inputs.csv, inputs.json, inputs.text),
                  build_recent_tables(inputs.csv, inputs.json),
                  build_config_tables(inputs.csv, inputs.json, inputs.yaml)):
        if set(tables) & set(built):
            raise ValueError("Duplicate table builders")
        tables.update(built)
    if set(tables) != set(range(2, 23)):
        raise ValueError(f"Incomplete active computational inventory: {sorted(tables)}")
    for number, table in tables.items():
        if not table["rows"] or any(len(row) != len(table["headers"]) for row in table["rows"]):
            raise ValueError(f"Malformed table {number}")
        table["rows"] = [[str(cell) for cell in row] for row in table["rows"]]
    return tables


def table_body(text, label):
    """Read displayed cells only after data generation, never for table values."""
    blocks = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", text, flags=re.S)
    selected = [b for b in blocks if re.search(r"\\label\s*\{" + re.escape(label) + r"\}", b)]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one manuscript table: {label}")
    bodies = re.findall(r"\\begin\{tabular\*?\}(.*?)\\end\{tabular\*?\}", selected[0], flags=re.S)
    if not bodies:
        raise ValueError(f"No tabular body for {label}")
    return "\n".join(bodies)


def validate_display(metadata, table, inputs):
    number = metadata["number"]
    if number not in DECIMAL_TABLES and number != 18:
        return {"status": "SOURCE_BACKED_METADATA" if number != 10 else "EXACT_SYMBOLIC_CERTIFICATE",
                "scope": "Normalized source records; no claim of literal manuscript prose/LaTeX equality."}
    source = inputs.path(metadata["manuscript_source"], role="display_validation_only")
    body = table_body(source.read_text(encoding="utf-8-sig"), metadata["label"])
    # Decimal strings retain their number of places, including trailing zeros.
    # Counts retain repeated values. Association is supplied by fixed selectors
    # in the builders; this check alone does not prove row association.
    actual = Counter(DECIMALS.findall("\n".join(" ".join(row) for row in table["rows"])))
    displayed = Counter(DECIMALS.findall(body))
    absent = actual - displayed
    uncovered = displayed - actual
    known_gap = (number == 18 and dict(absent) == KNOWN_TABLE18_GENERATED_DIFFERENCE
                 and dict(uncovered) == KNOWN_TABLE18_DISPLAY_DIFFERENCE)
    return {"status": "PASS" if actual == displayed else ("DISCLOSED_PARTIAL" if known_gap else "FAIL"),
            "scope": "Exact multiset of decimal display strings in table body; row selectors are recorded in source modules.",
            "regenerated_decimal_cells": sum(actual.values()),
            "displayed_decimal_cells": sum(displayed.values()),
            "regenerated_not_displayed": dict(sorted(absent.items())),
            "displayed_not_regenerated": dict(sorted(uncovered.items()))}


def tex_escape(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(c, c) for c in str(value))


def write_table(output, metadata, table):
    stem = f"table_{metadata['number']:02d}"
    with (output / (stem + ".csv")).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(table["headers"])
        writer.writerows(table["rows"])
    def markdown_row(row):
        return "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in row) + " |"
    lines = [f"# Table {metadata['number']}: {metadata['title']}", "",
             f"Status: **{table['status']}**. Section {metadata['section']}, page {metadata['page']}.", "",
             table["notes"], "", markdown_row(table["headers"]),
             markdown_row(["---"] * len(table["headers"])), *map(markdown_row, table["rows"]), "", "Sources:", ""]
    lines.extend("- `" + path + "`" for path in table["sources"])
    (output / (stem + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Deliberately a plain data tabular, not a replacement layout for the paper.
    # Long protocol text can be reflowed by downstream authors.
    lines = ["% Saved-input data export; no simulation, refit or resampling.",
             "% " + metadata["label"] + ": " + table["status"],
             r"\begin{tabular}{" + "l" * len(table["headers"]) + "}",
             " & ".join(map(tex_escape, table["headers"])) + r" \\", r"\hline"]
    lines.extend(" & ".join(map(tex_escape, row)) + r" \\" for row in table["rows"])
    lines.append(r"\end{tabular}")
    (output / (stem + ".tex")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def regenerate(output, root=ROOT):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError("--output must be outside the repository; saved evidence is read-only")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("--output must be new or empty")
    inputs = SavedInputs(root)
    tables = build_tables(inputs)
    coverage, validation = [], {}
    for metadata in TABLES:
        row = dict(metadata)
        number = row["number"]
        if number in tables:
            table = tables[number]
            row.update({k: table[k] for k in ("status", "notes", "sources")})
            row["rows"] = len(table["rows"])
            row["outputs"] = [f"table_{number:02d}.{ext}" for ext in ("csv", "md", "tex")]
            row["source_rows"] = table.get("source_rows", [])
            row["uncovered_fields"] = table.get("uncovered_fields", [])
            validation[str(number)] = validate_display(metadata, table, inputs)
        elif number == 1:
            row.update(status="not_computational", sources=[metadata["manuscript_source"], "manuscript/references.bib"],
                       notes="Analytical literature comparison, including asymptotic orders. Requires theorem/source review, not numerical regeneration.", outputs=[])
        else:
            row.update(status="archive", sources=[metadata["manuscript_source"]],
                       notes="Source table is in an appendix not input by main.tex. It has no number/page in the active 40-page manuscript; not regenerated as an active result.", outputs=[])
        coverage.append(row)
    failures = [number for number, check in validation.items() if check["status"] == "FAIL"]
    inputs.path("manuscript/main.pdf", role="numbering_reference")
    pdf_hash = inputs.records["manuscript/main.pdf"]["sha256"]
    if pdf_hash != PDF_SHA256:
        raise ValueError("Numbering catalog refers to a different PDF; review exhibit metadata before proceeding")
    output.mkdir(parents=True, exist_ok=True)
    for metadata in TABLES:
        if metadata["number"] in tables:
            write_table(output, metadata, tables[metadata["number"]])
    dump = lambda path, value: path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    dump(output / "coverage.json", {"tables": coverage, "figures": FIGURES, "manuscript_pdf_sha256": PDF_SHA256})
    with (output / "coverage.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["number", "label", "active", "section", "page", "status", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(coverage)
    counts = Counter(row["status"] for row in coverage)
    receipt = {"schema_version": 1,
               "status": "FAIL" if failures else "PASS_WITH_DISCLOSED_GAPS",
               "scientific_recomputation": {"simulation": False, "refit": False, "resampling": False,
                                             "operations": "saved-row selection, equality checks, rational marginalization/ratios, scaling and display formatting"},
               "active_numbered_tables": 22, "source_table_environments": 23,
               "data_exports": len(tables), "coverage_counts": dict(sorted(counts.items())),
               "exact_decimal_tables": len(DECIMAL_TABLES),
               "exact_decimal_cells": sum(validation[str(n)]["regenerated_decimal_cells"] for n in DECIMAL_TABLES),
               "display_validation": validation,
               "inputs": dict(sorted(inputs.records.items())),
               "source_code": {p.relative_to(root).as_posix(): sha(p)
                               for p in [root / "scripts/regenerate_paper_tables.py", *sorted((root / "scripts/table_regeneration").glob("*.py"))]},
               "author_attention": [tables[18]["notes"]],
               "outputs": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                           for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "README.md").write_text(
        "# Saved-input manuscript tables\n\n"
        "No simulations, fitted regressions or resampling were run. Tables are data exports, not replacement page layouts.\n\n"
        f"The source contains 23 table environments: 22 active numbered tables and one inactive archive table. {len(tables)} active tables have source-backed CSV/Markdown/TeX exports.\n\n"
        f"Fourteen decimal result tables contain {receipt['exact_decimal_cells']} regenerated decimal cells; their exact display comparisons are in VALIDATION_RECEIPT.json. Table 10 retains exact symbolic certificate values.\n\n"
        "Protocol inventories are normalized records; see coverage.json for complete versus partial coverage. Table 1 is analytical literature; the inactive appendix table is not an active numerical result.\n\n"
        "Table 18 remains partial: four original per-run uncertainty thresholds are unavailable and one stored coefficient rounds differently at the displayed precision. No missing uncertainty or display value is filled from the manuscript.\n",
        encoding="utf-8")
    receipt["outputs"] = {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                          for p in sorted(output.iterdir()) if p.is_file() and p.name != "VALIDATION_RECEIPT.json"}
    dump(output / "VALIDATION_RECEIPT.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New or empty directory outside this repository")
    args = parser.parse_args()
    try:
        result = regenerate(args.output)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f"Table regeneration stopped: {error}\n")
    print(json.dumps({k: result[k] for k in ("status", "active_numbered_tables", "data_exports", "coverage_counts", "exact_decimal_tables", "exact_decimal_cells")}, indent=2))
    if result["status"] == "FAIL":
        parser.exit(1, "Unexpected table display mismatch; inspect VALIDATION_RECEIPT.json.\n")


if __name__ == "__main__":
    main()
