# SCAFFOLD — final concise editorial polish (2026-10-13)

## Scope

Base: `SCAFFOLD_Reader_Focused_20261012.zip` (35-page manuscript).

Only two LaTeX source files changed:

- `manuscript/main.tex`: shortened the Abstract's concluding account of the controlled experiments, finite-tail averaged-model parameter error, and post-hoc curvature–noise directional comparison. Explicitly retains *finite-tail* and *post-hoc* qualifiers without listing detailed limitations in the Abstract.
- `manuscript/sections/01_introduction.tex`: rewrote *Significance and scope* into two concise sentences. It now directly connects the unresolved second-order coefficient in cited stationary expansions to the new separation of ordinary local-update and persistent-control contributions, leaving generic extension topics out of this paragraph.

## Preserved

No changes to the contribution list, Related Work, Setting, Main Results, mechanism, numerical study, Discussion, Conclusion, proofs, references, figures, numerical values, confidence intervals, or supplementary results. All original historical diagnostics remain intact.

## Empirical-claim consistency

Checked the manuscript's terminology against the reported experiments. The terms *finite-tail*, *post-hoc*, and *directional agreement* remain properly scoped. The Abstract does not call the real-data directional comparison a validation of the additive-noise control coefficient, and the numerical sections continue to distinguish sampled model averaging from a certified stationary law.

No further empirical-claim edits were necessary.

## Build and layout check

Compiled from source with `sh build.sh` using pdfLaTeX/BibTeX. The PDF remains 35 pages, with no undefined references, duplicate labels, overfull or underfull boxes, or LaTeX warning messages. The figure files were not redrawn or resized; later figure-placement and caption polishing can proceed separately.

To rebuild, enter `manuscript/` and run `sh build.sh`.
