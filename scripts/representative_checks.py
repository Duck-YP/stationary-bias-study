"""Fixed, small implementation checks; no stationary simulation or fitted results.

The fixtures adapt the archived core, p2 rotation, p3 algorithm/theory, and
targeted/tests.py checks. They invoke the preserved scientific implementations,
but compare them with explicit arithmetic, exact finite supports, or independent
linear-algebra identities. Maximum clients=3, local steps=4, rounds=17 per call.
"""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import itertools
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


@lru_cache(maxsize=1)
def targeted_modules():
    """Import the preserved snapshot without installing it as a new package."""
    directory = ROOT / "src/targeted_mechanism_snapshot/targeted"
    package_name = "_representative_targeted_snapshot"
    spec = importlib.util.spec_from_file_location(
        package_name, directory / "__init__.py",
        submodule_search_locations=[str(directory)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = package
    spec.loader.exec_module(package)
    result = []
    for name in ("model", "kernels"):
        full_name = f"{package_name}.{name}"
        spec = importlib.util.spec_from_file_location(full_name, directory / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        spec.loader.exec_module(module)
        result.append(module)
    return tuple(result)


def close(actual, expected, *, atol=2e-13):
    np.testing.assert_allclose(actual, expected, rtol=0., atol=atol)
    return float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))


def fixture(H=3):
    x = np.array([.31, -.23])
    controls = np.array([[.12, -.04], [-.05, .09], [-.07, -.05]])
    # Different clients, coordinates, and local steps prevent cancellation-only tests.
    eps = (np.arange(H * 3 * 2).reshape(H, 3, 2) % 11 - 5) / 13.
    return x, controls, eps


def scalar_update_arithmetic():
    from stationary_bias.core.algorithms.scaffold import scaffold_round
    from stationary_bias.core.models.objectives import MAIN_OBJECTIVE
    from stationary_bias.workstreams.p1_matched_fedavg.fedavg import fedavg_round
    x, gamma = .21, .04
    controls = np.array([.13, -.08, -.05])
    eps = np.array([[.3, -.2, .1], [-.4, .2, .15], [.1, .25, -.3]])
    errors = {}
    for scaffold in (False, True):
        theta = np.full(3, x)
        qbar = []
        for noise in eps:
            q = .5 * np.log(np.cosh(theta))
            qbar.append(q.mean())
            theta -= gamma * (theta + q + noise + (controls if scaffold else 0))
        if scaffold:
            result = scaffold_round(x, controls, gamma=gamma, H=3,
                                    objective=MAIN_OBJECTIVE, epsilon_steps=eps)
            errors["scaffold_control"] = close(
                result.xi_new, controls + (theta - theta.mean()) / (gamma * 3))
        else:
            result = fedavg_round(x, gamma=gamma, H=3,
                                  objective=MAIN_OBJECTIVE, epsilon_steps=eps)
        label = "scaffold" if scaffold else "fedavg"
        errors[label] = max(close(result.theta_final, theta),
                            close(result.x_new, theta.mean()), close(result.qbar, qbar))
    return errors


def vector_and_compiled_arithmetic():
    from stationary_bias.workstreams.p2_multidimensional_validation.objective import controlled_objective
    from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import scaffold_round_many_vector
    from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.algorithm import fedavg_round_many_vector
    from study.kernels import production_round, reference
    objective = controlled_objective()
    x, controls, eps = fixture()
    gamma = .04
    errors = {}
    for scaffold in (False, True):
        theta = np.tile(x, (3, 1))
        before, qbars = [], []
        for noise in eps:
            before.append(theta.copy())
            # Independent direct log(cosh) is accurate for these bounded fixtures.
            q = objective.alpha * np.log(np.cosh(theta @ objective.u))[:, None] * objective.u
            qbars.append(q.mean(axis=0))
            theta -= gamma * (theta @ objective.A.T + q + noise + (controls if scaffold else 0))
        mean = theta.mean(axis=0)
        expected_controls = controls + (theta - mean) / (gamma * 3) if scaffold else controls
        kwargs = dict(gamma=gamma, H=3, objective=objective, epsilon_steps=eps[None])
        result = (scaffold_round_many_vector(x[None], controls[None], **kwargs)
                  if scaffold else fedavg_round_many_vector(x[None], **kwargs))
        label = "scaffold" if scaffold else "fedavg"
        errors[label + "_vector"] = max(close(result.theta_final[0], theta),
                                         close(result.x_new[0], mean), close(result.qbar[0], qbars))
        if scaffold:
            errors["vector_control"] = close(result.xi_new[0], expected_controls)
        for name, fn in (("compiled", production_round), ("reference", reference)):
            got = fn(x, controls, gamma, eps, scaffold, np.zeros_like(controls),
                     objective.A, objective.alpha, objective.u)
            errors[f"{label}_{name}"] = max(close(got[0], mean), close(got[1], expected_controls),
                                              close(got[2], theta), close(got[3], before))
    return errors


def targeted_reference_and_controls():
    model, kernels = targeted_modules()
    x, controls, eps = fixture(H=4)
    states = np.stack([x, x + [.02, -.01]])
    gamma = 1 / 64
    weights, B, PH = model.operators(gamma, 4)
    errors = {}
    # A nonzero mean is intentionally preserved: this detects a hidden projection.
    for label, mean in (("zero_mean", np.zeros(2)), ("nonzero_mean", np.array([.1, -.06]))):
        c = controls + mean
        current = states.copy()
        expected_mean = c.mean(axis=0)
        max_state = max_control = max_mean = max_balance = 0.
        for t in range(7):
            noise = np.roll(eps, t % 3, axis=1)
            expected = model.reference_round(current, c, gamma, noise)
            got = kernels.explicit_round(current, c, gamma, noise, weights, B, PH)
            max_state = max(max_state, close(got[0], expected[0]))
            max_control = max(max_control, close(got[1], expected[1]))
            max_mean = max(max_mean, close(got[1].mean(axis=0), expected_mean))
            q = np.array([[[model.q_stable(point) for point in clients]
                           for clients in algorithms] for algorithms in expected[2]])
            qb = np.sum(weights[:, None, :] * q.mean(axis=2), axis=0)
            max_balance = max(max_balance, close(got[2], -gamma * qb / B))
            # Mean controls add the known weighted linear forcing to SCAFFOLD.
            forcing = np.stack([-gamma * weights.sum(axis=0) * expected_mean, np.zeros(2)])
            close(got[4], forcing)
            current, c = got[:2]
        errors[label] = dict(state=max_state, control=max_control,
                             mean_control=max_mean, balance=max_balance)
    points = [np.array([.3, -.8]), np.array([-2., .7]), np.array([1e-9, -1e-9])]
    errors["gradient_decomposition"] = max(
        close(kernels.q_compiled(*p, model.ALPHA), model.gradient_reference(p) - model.A @ p,
              atol=8e-16) for p in points)
    return errors


def deterministic_and_quadratic_boundaries():
    model, kernels = targeted_modules()
    x, c, eps = fixture(H=4)
    state = np.stack([x, x])
    gamma = 1 / 32
    weights, B, PH = model.operators(gamma, 4)
    got = kernels.explicit_round(state, c, gamma, eps, weights, B, PH, 0.)
    eta = -gamma * (weights * eps.mean(axis=1)).sum(axis=0)
    errors = {"quadratic_affine_recursion": close(got[0], state * PH + eta),
              "quadratic_balance_zero": close(got[2], np.zeros((2, 2)), atol=0.)}
    current, controls = state.copy(), np.zeros_like(c)
    for _ in range(7):
        current, controls, *_ = kernels.explicit_round(
            current, controls, gamma, np.zeros_like(eps), weights, B, PH)
        close(current[0], current[1], atol=2e-15)
        close(controls, np.zeros_like(c), atol=2e-15)
    errors["deterministic_equal_paths"] = close(current[0], current[1])
    origin = kernels.explicit_round(np.zeros_like(state), np.zeros_like(c), gamma,
                                   np.zeros_like(eps), weights, B, PH)
    close(origin[0], np.zeros_like(state), atol=0.)
    close(origin[1], np.zeros_like(c), atol=0.)
    errors["origin_exact"] = True
    weights, B, PH = model.operators(gamma, 1)
    current, controls = state.copy(), c.copy()
    for _ in range(7):
        current, controls, *_ = kernels.explicit_round(
            current, controls, gamma, eps[:1], weights, B, PH)
        close(current[0], current[1], atol=2e-15)
    errors["H1_equal_server_paths"] = close(current[0], current[1])
    return errors


def exact_noise_moments_and_indexing():
    from stationary_bias.workstreams.p2_multidimensional_validation.noise import covariance_cholesky
    _, kernels = targeted_modules()
    covariance = np.array([[1., .3], [.3, .7]])
    signs = np.array(list(itertools.product((-1., 1.), repeat=2)))
    samples = signs @ covariance_cholesky(covariance).T
    errors = {"correlated_mean": close(samples.mean(axis=0), np.zeros(2)),
              "correlated_covariance": close(samples.T @ samples / 4, covariance)}
    for asymmetric in (False, True):
        values = np.array([np.sqrt(2), -1 / np.sqrt(2)]) if asymmetric else np.array([-1., 1.])
        probabilities = np.array([1 / 3, 2 / 3]) if asymmetric else np.array([.5, .5])
        close(probabilities @ values, 0.)
        close(probabilities @ values**2, 1.)
        third = probabilities @ values**3
        close(third, 1 / np.sqrt(2) if asymmetric else 0.)
        for rho in (-.25, 0., .25):
            pairs = list(itertools.product(range(2), repeat=2))
            support = np.array([[values[i], values[j]] for i, j in pairs]) * np.sqrt([1 + rho, 1 - rho])
            mass = np.array([probabilities[i] * probabilities[j] for i, j in pairs])
            close(mass @ support, np.zeros(2))
            close(np.einsum("n,ni,nj->ij", mass, support, support), np.diag([1 + rho, 1 - rho]))
        # Check indexed law mapping, not empirical frequency or PRNG independence.
        observed = []
        for t in range(4):
            for slot in range(6):
                word = int(kernels.noise_word(np.uint64(991), t, 1, slot))
                if word == 2**64 - 1:
                    raise AssertionError("Fixture unexpectedly enters the rejection branch")
                expected = (np.sqrt(2) if word % 3 == 0 else -1 / np.sqrt(2)) if asymmetric else (1. if word & 1 else -1.)
                value = kernels.scalar_noise(np.uint64(991), t, 1, slot, asymmetric)
                close(value, expected, atol=0.)
                observed.append(value)
        np.testing.assert_array_equal(np.unique(observed), np.sort(values))
        errors["asymmetric" if asymmetric else "symmetric"] = {
            "mean": float(probabilities @ values), "variance": float(probabilities @ values**2),
            "third_moment": float(third), "indexed_values_checked": 24,
        }
    return errors


def tensor_lyapunov_and_formulas():
    from stationary_bias.workstreams.p2_multidimensional_validation.objective import controlled_objective
    from stationary_bias.workstreams.p2_multidimensional_validation.theory import vector_theory_targets
    from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.theory import fedavg_vector_theory_targets
    from stationary_bias.core.theory.one_dimensional import b20_total
    model, _ = targeted_modules()
    objective = controlled_objective()
    A, u, alpha = objective.A, objective.u, objective.alpha
    C = np.array([[1., .3], [.3, .7]])
    # An eigenbasis solution is independent of the implementation's Kronecker solve.
    lam, V = np.linalg.eigh(A)
    S = V @ ((V.T @ C @ V) / (lam[:, None] + lam[None, :])) @ V.T
    T = alpha * np.einsum("i,j,k->ijk", u, u, u)
    TC = np.einsum("ijk,jk->i", T, C)
    TS = np.einsum("ijk,jk->i", T, S)
    errors = {"lyapunov": close(A @ S + S @ A, C),
              "tensor_contraction": close(objective.third_derivative_contraction(C), TC)}
    for H in (1, 2, 4):
        sc = vector_theory_targets(objective, C, H)
        fa = fedavg_vector_theory_targets(objective, C, H)
        base = np.linalg.solve(A, TC)
        close(sc.S_C, S)
        close(sc.B11_d, -.5 * np.linalg.solve(A, TS))
        close(fa.B11_d, sc.B11_d)
        close(fa.B20_FA, -(H - 1) / 4 * base)
        close(sc.B20_ctrl, -(H - 1) * (2 * H - 1) / (12 * H) * base)
        close(sc.B20, fa.B20_FA + sc.B20_ctrl)
    close(b20_total(2), -.1875, atol=0.)
    close(b20_total(4), -.59375, atol=0.)
    # Independent trigonometric third derivative tensor at zero.
    T = np.zeros((2, 2, 2))
    T[0, 0, 0] = 2 * model.ALPHA
    T[0, 1, 1] = T[1, 0, 1] = T[1, 1, 0] = -2 * model.ALPHA
    for rho in (-.25, 0., .25):
        C = np.diag([1 + rho, 1 - rho])
        S = np.diag(np.diag(C) / (2 * np.diag(model.A)))
        tc = np.linalg.solve(model.A, np.einsum("ijk,jk->i", T, C))
        b11 = -.5 * np.linalg.solve(model.A, np.einsum("ijk,jk->i", T, S))
        for H in (1, 2, 4):
            targets = model.targets(rho, H)
            close(targets["B11"], b11)
            close(targets["FedAvg"], -(H - 1) / 4 * tc)
            close(targets["difference"], -(H - 1) * (2 * H - 1) / (12 * H) * tc)
            close(targets["SCAFFOLD"], targets["FedAvg"] + targets["difference"])
        if rho == 0:
            close(tc, np.zeros(2), atol=0.)
            if np.linalg.norm(T) == 0 or np.linalg.norm(b11) == 0:
                raise AssertionError("Null coefficient fixture must retain a nonzero tensor and B11")
    errors["nontrivial_null_tensor_norm"] = float(np.linalg.norm(T))
    return errors


def affine_translation():
    from study.kernels import production_round
    from study.model import A, ALPHA, U
    x, controls, eps = fixture()
    shifts = np.array([[.2, -.1], [-.05, .16], [-.15, -.06]])
    close(shifts.sum(axis=0), np.zeros(2))
    homogeneous, translated = x.copy(), x.copy()
    c, translated_c = controls.copy(), controls - shifts
    max_x = max_c = max_local = 0.
    for t in range(7):
        noise = np.roll(eps, t % 3, axis=1)
        a = production_round(homogeneous, c, .04, noise, True, np.zeros_like(shifts), A, ALPHA, U)
        b = production_round(translated, translated_c, .04, noise, True, shifts, A, ALPHA, U)
        max_x = max(max_x, close(b[0], a[0]))
        max_c = max(max_c, close(b[1], a[1] - shifts))
        max_local = max(max_local, close(b[2], a[2]), close(b[3], a[3]))
        homogeneous, c = a[:2]
        translated, translated_c = b[:2]
    # Zero-sum affine gradients also cancel in one FedAvg local step.
    a = production_round(x, controls, .04, eps[:1], False, np.zeros_like(shifts), A, ALPHA, U)
    b = production_round(x, controls, .04, eps[:1], False, shifts, A, ALPHA, U)
    return {"scaffold_server": max_x, "scaffold_controls": max_c,
            "scaffold_local": max_local, "fedavg_H1_server": close(b[0], a[0])}


def orthogonal_equivariance():
    from stationary_bias.workstreams.p2_multidimensional_validation.objective import controlled_objective, RankOneVectorObjective
    from stationary_bias.workstreams.p2_multidimensional_validation.algorithm import scaffold_round_many_vector
    from stationary_bias.workstreams.p3_multidimensional_fedavg_attribution.algorithm import fedavg_round_many_vector
    from stationary_bias.workstreams.p2_multidimensional_validation.theory import vector_theory_targets
    from study.kernels import production_round
    objective = controlled_objective()
    Q = np.array([[np.sqrt(3) / 2, -.5], [.5, np.sqrt(3) / 2]])
    rotated = RankOneVectorObjective(Q @ objective.A @ Q.T, Q @ objective.u, objective.alpha)
    x, controls, eps = fixture()
    errors = {"orthogonality": close(Q @ Q.T, np.eye(2))}
    for scaffold in (False, True):
        kwargs = dict(gamma=.04, H=3)
        if scaffold:
            a = scaffold_round_many_vector(x[None], controls[None], objective=objective, epsilon_steps=eps[None], **kwargs)
            b = scaffold_round_many_vector((Q @ x)[None], (controls @ Q.T)[None], objective=rotated,
                                            epsilon_steps=(eps @ Q.T)[None], **kwargs)
            close(b.xi_new, a.xi_new @ Q.T)
        else:
            a = fedavg_round_many_vector(x[None], objective=objective, epsilon_steps=eps[None], **kwargs)
            b = fedavg_round_many_vector((Q @ x)[None], objective=rotated, epsilon_steps=(eps @ Q.T)[None], **kwargs)
        label = "scaffold" if scaffold else "fedavg"
        errors[label] = max(close(b.x_new, a.x_new @ Q.T), close(b.theta_final, a.theta_final @ Q.T),
                            close(b.qbar, a.qbar @ Q.T))
        ca = production_round(x, controls, .04, eps, scaffold, np.zeros_like(controls), objective.A, objective.alpha, objective.u)
        cb = production_round(Q @ x, controls @ Q.T, .04, eps @ Q.T, scaffold, np.zeros_like(controls), rotated.A, rotated.alpha, rotated.u)
        errors[label + "_compiled"] = max(close(bv, av @ Q.T) for av, bv in zip(ca, cb))
    C = np.array([[1., .3], [.3, .7]])
    a = vector_theory_targets(objective, C, 4)
    b = vector_theory_targets(rotated, Q @ C @ Q.T, 4)
    errors["lyapunov_rotation"] = close(b.S_C, Q @ a.S_C @ Q.T)
    for name in ("B11_d", "B20", "B20_local", "B20_ctrl"):
        errors[name] = close(getattr(b, name), Q @ getattr(a, name))
    return errors


def finite_window_and_resume():
    model, kernels = targeted_modules()
    x, controls, _ = fixture(H=4)
    states = np.stack([x, x + [.03, -.02]])
    gamma, H, N, rounds = 1 / 64, 4, 3, 17
    weights, B, PH = model.operators(gamma, H)
    errors = {}
    for asymmetric in (False, True):
        args = (N, H, gamma, weights, B, PH, -.25, asymmetric)
        whole = kernels.trigonometric_chunk(states.copy(), controls.copy(), np.uint64(991), 0, rounds, *args)
        first = kernels.trigonometric_chunk(states.copy(), controls.copy(), np.uint64(991), 0, 6, *args)
        second = kernels.trigonometric_chunk(first[0], first[1], np.uint64(991), 6, rounds - 6, *args)
        for i in (0, 1):
            np.testing.assert_array_equal(whole[i], second[i])
        for i in range(2, 7):
            np.testing.assert_array_equal(whole[i], np.concatenate([first[i], second[i]]))
        new, _, raw, bal, eta, residual, ctrlmean = whole
        endpoint = (new - states) / rounds
        pre = np.concatenate([states[None], raw[:-1]])
        pre_identity = B * (pre.mean(axis=0) - bal.mean(axis=0)) - eta.mean(axis=0) + endpoint - residual.mean(axis=0)
        post_identity = B * (raw.mean(axis=0) - bal.mean(axis=0)) - eta.mean(axis=0) + PH * endpoint - residual.mean(axis=0)
        paired = B * (raw[:, 0].mean(axis=0) - raw[:, 1].mean(axis=0) - bal[:, 0].mean(axis=0) + bal[:, 1].mean(axis=0))
        paired += PH * (endpoint[0] - endpoint[1]) - residual[:, 0].mean(axis=0) + residual[:, 1].mean(axis=0)
        if np.max(np.abs(endpoint)) < 1e-5:
            raise AssertionError("Endpoint correction must be non-vacuous in this fixture")
        errors["asymmetric" if asymmetric else "symmetric"] = {
            "pre_identity": close(pre_identity, np.zeros((2, 2)), atol=2e-15),
            "post_identity": close(post_identity, np.zeros((2, 2)), atol=2e-15),
            "paired_identity": close(paired, np.zeros(2), atol=2e-15),
            "round_residual": close(residual, np.zeros_like(residual), atol=2e-15),
            "mean_controls": close(ctrlmean, np.zeros_like(ctrlmean), atol=2e-15),
            "endpoint_maximum": float(np.max(np.abs(endpoint))), "resume_bitwise_exact": True,
        }
    return errors


CASES = {
    "scalar_update_arithmetic": scalar_update_arithmetic,
    "vector_and_compiled_arithmetic": vector_and_compiled_arithmetic,
    "targeted_reference_and_controls": targeted_reference_and_controls,
    "deterministic_and_quadratic_boundaries": deterministic_and_quadratic_boundaries,
    "exact_noise_moments_and_indexing": exact_noise_moments_and_indexing,
    "tensor_lyapunov_and_formulas": tensor_lyapunov_and_formulas,
    "affine_translation": affine_translation,
    "orthogonal_equivariance": orthogonal_equivariance,
    "finite_window_and_resume": finite_window_and_resume,
}


def run_checks():
    return {
        "schema_version": 1,
        "status": "PASS",
        "scope": "fixed tiny implementation examples; no stationary estimates, fitting, or production run",
        "limits": {"clients": 3, "coordinates": 2, "local_steps_max": 4, "rounds_per_call_max": 17},
        "noise_scope": "exact finite-support moments and indexed mapping; no claim of PRNG independence from this check",
        "checks": {name: check() for name, check in CASES.items()},
    }
