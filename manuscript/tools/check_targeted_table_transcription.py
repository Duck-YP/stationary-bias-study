#!/usr/bin/env python3
"""Check the added paper tables against the supplied frozen CSV (no refitting)."""
from __future__ import annotations
import argparse, csv, io, json, zipfile
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    manuscript = Path(__file__).resolve().parents[1]
    parser.add_argument("--manuscript", type=Path, default=manuscript)
    parser.add_argument("--review-zip", type=Path,
        default=manuscript.parent / "repository_materials/targeted_mechanism/TARGETED_MECHANISM_REVIEW.zip")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not args.review_zip.is_file():
        parser.error(f"Review archive not found: {args.review_zip}")
    with zipfile.ZipFile(args.review_zip) as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read("results/primary_family_36.csv").decode("utf-8-sig"))))
    lookup = {(r["comparison"], r["observable"], int(r["coordinate"])): r for r in rows}
    selections = json.loads((args.manuscript / "revision_audit/targeted_mechanism_20261015/new_numeric_selections.json").read_text())
    text = "\n".join((args.manuscript / p).read_text() for p in
        ["sections/07_numerical_study.tex", "appendix/C_numerical_details.tex"])
    details = []
    def formatted(value: str, digits: int, scale: float) -> str:
        x = float(value) * scale
        if abs(x) < 0.5 * 10 ** (-digits):
            x = 0.0
        return f"{x:.{digits}f}"
    for selection in selections:
        key = (selection["comparison"], selection["observable"], selection["coordinate"])
        row = lookup[key]
        for field in ["estimate", "simultaneous_lower", "simultaneous_upper"]:
            expected = formatted(row[field], selection["digits"], selection["scale"])
            details.append({"key": key, "field": field, "display": expected, "pass": expected in text})
        if selection["table"] == "tab:mechanism-controls":
            expected = formatted(row["target"], selection["target_digits"], 1)
            details.append({"key": key, "field": "target", "display": expected, "pass": expected in text})
    result = {"primary_entries": len(selections), "numeric_tokens": len(details),
        "failures": sum(not item["pass"] for item in details),
        "training": False, "refitting": False, "resampling": False, "details": details}
    if len(selections) != 36 or len({(s["comparison"],s["observable"],s["coordinate"]) for s in selections}) != 36:
        raise RuntimeError("Primary-family coverage is not one-to-one.")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "details"}, indent=2))
    if result["failures"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
