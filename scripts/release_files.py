"""Enumerate publication files, excluding local checkout/install/runtime state."""
from pathlib import Path
import os

RUNTIME = {".git", ".venv", "venv", ".deps", "__pycache__", ".pytest_cache",
           ".mplconfig", ".mypy_cache", ".ruff_cache", "regenerated", "publication_scratch",
           "build", "dist"}


def ignored_parts(parts):
    return bool(RUNTIME.intersection(parts)) or any(p.endswith(".egg-info") for p in parts)


def public_files(root: Path):
    for directory, children, names in os.walk(root):
        children[:] = sorted(name for name in children if not ignored_parts([name]))
        for name in sorted(names):
            path = Path(directory) / name
            if not ignored_parts(path.relative_to(root).parts):
                yield path
