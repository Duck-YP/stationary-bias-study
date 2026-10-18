"""Bounded saved-evidence replay and failure detection, with no statistical fit."""
import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("paper_tables", ROOT / "scripts/regenerate_paper_tables.py")
TABLES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TABLES)


def test_saved_table_export_is_deterministic_and_preserves_gaps(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    receipt = TABLES.regenerate(first)
    TABLES.regenerate(second)
    assert receipt["status"] == "PASS_WITH_DISCLOSED_GAPS"
    assert receipt["active_numbered_tables"] == 22
    assert receipt["source_table_environments"] == 23
    assert receipt["data_exports"] == 21
    assert receipt["coverage_counts"] == {"supported": 17, "partial": 4, "not_computational": 1, "archive": 1}
    assert receipt["exact_decimal_tables"] == 14
    assert receipt["exact_decimal_cells"] == 453
    assert all(receipt["display_validation"][str(n)]["status"] == "PASS" for n in TABLES.DECIMAL_TABLES)
    gap = receipt["display_validation"]["18"]
    assert gap["status"] == "DISCLOSED_PARTIAL"
    assert gap["regenerated_not_displayed"] == {"-0.1080237": 1}
    assert len(gap["displayed_not_regenerated"]) == 5  # Four missing SE thresholds and one rounded cell.
    with (first / "table_18.csv").open(newline="", encoding="utf-8") as handle:
        diagnostic = list(csv.DictReader(handle))
    assert len(diagnostic) == 4
    assert {row["3 x combined SE"] for row in diagnostic} == {"UNAVAILABLE"}
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {p.name: p.read_bytes() for p in second.iterdir()}
    # Every input still has its originally observed bytes after both exports.
    assert all(TABLES.sha(ROOT / path) == record["sha256"] for path, record in receipt["inputs"].items())


def test_changed_saved_values_and_broken_pairs_are_detected():
    inputs = TABLES.SavedInputs(ROOT)
    recent = TABLES.build_recent_tables(inputs.csv, inputs.json)
    metadata = next(row for row in TABLES.TABLES if row["number"] == 4)
    recent[4]["rows"][0][3] = "0.12187858"
    check = TABLES.validate_display(metadata, recent[4], inputs)
    assert check["status"] == "FAIL"
    assert check["regenerated_not_displayed"] == {"0.12187858": 1}

    historical = TABLES.build_historical_tables(inputs.csv, inputs.json, inputs.text)
    metadata = next(row for row in TABLES.TABLES if row["number"] == 18)
    historical[18]["rows"][0][3] = "-0.1408082"
    # A partial table must not swallow an additional unexpected discrepancy.
    assert TABLES.validate_display(metadata, historical[18], inputs)["status"] == "FAIL"

    def broken_paired_csv(path):
        rows = inputs.csv(path)
        if path.endswith("E4/BIAS_VARIANCE_MSE.csv"):
            for row in rows:
                if row["algorithm"] == "FedAvg" and row["family"] == "primary" and row["K"] == "64":
                    row["delta_U"] = str(float(row["delta_U"]) + 1)
        return rows

    with pytest.raises(ValueError, match="Duplicated saved E4 paired fields disagree"):
        TABLES.build_recent_tables(broken_paired_csv, inputs.json)


def test_rejects_output_inside_repository_before_writing():
    with pytest.raises(ValueError, match="outside the repository"):
        TABLES.regenerate(ROOT / "manuscript" / "table_rebuild_should_never_exist")
    assert not (ROOT / "manuscript" / "table_rebuild_should_never_exist").exists()
