"""Portable, bounded successors to selected archived scientific unit tests.

These tests never collect or run the archived suites or production workflows.
The same fixed fixtures are available from scripts/run_representative_example.py.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("representative_checks", ROOT / "scripts/representative_checks.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


@pytest.mark.parametrize("name", list(checks.CASES))
def test_fixed_implementation_invariant(name):
    result = checks.CASES[name]()
    assert result
