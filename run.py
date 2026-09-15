#!/usr/bin/env python3
"""Installation-free router for every research workstream."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from stationary_bias.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
