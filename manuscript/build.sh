#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
command -v pdflatex >/dev/null 2>&1 || { echo "pdfLaTeX is required." >&2; exit 1; }
BIBTEX=""
for name in bibtex bibtex.original bibtex8; do
  if command -v "$name" >/dev/null 2>&1 && "$name" --version >/dev/null 2>&1; then
    BIBTEX="$name"
    break
  fi
done
[ -n "$BIBTEX" ] || { echo "BibTeX is required." >&2; exit 1; }
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
"$BIBTEX" main
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
