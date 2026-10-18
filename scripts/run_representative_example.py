"""Run fixed tiny implementation examples, writing JSON only when requested.

Usage: python scripts/run_representative_example.py [--output PATH]
No experiment configuration, production workflow, or saved scientific output is changed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from representative_checks import run_checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="optional new JSON report path (refuses overwrite)")
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error(f"Refusing to overwrite {args.output}")
    result = run_checks()
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
