"""Independent symbolic/numerical certificate for the targeted trigonometric model.

Derivations start from the scalar objective and exact noise supports. The supplied
reference is imported only *after* independent targets have been constructed.
Run with an existing Python environment providing numpy and sympy:
  python independent_model_checks.py
All outputs are written alongside this file. No stationary simulation is run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import sympy as sp


HERE = Path(__file__).resolve().parent
BRIEF = HERE.parent / "brief" / "SCAFFOLD_Targeted_Closure_20261014"
REF_PATH = BRIEF / "null_model_reference.py"
TARGET_PATH = BRIEF / "ANALYTICAL_TARGETS_CHECKED.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(value):
    if isinstance(value, sp.MatrixBase):
        return [[str(sp.simplify(value[i, j])) for j in range(value.cols)]
                for i in range(value.rows)]
    if isinstance(value, (list, tuple)):
        return [exact(v) for v in value]
    return str(sp.simplify(value))


def array(value):
    return np.array(value, dtype=float)


def main():
    x1, x2, rho = sp.symbols("x1 x2 rho", real=True)
    xs = (x1, x2)
    alpha = sp.Rational(1, 20)
    H = sp.Integer(4)
    scalar_f = ((x1*x1 + 2*x2*x2) / 2
                + alpha * (-4*(sp.sin(x1)-x1)
                           + sp.sin(x1+x2)-(x1+x2)
                           + sp.sin(x1-x2)-(x1-x2)))
    grad = sp.Matrix([sp.diff(scalar_f, x) for x in xs])
    hess = sp.hessian(scalar_f, xs)
    origin = {x1: 0, x2: 0}
    A = hess.subs(origin)
    assert A == sp.diag(1, 2)
    assert grad.subs(origin) == sp.zeros(2, 1)
    q = grad - A * sp.Matrix(xs)
    stable_q = sp.Matrix([
        4*alpha*(sp.sin(x1/2)**2-sp.cos(x1)*sp.sin(x2/2)**2),
        -2*alpha*sp.sin(x1)*sp.sin(x2),
    ])
    assert all(sp.trigsimp(sp.expand_trig(a-b), method="fu") == 0
               for a, b in zip(q, stable_q))
    factored_q = sp.Matrix([
        4*alpha*(sp.sin((x1+x2)/2)*sp.sin((x1-x2)/2)
                 + 2*sp.sin(x1/2)**2*sp.sin(x2/2)**2),
        -2*alpha*sp.sin(x1)*sp.sin(x2),
    ])
    assert all(sp.trigsimp(sp.expand_trig(a-b), method="fu") == 0
               for a, b in zip(q, factored_q))
    analytic_hess = sp.Matrix([
        [1+2*alpha*sp.sin(x1)*(2-sp.cos(x2)),
         -2*alpha*sp.cos(x1)*sp.sin(x2)],
        [-2*alpha*sp.cos(x1)*sp.sin(x2),
         2-2*alpha*sp.sin(x1)*sp.cos(x2)],
    ])
    assert all(sp.trigsimp(sp.expand_trig(a-b)) == 0
               for a, b in zip(hess, analytic_hess))
    T = [[[sp.diff(scalar_f, xs[i], xs[j], xs[k]).subs(origin)
           for k in range(2)] for j in range(2)] for i in range(2)]
    assert sum(v*v for plane in T for row in plane for v in row) > 0
    # Every order j >= 2 derivative of sin(v.x)-v.x has tensor norm <= ||v||^j.
    ridge_vectors = [sp.Matrix([1, 0]), sp.Matrix([1, 1]), sp.Matrix([1, -1])]
    ridge_weights = [-4, 1, 1]
    ridge_bounds = {
        j: sp.simplify(alpha * sum(abs(w) * (v.dot(v))**sp.Rational(j, 2)
                                   for w, v in zip(ridge_weights, ridge_vectors)))
        for j in range(2, 6)
    }
    assert ridge_bounds[2] == sp.Rational(2, 5)
    mu, L = sp.Integer(1)-ridge_bounds[2], sp.Integer(2)+ridge_bounds[2]
    assert mu == sp.Rational(3, 5) and L == sp.Rational(12, 5)
    non_even_gap = sp.simplify(scalar_f.subs({x1: sp.pi/2, x2: 0})
                             - scalar_f.subs({x1: -sp.pi/2, x2: 0}))
    assert non_even_gap != 0

    def contraction(M):
        return sp.Matrix([sum(T[i][j][k]*M[j, k]
                              for j in range(2) for k in range(2))
                          for i in range(2)])

    m11, m12, m22 = sp.symbols("m11 m12 m22")
    general_contraction = contraction(sp.Matrix([[m11, m12], [m12, m22]]))
    C = sp.diag(1+rho, 1-rho)
    s11, s12, s22 = sp.symbols("s11 s12 s22")
    unknown_S = sp.Matrix([[s11, s12], [s12, s22]])
    sol = sp.solve(list(A*unknown_S+unknown_S*A-C), (s11, s12, s22), dict=True)
    assert len(sol) == 1
    S = unknown_S.subs(sol[0])
    assert sp.simplify(A*S+S*A-C) == sp.zeros(2)
    b11 = -A.inv()*contraction(S)/2
    # Coefficient definitions independently transcribed from local manuscript
    # sections/04_main_results.tex, not from null_model_reference.theory().
    b20_scaffold = -(H-1)*(5*H-1)/(12*H)*A.inv()*contraction(C)
    b20_fedavg = -(H-1)/4*A.inv()*contraction(C)
    b20_control = -(H-1)*(2*H-1)/(12*H)*A.inv()*contraction(C)
    assert sp.simplify(b20_scaffold-b20_fedavg-b20_control) == sp.zeros(2, 1)
    assert contraction(C).subs(rho, 0) == sp.zeros(2, 1)
    assert b11.subs(rho, 0) == sp.Matrix([-sp.Rational(1, 80), 0])
    gamma_imported = min(sp.Integer(1), 1/(48*L), 1/(24*H*(L+mu)))
    assert gamma_imported == sp.Rational(1, 288)
    assert all(sp.Rational(1, d) < gamma_imported for d in (512, 1024, 2048))
    derived_rows = []
    for rv in (-sp.Rational(1, 4), sp.Integer(0), sp.Rational(1, 4)):
        expr = {"A": A, "C": C, "S_C": S, "T_C": contraction(C),
                "T_S_C": contraction(S), "B11": b11,
                "B20_scaffold": b20_scaffold, "B20_fedavg": b20_fedavg,
                "B20_control": b20_control}
        vals = {name: value.subs(rho, rv) for name, value in expr.items()}
        numeric_vals = {name: (array(value).ravel().tolist() if value.cols == 1
                              else array(value).tolist()) for name, value in vals.items()}
        derived_rows.append({"rho": float(rv), "H": 4, "exact": {name: exact(v) for name, v in vals.items()},
                             "numeric": numeric_vals})

    laws = {
        "symmetric_rademacher": ([-sp.Integer(1), sp.Integer(1)], [sp.Rational(1, 2)]*2),
        "asymmetric_two_point": ([sp.sqrt(2), -1/sp.sqrt(2)], [sp.Rational(1, 3), sp.Rational(2, 3)]),
    }
    noise = {}
    for name, (support, probs) in laws.items():
        moments = {j: sp.simplify(sum(p*v**j for p, v in zip(probs, support)))
                   for j in range(1, 7)}
        assert moments[1] == 0 and moments[2] == 1
        rows = []
        for rv in (-sp.Rational(1, 4), sp.Integer(0), sp.Rational(1, 4)):
            cov = C.subs(rho, rv)
            root = sp.diag(sp.sqrt(cov[0, 0]), sp.sqrt(cov[1, 1]))
            weighted = [(sp.simplify(probs[i]*probs[j]), root*sp.Matrix([support[i], support[j]]))
                        for i, j in itertools.product(range(2), repeat=2)]
            mean = sum((p*v for p, v in weighted), sp.zeros(2, 1)).applyfunc(sp.simplify)
            second = sum((p*(v*v.T) for p, v in weighted), sp.zeros(2)).applyfunc(sp.simplify)
            assert mean == sp.zeros(2, 1) and second == cov
            max_norm_sq = max(sp.simplify(v.dot(v)) for _, v in weighted)
            assert max_norm_sq <= 4 and max_norm_sq < 5
            rows.append({"rho": float(rv), "mean_exact": exact(mean),
                         "covariance_exact": exact(second),
                         "maximum_norm_squared_exact": exact(max_norm_sq),
                         "support_and_probabilities": [{"p": exact(p), "epsilon": exact(v)} for p, v in weighted]})
        noise[name] = {"moments_exact": {str(j): exact(v) for j, v in moments.items()},
                       "moments_numeric": {str(j): float(v) for j, v in moments.items()},
                       "vector_laws": rows}
    assert noise["symmetric_rademacher"]["moments_exact"]["3"] == "0"
    assert noise["asymmetric_two_point"]["moments_exact"]["3"] == "sqrt(2)/2"
    assert noise["asymmetric_two_point"]["moments_exact"]["4"] == "3/2"

    # Only now load the provided reference to compare against independent work.
    spec = importlib.util.spec_from_file_location("provided_reference", REF_PATH)
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    result = subprocess.run([sys.executable, str(REF_PATH)], capture_output=True,
                            text=True, check=True)
    (HERE / "attachment_reference_stdout.json").write_text(result.stdout, encoding="utf-8")
    reference_output = json.loads(result.stdout)
    supplied = json.loads(TARGET_PATH.read_text(encoding="utf-8"))
    target_max_difference = 0.0
    for row, ref_row, supplied_row in zip(derived_rows, reference_output["targets"], supplied["targets"]):
        assert row["rho"] == ref_row["rho"] == supplied_row["rho"]
        for key, value in row["numeric"].items():
            for candidate in (ref_row, supplied_row):
                delta = float(np.max(np.abs(array(value)-array(candidate[key]))))
                target_max_difference = max(target_max_difference, delta)
                np.testing.assert_allclose(value, candidate[key], rtol=0, atol=2e-15)
    for name, value in noise.items():
        for j, moment in value["moments_numeric"].items():
            np.testing.assert_allclose(moment, reference_output["noise_moments"][name][f"moment_{j}"], rtol=0, atol=3e-15)

    independent_gradient = sp.lambdify(xs, grad, "numpy")
    independent_hessian = sp.lambdify(xs, hess, "numpy")
    independent_objective = sp.lambdify(xs, scalar_f, "numpy")
    rng = np.random.default_rng(202610140731)
    points = np.vstack([np.zeros((1, 2)), rng.uniform(-2, 2, size=(300, 2)),
                        rng.uniform(-100, 100, size=(100, 2)),
                        np.array([[1e-2, -2e-2], [1e-6, -2e-6], [1e-12, -2e-12]])])
    numeric = {"points_checked": len(points), "max_gradient_absolute_difference": 0.0,
               "max_hessian_absolute_difference": 0.0, "max_objective_absolute_difference": 0.0}
    for point in points:
        grad_own = array(independent_gradient(*point)).ravel()
        hess_own = array(independent_hessian(*point))
        grad_ref, hess_ref = reference.gradient(point), reference.hessian(point)
        np.testing.assert_allclose(grad_ref, grad_own, rtol=2e-15, atol=3e-14)
        np.testing.assert_allclose(hess_ref, hess_own, rtol=0, atol=3e-15)
        numeric["max_gradient_absolute_difference"] = max(numeric["max_gradient_absolute_difference"], float(np.max(np.abs(grad_ref-grad_own))))
        numeric["max_hessian_absolute_difference"] = max(numeric["max_hessian_absolute_difference"], float(np.max(np.abs(hess_ref-hess_own))))
        numeric["max_objective_absolute_difference"] = max(numeric["max_objective_absolute_difference"], float(abs(reference.objective(point)-independent_objective(*point))))
    # Independent high-precision derivative evaluation addresses cancellation
    # near zero, where a double-precision subtractive cosine formula is unsuitable.
    small_rows = []
    factored_numeric = sp.lambdify(xs, factored_q, "numpy")
    for exponent in (2, 4, 6, 8, 10, 12):
        a = sp.Rational(1, 10**exponent)
        for b in (-2*a, a, sp.Integer(0)):
            own = np.array([float(v.subs({x1: a, x2: b}).evalf(80)) for v in q])
            ref = reference.nonlinear_gradient([float(a), float(b)])
            factored = array(factored_numeric(float(a), float(b))).ravel()
            # The supplied form subtracts O(||x||^2) terms, even where q1 is
            # quartic. Use its operation scale, not a relative bound on q1.
            roundoff_bound = 64*np.finfo(float).eps*float(alpha)*(float(a)**2+float(b)**2)
            np.testing.assert_allclose(ref, own, rtol=3e-15, atol=roundoff_bound)
            np.testing.assert_allclose(factored, own, rtol=3e-15, atol=1e-60)
            small_rows.append({"x_exact": [str(a), str(b)], "independent_q": own.tolist(),
                               "reference_q": ref.tolist(), "factored_q": factored.tolist(),
                               "reference_absolute_roundoff_bound": roundoff_bound,
                               "max_abs_error": float(np.max(np.abs(ref-own))),
                               "max_factored_abs_error": float(np.max(np.abs(factored-own)))})
    numeric["near_zero_high_precision_checks"] = small_rows
    output = {
        "status": "PASS_INDEPENDENT_MODEL_AND_EXACT_NOISE_CHECKS",
        "scope": "Analytical construction and provided reference only; no stationary simulation or theorem proof.",
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform(), "numpy": np.__version__, "sympy": sp.__version__},
        "source_hashes": {str(p.relative_to(HERE.parent)): sha256(p) for p in (REF_PATH, TARGET_PATH, HERE / "independent_model_checks.py")},
        "objective_exact": str(scalar_f), "gradient_exact": exact(grad),
        "independently_checked_factored_q": exact(factored_q),
        "hessian_exact": exact(hess), "third_tensor_at_zero_exact": [[[str(v) for v in row] for row in plane] for plane in T],
        "general_contraction_exact": exact(general_contraction),
        "non_central_evenness_gap_at_pi_over_2_exact": exact(non_even_gap),
        "global_bounds": {"mu_exact": exact(mu), "L_exact": exact(L),
                          "ridge_derivative_norm_bounds_exact": {str(j): exact(v) for j, v in ridge_bounds.items()},
                          "ridge_derivative_norm_bounds_numeric": {str(j): float(v) for j, v in ridge_bounds.items()},
                          "bounded_derivative_interpretation": "Hessian and orders 3-5 are bounded. The gradient is necessarily unbounded under global strong convexity.",
                          "gamma_imported_exact": exact(gamma_imported),
                          "gamma0_full_theorem_certified": False},
        "targets": derived_rows, "noise_laws": noise,
        "reference_comparison_max_target_absolute_difference": target_max_difference,
        "numeric_reference_checks": numeric,
        "noise_independence_limitation": "Exact marginal moments verified. Fresh-block independence is a generator/design property, to be checked in the production path; no finite sample can prove probabilistic independence.",
    }
    path = HERE / "independent_model_checks.json"
    path.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "output": str(path),
                      "target_max_abs_difference": target_max_difference,
                      "points_checked": len(points), "near_zero_checks": len(small_rows)}, indent=2))


if __name__ == "__main__":
    main()
