"""Source-backed protocol inventories for manuscript tables 7, 8, 9, 19, 20.

These normalized tables display saved configuration fields and explicit counting
operations. They do not parse manuscript numbers, run models or recalculate CIs.
Missing prose-level settings are disclosed rather than reconstructed by guess.
"""

from collections import Counter
from fractions import Fraction
import json


P2 = "configs/original/p2_multidimensional_validation/configs/"
SUPP = "configs/supplementary/PROTOCOL_FROZEN.json"
MS = "manuscript/supplementary_results/"
TM = "artifacts/canonical_paper_export/targeted_mechanism/"
ORIGINAL = (
    ("Primary joint grid", "d2_coefficient_primary.yaml", "primary_joint_path"),
    ("Smaller-step joint grid", "d2_h4_small_step_confirmation.yaml", "smaller_step_path"),
    ("Fixed-step client count", "d2_fixed_gamma_largeN_plateau.yaml", "fixed_gamma_large_N"),
    ("Five-dimensional", "d5_controlled_validation.yaml", "primary_joint_path"),
)


def _text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _rational(value):
    raw = float(value)
    rational = Fraction(raw).limit_denominator(10**9)
    if abs(float(rational) - raw) > 1e-12:
        return str(value)
    return str(rational)


def _unique(values):
    return sorted(set(values))


def _origin(path, fields, selector=None, **extra):
    result = {"path": path, "fields": list(fields)}
    if selector is not None:
        result["selector"] = selector
    result.update(extra)
    return result


class _Inventory:
    def __init__(self):
        self.rows = []
        self.origins = []

    def add(self, study, field, value, path, keys, **extra):
        self.rows.append([study, field, _text(value)])
        self.origins.append(_origin(path, keys, **extra))

    def result(self, label, missing=()):
        return {"headers": ["study / component", "saved field / derivation", "value"],
                "rows": self.rows,
                "sources": list(dict.fromkeys(o["path"] for o in self.origins)),
                "source_rows": self.origins,
                "status": "partial" if missing else "supported",
                "notes": label + "; normalized source-backed protocol inventory, not verbatim manuscript layout. "
                         + ("Not covered: " + "; ".join(missing) if missing else "All listed manuscript settings are represented by saved fields or explicit counts."),
                "uncovered_fields": list(missing)}


