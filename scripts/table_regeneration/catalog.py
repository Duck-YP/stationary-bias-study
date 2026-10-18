"""Exhibit identifiers from the finalized 40-page manuscript, not table values.

Numbering was checked against the clean-build main.aux and rendered PDF.  The
inactive reproducibility appendix is deliberately not assigned a table number.
"""
PDF_SHA256 = "81d84cbc4b9730d7fa682bb1b749d22aab053fce0636fa5dd1eeda5f913ae22c"
MAIN = "manuscript/sections/07_numerical_study.tex"
APP = "manuscript/appendix/C_numerical_details.tex"
_ITEMS = [
    (1, "tab:prior-bias-resolution", 3, "2", "Prior analytical resolution", "manuscript/sections/02_related_work.tex"),
    (2, "tab:num-attribution-summary", 11, "6.2.1", "Analytical vectors and finite-grid intercepts", MAIN),
    (3, "tab:supp-control", 13, "6.2.5", "Cartesian-grid control coefficients", MAIN),
    (4, "tab:mechanism-controls", 14, "6.2.7", "Contraction and matched-noise first coordinate", MAIN),
    (5, "tab:supp-policy", 15, "6.3", "Step-size and local-step policies", MAIN),
    (6, "tab:e5-bridge", 17, "6.5", "Post-hoc full-vector alignment", MAIN),
    (7, "tab:num-controlled-settings", 28, "C.1.1", "Controlled experimental settings", APP),
    (8, "tab:num-run-schedules", 29, "C.1.2", "Run schedules", APP),
    (9, "tab:num-inference", 30, "C.1.2", "Sampling-uncertainty procedures", APP),
    (10, "tab:num-noise-laws", 30, "C.1.4", "Exact scalar noise laws", APP),
    (11, "tab:num-core", 31, "C.2.1", "Joint-grid simultaneous intervals", APP),
    (12, "tab:E-h4diag", 32, "C.2.2", "H=4 finite-grid residual diagnostics", APP),
    (13, "tab:E-plateau", 32, "C.2.3", "Fixed-step intercept intervals", APP),
    (14, "tab:E-d5", 33, "C.2.3", "Five-dimensional coefficients", APP),
    (15, "tab:supp-leading", 33, "C.2.4", "Client-dependent leading coefficient", APP),
    (16, "tab:mechanism-complement", 34, "C.2.5", "Contraction and noise-law complementary results", APP),
    (17, "tab:num-restricted-mechanism", 35, "C.2.5", "Restricted-grid first-coordinate sensitivity", APP),
    (18, "tab:E-direct-balance", 35, "C.3.1", "Direct versus balance discrepancies", APP),
    (19, "tab:num-structural-settings", 36, "C.3.2", "Structural consistency settings", APP),
    (20, "tab:num-real-settings", 37, "C.4.1", "Real-data settings", APP),
    (21, "tab:supp-real-full", 38, "C.4.1", "Allocation and partition results", APP),
    (22, "tab:e4-primary", 39, "C.4.3", "Longest-window averaging statistics", APP),
]

TABLES = [dict(number=n, label=label, page=page, section=section,
               title=title, manuscript_source=source, active=True)
          for n, label, page, section, title, source in _ITEMS]
TABLES.append(dict(number=None, label="tab:F-artifacts", page=None,
                   section="inactive appendix D", title="Historical artifact map",
                   manuscript_source="manuscript/appendix/D_reproducibility.tex", active=False))

FIGURES = [
    dict(number=1, label="fig:num-matched-primary", page=11, section="6.2.2",
         panels=["hist_matched_H2", "hist_matched_H4"]),
    dict(number=2, label="fig:E-p2-plateau", page=12, section="6.2.3",
         panels=["hist_fixed_gamma_coord1", "hist_fixed_gamma_coord2"]),
    dict(number=3, label="fig:real-allocation", page=15, section="6.3",
         panels=["real_R0_allocation"]),
    dict(number=4, label="fig:e4-averaging", page=16, section="6.4",
         panels=["e4_averaging_scaffold", "e4_averaging_fedavg"]),
    dict(number=5, label="fig:E-control-h4", page=32, section="C.2.2",
         panels=["hist_H4_smallstep", "hist_H4_loglog_residual"]),
]
