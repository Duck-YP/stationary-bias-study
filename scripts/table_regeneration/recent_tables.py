"""Render recent manuscript tables from saved results, without statistical fitting.

The caller supplies read-only loaders and records input hashes.  Table templates
contain labels and fixed selectors; numerical cells come from the saved files.
``source_rows`` records the input rows/JSON keys and display transformations.
"""

from fractions import Fraction
import math


E4 = "manuscript/supplementary_results/E4/"
E5 = "manuscript/supplementary_results/E5/"
TM = "artifacts/canonical_paper_export/targeted_mechanism/"
PRIMARY = TM + "results/primary_family_36.csv"
ALL_FITS = TM + "results/intercepts_and_contrasts.csv"
CONDITIONS = (
    "rho_minus_symmetric", "rho_zero_symmetric",
    "rho_plus_symmetric", "rho_plus_asymmetric",
)
LAW = "rho_plus_symmetric minus rho_plus_asymmetric"
COVARIANCE = "rho_plus_symmetric minus rho_minus_symmetric"
INTERVAL_FIELDS = ("estimate", "simultaneous_lower", "simultaneous_upper")


def _one(rows, **selector):
    matched = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in selector.items())]
    if len(matched) != 1:
        raise ValueError(f"Expected one saved row for {selector}; found {len(matched)}")
    return matched[0]


def _number(value, digits, scale=1, unsigned_zero=False):
    value = float(value) * scale
    if not math.isfinite(value):
        raise ValueError("Cannot display a non-finite saved table value")
    if unsigned_zero and value == 0:
        value = 0.0
    return f"{value:.{digits}f}"


def _origin(path, row, selector, fields, scale=1, digits=None):
    record = {"path": path, "selector": selector, "fields": list(fields), "scale": scale}
    if "_source_row" in row:
        record["row"] = row["_source_row"]
    if digits is not None:
        record["digits"] = digits
    return record


def _table(headers, rows, sources, source_rows, notes):
    if any(len(row) != len(headers) for row in rows):
        raise ValueError("A regenerated table has inconsistent column counts")
    return {"headers": headers, "rows": rows, "sources": list(dict.fromkeys(sources)),
            "status": "supported", "notes": notes, "source_rows": source_rows}


def _coefficient(rows, comparison, observable, coordinate, grid="full"):
    selector = {"comparison": comparison, "observable": observable,
                "coordinate": coordinate, "estimator": "balance", "grid": grid}
    return _one(rows, **selector), selector


def _fraction_label(value, signed=False):
    ratio = Fraction(str(value))
    label = str(ratio)
    return "+" + label if signed and ratio > 0 else label