def build_config_tables(load_csv, load_json, load_yaml):
    """Return five tables using caller-controlled read-only, hash-tracked loaders."""
    yaml_cache, json_cache, csv_cache = {}, {}, {}
    def y(path):
        if path not in yaml_cache:
            yaml_cache[path] = load_yaml(path)
        return yaml_cache[path]
    def j(path):
        if path not in json_cache:
            json_cache[path] = load_json(path)
        return json_cache[path]
    def c(path):
        if path not in csv_cache:
            csv_cache[path] = load_csv(path)
        return csv_cache[path]

    supplementary = j(SUPP)
    targeted_path = TM + "PROTOCOL_FROZEN.json"
    targeted = j(targeted_path)
    cert_path = TM + "certificate/independent_model_checks.json"
    certificate = j(cert_path)
    e4_path = MS + "E4/E4_v1_PROTOCOL_FROZEN.json"
    e4 = j(e4_path)
    tables = {}

    # T7: seven fixed studies, complete numerical design metadata.
    rows, origins = [], []
    for label, filename, design_key in ORIGINAL:
        path = P2 + filename
        config, design = y(path), y(path)[design_key]
        h = design.get("H_values", [design.get("H")])
        if "path" in design:
            ns = [p["N"] for p in design["path"]]
            gammas = [str(Fraction(1, p["gamma_denominator"])) for p in design["path"]]
        else:
            ns = design["N_values"]
            gammas = [str(Fraction(1, design["gamma_denominator"]))]
        rows.append([label, str(config["objective"]["d"]), _text(h), _text(ns),
                     _text(gammas), str(config["chains"]["count_per_setting"])])
        origins.append(_origin(path, ["objective.d", design_key, "chains.count_per_setting"],
                               transformation="gamma is exact reciprocal of saved gamma_denominator; retain path pairing"))
    fit_path = MS + "fitted_coefficients.csv"
    for label, role in (("Leading coefficient", "E1a"), ("Cartesian control coefficient", "E1b")):
        selected = [(i, cell) for i, cell in enumerate(supplementary["cells"]) if role in cell["roles"]]
        fits = [row for row in c(fit_path) if row["experiment"] == role and row["window"] == "primary"]
        coordinates = _unique(int(row["coordinate"]) for row in fits)
        if not selected or coordinates != list(range(len(coordinates))) or not coordinates:
            raise ValueError(f"Missing saved design/coordinate inventory for {role}")
        cells = [cell for _, cell in selected]
        rows.append([label, str(len(coordinates)), _text(_unique(cell["H"] for cell in cells)),
                     _text(_unique(cell["N"] for cell in cells)),
                     _text([_rational(g) for g in sorted({cell["gamma"] for cell in cells}, reverse=True)]),
                     str(len(supplementary["production_seeds"]))])
        origins.extend([
            _origin(SUPP, ["cells", "production_seeds"], {"role": role},
                    json_keys=[f"cells[{i}]" for i, _ in selected], transformation="unique H,N,gamma; seed count"),
            _origin(fit_path, ["experiment", "window", "coordinate"], {"experiment": role, "window": "primary"},
                    rows=[row.get("_source_row") for row in fits], transformation="dimension = count of contiguous saved coordinate indices"),
        ])
    cells = targeted["cells"]
    rows.append(["Contraction/noise law", str(len(certificate["third_tensor_at_zero_exact"])),
                 _text([targeted["H"]]), _text(_unique(cell["N"] for cell in cells)),
                 _text([_rational(g) for g in sorted({cell["gamma"] for cell in cells}, reverse=True)]),
                 str(len(targeted["production_seeds"]))])
    origins.extend([_origin(targeted_path, ["H", "cells", "production_seeds"]),
                    _origin(cert_path, ["third_tensor_at_zero_exact"], transformation="dimension = tensor first-axis length")])
    tables[7] = {"headers": ["comparison", "dimension", "H", "client counts N", "step sizes gamma", "runs per configuration"],
                 "rows": rows, "sources": list(dict.fromkeys(o["path"] for o in origins)),
                 "source_rows": origins, "status": "supported", "uncovered_fields": [],
                 "notes": "tab:num-controlled-settings; all seven numerical designs. Joint-path N and gamma lists are paired in source order; supplementary unique sets summarize Cartesian designs. Supplementary dimension is derived from saved coordinate indices, not imported from manuscript prose."}

    # T8: preserve actual cell schedules, including primary/extended distinction.
    inv = _Inventory()
    for label, filename, _ in ORIGINAL:
        path = P2 + filename
        config = y(path)
        selected_keys = ("mixing_mu", "burn_in_multiples", "batch_length_multiples", "min_batches", "max_batches", "extension_batches")
        inv.add(label, "mixing and batch policy", {k: config["protocol"][k] for k in selected_keys},
                path, ["protocol." + k for k in selected_keys])
    for path, document in ((SUPP, supplementary), (targeted_path, targeted)):
        for index, cell in enumerate(document["cells"]):
            study = cell.get("id", cell.get("condition", "targeted")
                             + "; N=" + str(cell["N"]) + "; gamma=" + _rational(cell["gamma"]))
            inv.add(study, "frozen schedule in communication rounds", cell["schedule"], path,
                    [f"cells[{index}].schedule"], selector={"cell_index": index},
                    scope="primary_batches, when present, distinguishes primary analysis from longer recorded tails")
    inv.add("Contraction/noise law", "certified curvature lower bound", certificate["global_bounds"]["mu_exact"],
            cert_path, ["global_bounds.mu_exact"])
    inv.add("Real-data training", "regularization lambda", e4["objective"]["lambda"],
            e4_path, ["objective.lambda"])
    tables[8] = inv.result("tab:num-run-schedules", (
        "the heuristic ceiling formulas are not stored as structured formula fields for supplementary/targeted cells; actual tau/tau0, burn, batch length and batch counts are preserved",
        "original YAML min/max batch policy is a planned policy; this inventory alone does not establish each run's realized stopping batch",
    ))

    # T9: complete uncertainty-method metadata and saved contrast-family counts.
    inv = _Inventory()
    for label, filename in (("Joint grid and fixed step, d=2", "d2_coefficient_primary.yaml"),
                            ("Five-dimensional", "d5_controlled_validation.yaml")):
        path, config = P2 + filename, y(P2 + filename)
        for key in ("per_setting_uncertainty", "bootstrap"):
            inv.add(label, key, config[key], path, [key])
    for key in ("resampling", "ci", "multiplicity", "E1a_primary_fit", "E1b_primary_fit", "E1b_contrast"):
        inv.add("Cartesian/local step", key, supplementary[key], SUPP, [key])
    inv.add("Cartesian/local step", "Student-t degrees of freedom from independent run count",
            len(supplementary["production_seeds"]) - 1, SUPP, ["production_seeds"], transformation="len(production_seeds)-1")
    contrasts_path = MS + "tables/E1_intercept_contrasts.csv"
    contrasts = c(contrasts_path)
    inv.add("Cartesian/local step", "saved contrast scalar counts by kind", dict(Counter(row["kind"] for row in contrasts)),
            contrasts_path, ["kind"], rows=[r.get("_source_row") for r in contrasts], transformation="row count grouped by kind")
    for key in ("bootstrap_draws", "resampling", "intervals", "primary_family"):
        inv.add("Contraction/noise law", key, targeted[key], targeted_path, [key])
    for key in ("ci", "U_statistic", "E3_primary_estimator"):
        inv.add("Real-data allocation", key, supplementary[key], SUPP, [key])
    inv.add("Real-data allocation", "cellwise projection family", supplementary["multiplicity"]["E3_signed_projections"],
            SUPP, ["multiplicity.E3_signed_projections"])
    allocations_path = MS + "tables/E3_policy_allocation_contrasts.csv"
    inv.add("Real-data allocation", "saved allocation/configuration contrast count", len(c(allocations_path)),
            allocations_path, ["cell_id", "baseline_cell_id", "algorithm"], transformation="number of saved contrast rows")
    e4_receipt_path = MS + "E4/STATISTICAL_METHOD_RECEIPT.json"
    e4_receipt = j(e4_receipt_path)
    for key in ("draws", "families", "bootstrap_bias_center_corrected"):
        inv.add("Model averaging", key, e4_receipt[key], e4_receipt_path, [key])
    for key in ("bootstrap", "sensitivity"):
        inv.add("Model averaging", key, e4[key], e4_path, [key])
    e5_receipt_path = MS + "E5/STATISTICAL_METHOD_RECEIPT.json"
    e5_receipt = j(e5_receipt_path)
    for key in ("draws", "scalar_family_size", "vector_family_size", "scalar_and_vector_families_separately_95_percent_not_joint"):
        inv.add("Directional comparison", key, e5_receipt[key], e5_receipt_path, [key])
    e5_spec_path = MS + "E5/E5_POSTHOC_ANALYSIS_SPEC.json"
    e5_spec = j(e5_spec_path)
    for key in ("bootstrap", "intervals", "alpha"):
        inv.add("Directional comparison", key, e5_spec[key], e5_spec_path, [key])
    tables[9] = inv.result("tab:num-inference")

    # T19: rotation config is complete; affine saved checks lack several settings.
    inv = _Inventory()
    rotation_path = P2 + "d2_rotation_invariance.yaml"
    rotation = y(rotation_path)
    for key in ("coordinate_transform", "paired_matrix", "noise_coupling", "initialization"):
        inv.add("Orthogonal rotation", key, rotation[key], rotation_path, [key])
    affine_path = MS + "tables/E2_exact_checks.csv"
    affine = c(affine_path)
    for field in ("N", "H", "rho", "rounds"):
        values = _unique(float(row[field]) if field == "rho" else int(row[field]) for row in affine)
        inv.add("Affine translation", field + " values", values, affine_path, [field],
                rows=[row.get("_source_row") for row in affine], transformation="sorted distinct saved values")
    inv.add("Affine translation", "saved configuration count", len(affine), affine_path, ["N", "H", "rho"],
            transformation="count saved exact-check rows")
    tables[19] = inv.result("tab:num-structural-settings", (
        "affine gamma is absent from E2_exact_checks.csv",
        "affine offset construction a_c=+/-rho*u, translated initialization and matched-noise semantics are not fields in the selected structured affine evidence",
    ))

    # T20: data, recorded configurations, windows and derived operation counts.
    inv = _Inventory()
    data_path = MS + "DATA_MANIFEST.json"
    data = j(data_path)
    for key in ("retained_count", "excluded_count", "subset_seed", "preprocessing"):
        inv.add("Training data and preprocessing", key, data[key], data_path, [key])
    for index, item in enumerate(data["files"]):
        inv.add(item["file"], "dataset validation", item["validation"], data_path, [f"files[{index}].validation"])
    inv.add("Objective", "regularization and evaluation metadata", e4["objective"], e4_path, ["objective"])
    inv.add("Training", "independent paired runs per configuration", len(supplementary["production_seeds"]),
            SUPP, ["production_seeds"], transformation="number of production seed labels")
    real = [(i, cell) for i, cell in enumerate(supplementary["cells"]) if cell["family"] == "E3"]
    shared = [(i, cell) for i, cell in real if cell["regime"] == "R0"]
    for field in ("regime", "partition_seed"):
        inv.add("Client-objective configurations", field, _unique(cell[field] for _, cell in real),
                SUPP, [f"cells[{i}].{field}" for i, _ in real], transformation="sorted distinct saved values")
    allocation = [(i, cell) for i, cell in shared if "allocation" in cell["roles"]]
    inv.add("Fixed-budget shared allocations", "N,m,H,gamma and N*m", [
        {**{k: cell[k] for k in ("N", "m", "H", "gamma")}, "N*m": cell["N"] * cell["m"]}
        for _, cell in sorted(allocation, key=lambda pair: pair[1]["N"])], SUPP,
        [f"cells[{i}]" for i, _ in allocation], transformation="retain saved allocation-role cells; budget=N*m")
    inv.add("Additional shared-objective runs", "all shared configuration metadata", [
        {k: cell[k] for k in ("id", "H", "N", "m", "gamma", "roles")} for _, cell in shared],
        SUPP, [f"cells[{i}]" for i, _ in shared])
    inv.add("Additional shared-objective runs", "shared configuration count", len(shared), SUPP,
            ["cells"], selector={"family": "E3", "regime": "R0"}, transformation="count selected cells")
    for key in ("K", "primary_cell", "same_end_batch", "algorithms"):
        inv.add("Averaging windows", key, e4[key], e4_path, [key])
    primary_cells = [(i, cell) for i, cell in enumerate(e4["cells"]) if cell["id"] == e4["primary_cell"]]
    if len(primary_cells) != 1:
        raise ValueError("Expected one saved E4 primary cell")
    index, primary = primary_cells[0]
    schedule = primary["schedule"]
    tail = max(e4["K"]) * schedule["batch_length"]
    end = schedule["burn"] + tail
    inv.add("Primary averaging horizon", "saved schedule", schedule, e4_path, [f"cells[{index}].schedule"])
    inv.add("Primary averaging horizon", "derived horizon and example-gradient evaluations per algorithm",
            {"longest_window_rounds": tail, "end_round": end,
             "example_gradient_evaluations_per_algorithm": end * primary["H"] * primary["N"] * primary["m"]},
            e4_path, ["K", f"cells[{index}].schedule", f"cells[{index}].H", f"cells[{index}].N", f"cells[{index}].m"],
            transformation="tail=max(K)*batch_length; end=burn+tail; evaluations=end*H*N*m")
    v2_path = MS + "E4/E4_v2_PROTOCOL_FROZEN.json"
    v2 = j(v2_path)
    pilot = v2["pilot_schedule"]
    inv.add("Longer-run pilots", "pilot count and frozen schedule",
            {"pilot_runs": len(v2["pilot_seeds"]), **pilot,
             "total_rounds": pilot["burn"] + pilot["batches"] * pilot["batch_length"]},
            v2_path, ["pilot_seeds", "pilot_schedule"], transformation="pilot count=len(pilot_seeds); total=burn+batches*batch_length")
    tables[20] = inv.result("tab:num-real-settings", (
        "sampling-with-replacement rule and L_sample/base-step formula are not structured fields in the selected protocols (actual gamma values are saved)",
        "the label conversion to {0,1}, equal-client weighting, random-IID and two-label-shards construction are not regenerated from regime identifiers alone",
        "the prose distinction between one primary and two alternative partitions is not inferred solely from the saved partition-seed set",
    ))

    if set(tables) != {7, 8, 9, 19, 20}:
        raise ValueError("Unexpected configuration-table inventory")
    for number, table in tables.items():
        if not table["rows"] or any(len(row) != len(table["headers"]) for row in table["rows"]):
            raise ValueError(f"Malformed configuration table {number}")
        if any(not isinstance(cell, str) for row in table["rows"] for cell in row):
            raise ValueError(f"Non-string display cell in configuration table {number}")
    return tables