def build_recent_tables(load_csv, load_json):
    """Return tables 4, 6, 10, 16, 17 and 22 from immutable saved inputs.

    CSV loaders return string-valued dictionaries, optionally including a
    one-based ``_source_row``.  No simulations, bootstrap, refits or TeX reads
    are performed here.  Fixed selectors retain the manuscript's complete
    displayed rows, including unfavorable results.
    """
    tables = {}
    primary = load_csv(PRIMARY)
    if len(primary) != 36:
        raise ValueError(f"Expected the complete 36-scalar primary family, got {len(primary)}")
    protocol_path = TM + "PROTOCOL_FROZEN.json"
    protocol = load_json(protocol_path)
    condition_labels = {}
    condition_origins = []
    for condition in CONDITIONS:
        cells = [(i, c) for i, c in enumerate(protocol["cells"]) if c["condition"] == condition]
        if not cells or len({(c["rho"], c["asymmetric"]) for _, c in cells}) != 1:
            raise ValueError(f"Missing or inconsistent saved condition metadata: {condition}")
        i, cell = cells[0]
        condition_labels[condition] = (
            _fraction_label(cell["rho"], signed=True),
            "Asymmetric" if cell["asymmetric"] else "Symmetric",
        )
        condition_origins.append({"path": protocol_path,
                                  "selector": {"condition": condition},
                                  "json_keys": [f"cells[{i}].rho", f"cells[{i}].asymmetric"]})

    # Table 4: the matched first coordinate, followed by the fixed law contrast.
    output, origins = [], list(condition_origins)
    for comparison in (*CONDITIONS, LAW):
        row, selector = _coefficient(primary, comparison, "difference", 1)
        labels = (condition_labels[comparison] if comparison in condition_labels
                  else ("Symmetric minus asymmetric (rho="
                        + condition_labels["rho_plus_symmetric"][0] + ")", ""))
        output.append([*labels, _number(row["target"], 6, unsigned_zero=True),
                       *[_number(row[f], 8) for f in INTERVAL_FIELDS]])
        origins.append(_origin(PRIMARY, row, selector, ("target", *INTERVAL_FIELDS),
                               digits={"target": 6, **dict.fromkeys(INTERVAL_FIELDS, 8)}))
    tables[4] = _table(
        ["rho / contrast", "noise law", "target", "estimate", "simultaneous lower", "simultaneous upper"],
        output, [PRIMARY, protocol_path], origins,
        "tab:mechanism-controls; five fixed primary balance/full-grid selections. "
        "Targets use six decimals; estimates and saved simultaneous endpoints use eight.")

    # Table 6: all six nonzero-proxy configurations, at the designated saved K.
    e5_path = E5 + "FULL_VECTOR_ALIGNMENT.csv"
    e5_spec_path = E5 + "E5_POSTHOC_ANALYSIS_SPEC.json"
    e5_spec = load_json(e5_spec_path)
    e5 = [r for r in load_csv(e5_path)
          if int(r["K"]) == int(e5_spec["primary_K"]) and int(r["H"]) > 1]
    if len(e5) != 6 or len({r["cell_id"] for r in e5}) != 6:
        raise ValueError("Expected all six distinct nonzero-proxy E5 configurations")
    e5.sort(key=lambda r: (int(r["H"]), int(r["N"]), float(r["gamma"])))
    base_gamma = max(float(r["gamma"]) for r in e5)
    output, origins = [], [{"path": e5_spec_path, "json_keys": ["primary_K"]}]
    for row in e5:
        quotient = float(row["gamma"]) / base_gamma
        ratio = Fraction(quotient).limit_denominator(1024)
        if abs(float(ratio) - quotient) > 1e-12:
            raise ValueError("Saved E5 step-size ratio has no stable rational display")
        output.append([str(int(row[f])) for f in ("H", "N", "m")] + [str(ratio)]
                      + [_number(row[f], 6) for f in ("cosine", "projection_ratio", "relative_residual")])
        origin = _origin(e5_path, row, {"cell_id": row["cell_id"], "K": e5_spec["primary_K"]},
                         ("H", "N", "m", "gamma", "cosine", "projection_ratio", "relative_residual"),
                         digits={"cosine": 6, "projection_ratio": 6, "relative_residual": 6})
        origin["gamma_display"] = "gamma / maximum gamma among the six saved selected rows; rational denominator <= 1024, checked within 1e-12"
        origins.append(origin)
    tables[6] = _table(
        ["H", "N", "m", "gamma / gamma_b", "cosine", "projection ratio", "relative residual"],
        output, [e5_path, e5_spec_path], origins,
        "tab:e5-bridge; all six nonzero-proxy configurations at the saved primary K; "
        "three alignment statistics use six decimals. Saved point estimates only.")

    # Table 10: recover scalar support by marginalizing the exact rho=0 vector law.
    noise_path = TM + "certificate/independent_model_checks.json"
    noise = load_json(noise_path)["noise_laws"]
    output, origins = [], []
    for name, label in (("symmetric_rademacher", "Symmetric"),
                        ("asymmetric_two_point", "Asymmetric")):
        law = noise[name]
        indexed = [(i, v) for i, v in enumerate(law["vector_laws"]) if v["rho"] == 0]
        if len(indexed) != 1:
            raise ValueError(f"Expected one exact rho=0 certificate for {name}")
        index, vector_law = indexed[0]
        marginal = {}
        for atom in vector_law["support_and_probabilities"]:
            value = atom["epsilon"][0][0]
            marginal[value] = marginal.get(value, Fraction(0)) + Fraction(atom["p"])
        if len(marginal) != 2 or sum(marginal.values(), Fraction(0)) != 1:
            raise ValueError(f"Invalid two-point marginal in the saved {name} certificate")
        output.append([label, "(" + ", ".join(marginal) + ")",
                       "(" + ", ".join(str(p) for p in marginal.values()) + ")",
                       law["moments_exact"]["3"], law["moments_exact"]["4"]])
        prefix = "noise_laws." + name
        origins.append({"path": noise_path, "selector": {"law": name, "rho": 0},
                        "json_keys": [prefix + f".vector_laws[{index}].support_and_probabilities",
                                      prefix + '.moments_exact["3"]', prefix + '.moments_exact["4"]'],
                        "transformation": "first-coordinate marginal; sum exact rational atom probabilities; retain exact symbolic strings"})
    tables[10] = _table(
        ["law", "support", "probabilities", "E[z^3]", "E[z^4]"],
        output, [noise_path], origins,
        "tab:num-noise-laws; exact certificate expressions are preserved, e.g. sqrt(2)/2 "
        "is algebraically the manuscript's 1/sqrt(2). No decimal approximation.")

    # Table 16: twelve two-coordinate individual rows and five paired coord-2 rows.
    output, origins = [], list(condition_origins)
    comparisons = (*CONDITIONS, LAW, COVARIANCE)
    def condition_label(comparison):
        if comparison == LAW:
            return "Law contrast"
        if comparison == COVARIANCE:
            return "Covariance contrast"
        rho, law = condition_labels[comparison]
        return rho + ", " + law.lower()
    for comparison in comparisons:
        for algorithm, short in (("SCAFFOLD", "S"), ("FedAvg", "F")):
            display = [condition_label(comparison), short]
            for coordinate in (1, 2):
                row, selector = _coefficient(primary, comparison, algorithm, coordinate)
                display.extend(_number(row[f], 4, 1000) for f in INTERVAL_FIELDS)
                origins.append(_origin(PRIMARY, row, selector, INTERVAL_FIELDS, scale=1000, digits=4))
            output.append(display)
    for comparison in (*CONDITIONS, LAW):
        row, selector = _coefficient(primary, comparison, "difference", 2)
        output.append([condition_label(comparison), "D", "", "", "",
                       *[_number(row[f], 4, 1000) for f in INTERVAL_FIELDS]])
        origins.append(_origin(PRIMARY, row, selector, INTERVAL_FIELDS, scale=1000, digits=4))
    tables[16] = _table(
        ["condition / contrast", "algorithm", "j1 estimate", "j1 lower", "j1 upper",
         "j2 estimate", "j2 lower", "j2 upper"],
        output, [PRIMARY, protocol_path], origins,
        "tab:mechanism-complement; 17 display rows, 29 saved scalar selections. All numerical "
        "estimates and simultaneous endpoints are multiplied by 1000 and shown to four decimals. "
        "Blank first-coordinate cells in paired rows are display placeholders.")

    # Table 17: fixed restricted-grid sensitivity rows, never outcome-filtered.
    all_fits = load_csv(ALL_FITS)
    output, origins = [], []
    for label, comparison, algorithm, target_digits in (
            ("SCAFFOLD coefficient", "rho_plus_symmetric", "SCAFFOLD", 6),
            ("FedAvg coefficient", "rho_plus_symmetric", "FedAvg", 4),
            ("SCAFFOLD covariance contrast", COVARIANCE, "SCAFFOLD", 5)):
        row, selector = _coefficient(all_fits, comparison, algorithm, 1, "omit_largest_gamma")
        output.append([label, _number(row["target"], target_digits),
                       *[_number(row[f], 8) for f in INTERVAL_FIELDS]])
        origins.append(_origin(ALL_FITS, row, selector, ("target", *INTERVAL_FIELDS),
                               digits={"target": target_digits, **dict.fromkeys(INTERVAL_FIELDS, 8)}))
    tables[17] = _table(
        ["quantity", "target", "estimate", "simultaneous lower", "simultaneous upper"],
        output, [ALL_FITS], origins,
        "tab:num-restricted-mechanism; three fixed balance/omit_largest_gamma/coordinate-1 "
        "selections. No filtering by target inclusion, significance or result status.")

    # Table 22: individual summaries plus genuinely paired saved contrasts.
    e4_path = E4 + "BIAS_VARIANCE_MSE.csv"
    e4_protocol_path = E4 + "E4_v1_PROTOCOL_FROZEN.json"
    e4_protocol = load_json(e4_protocol_path)
    e4_rows = load_csv(e4_path)
    primary_cell, longest = e4_protocol["primary_cell"], max(e4_protocol["K"])
    selected = {algorithm: _one(e4_rows, cell_id=primary_cell, K=longest, algorithm=algorithm)
                for algorithm in ("SCAFFOLD", "FedAvg")}
    if any(row["family"] != "primary" for row in selected.values()):
        raise ValueError("E4 selected rows are not members of the saved primary family")
    origins = [{"path": e4_protocol_path, "json_keys": ["primary_cell", "K"],
                "transformation": "designated primary cell and maximum saved K"}]
    output = []
    def interval(row, field, scale, digits, estimate=True):
        lower = _number(row[field + "_lower_simultaneous"], digits, scale)
        upper = _number(row[field + "_upper_simultaneous"], digits, scale)
        prefix = _number(row[field], digits, scale) + " " if estimate else ""
        return prefix + "[" + lower + ", " + upper + "]"
    for label, field, scale, digits in (("MSE", "MSE", 1e6, 3),
                                       ("Train objective gap", "train_gap", 1e6, 3),
                                       ("Held-out log loss", "test_loss", 1, 6)):
        output.append([label, *[interval(selected[a], field, scale, digits)
                               for a in ("SCAFFOLD", "FedAvg")], ""])
        for algorithm, row in selected.items():
            origins.append(_origin(e4_path, row, {"cell_id": primary_cell, "K": longest, "algorithm": algorithm},
                                   (field, field + "_lower_simultaneous", field + "_upper_simultaneous"),
                                   scale=scale, digits=digits))
    for label, field, scale, digits, show_estimate in (
            ("Delta U", "delta_U", 1e6, 3, True),
            ("Delta V", "delta_V", 1e6, 3, True),
            ("Delta train gap", "delta_train", 1e6, 3, False),
            ("Delta held-out log loss", "delta_test", 1, 8, False)):
        fields = ((field,) if show_estimate else ()) + (field + "_lower_simultaneous", field + "_upper_simultaneous")
        if any(selected["SCAFFOLD"][f] != selected["FedAvg"][f] for f in fields):
            raise ValueError(f"Duplicated saved E4 paired fields disagree: {field}")
        row = selected["SCAFFOLD"]
        output.append([label, "", "", interval(row, field, scale, digits, show_estimate)])
        origins.append(_origin(e4_path, row, {"cell_id": primary_cell, "K": longest, "algorithm": "SCAFFOLD"},
                               fields, scale=scale, digits=digits))
    tables[22] = _table(
        ["quantity", "SCAFFOLD", "FedAvg", "paired contrast"],
        output, [e4_path, e4_protocol_path], origins,
        "tab:e4-primary; seven display rows. Errors and training gaps use scale 1e6 and three "
        "decimals; individual test losses use six decimals, paired test-loss endpoints eight. "
        "All intervals are saved primary-family simultaneous intervals. Paired fields are read "
        "directly and checked for equality across their two duplicated algorithm records.")

    expected_counts = {4: 5, 6: 6, 10: 2, 16: 17, 17: 3, 22: 7}
    if set(tables) != set(expected_counts) or any(len(tables[n]["rows"]) != k for n, k in expected_counts.items()):
        raise ValueError("Unexpected recent-table inventory")
    return tables
