# Independent model and noise certificate

Status: **PASS_INDEPENDENT_MODEL_AND_EXACT_NOISE_CHECKS**. This is an analytical
and implementation certificate for the proposed construction; it is not a
stationarity certificate, a reproof of the manuscript's coefficient theorem, or
evidence that simulation confidence intervals attain a target.

The source for the derivation is the scalar objective itself. The independent
checker differentiates it with SymPy, solves the Lyapunov equation as a symbolic
linear system, contracts the resulting third derivative tensor, and enumerates
the exact noise supports with rational probabilities. Only after these
calculations does it import the supplied reference and compare its output. The
coefficient definitions are checked against the current local
`manuscript/sections/04_main_results.tex`; the reference's `theory()` routine is
not used to derive them.

## Fixed objective and derivatives

Write alpha = 1/20, A = diag(1,2), and

\[
f(x)=\tfrac12(x_1^2+2x_2^2)+\alpha\{-4(\sin x_1-x_1)
+\sin(x_1+x_2)-(x_1+x_2)+\sin(x_1-x_2)-(x_1-x_2)\}.
\]

Direct differentiation gives

\[
q(x)=\nabla f(x)-Ax=
\begin{pmatrix}
2\alpha[1-2\cos x_1+\cos x_1\cos x_2]\\
-2\alpha\sin x_1\sin x_2
\end{pmatrix},
\]

\[
\nabla^2 f(x)=\begin{pmatrix}
1+2\alpha\sin x_1(2-\cos x_2)&-2\alpha\cos x_1\sin x_2\\
-2\alpha\cos x_1\sin x_2&2-2\alpha\sin x_1\cos x_2
\end{pmatrix}.
\]

Therefore grad f(0)=0 and Hess f(0)=A. At the origin the only nonzero third
derivatives are T111=1/10 and T122=T212=T221=-1/10. In particular T is nonzero
(its Frobenius norm is 1/5), so the objective is nonquadratic. It is not
centrally even: f(pi/2,0)-f(-pi/2,0)=(pi-2)/10 is nonzero.

The perturbation has ridge vectors e1, (1,1), (1,-1) and coefficients -4,1,1.
For a ridge with vector v, the order-j derivative tensor has operator norm at
most ||v||^j, because each sine/cosine derivative is bounded by one. Thus

\[
\|\nabla^2 f(x)-A\|\le\alpha(4+2\cdot2)=2/5,
\qquad (3/5)I\preceq\nabla^2f(x)\preceq(12/5)I.
\]

This bound holds for every x; it is not inferred from a finite Hessian grid.
Global strong convexity and grad f(0)=0 establish the unique minimizer x*=0.
The function is C-infinity, and valid tensor bounds for orders 3,4,5 are
respectively (1+sqrt(2))/5, 3/5, and (1+2sqrt(2))/5, approximately 0.482842713,
0.6, and 0.765685425. The objective and these constants are fixed across all
N, gamma, H, covariance and noise-law conditions.

**Regularity clarification.** The brief's phrase “bounded derivatives through
order 5” is interpreted as bounded Hessian and bounded orders 3–5, exactly as
stated in the local manuscript's regularity assumptions. A globally strongly
convex objective on R² cannot also have a globally bounded gradient:
<grad f(x),x> >= mu||x||² implies ||grad f(x)|| >= mu||x||. Neither the gradient
nor the objective value is claimed bounded here.

## Independent contraction and coefficient calculation

For a symmetric M,

\[
T[M]=(2\alpha(M_{11}-M_{22}),-4\alpha M_{12})^T.
\]

For C_rho=diag(1+rho,1-rho), all three proposed covariances have trace 2 and
minimum eigenvalue at least 3/4. Solving AS+SA=C entry by entry gives
S=diag((1+rho)/2,(1-rho)/4), uniquely because A is positive definite. Hence

\[
T[C]=(4\alpha\rho,0),\quad
T[S]=(\alpha(1+3\rho)/2,0),\quad
B_{11}=(-\alpha(1+3\rho)/4,0).
\]

At H=4 the manuscript coefficient multipliers of -A^(-1)T[C] are 19/16
(SCAFFOLD), 3/4 (FedAvg), and 7/16 (control increment). Their independently
calculated coordinate-1 targets are:

| rho | B11 | B20 SCAFFOLD | B20 FedAvg | B20 control |
| --- | ---: | ---: | ---: | ---: |
| -1/4 | -0.003125 | +0.059375 | +0.037500 | +0.021875 |
| 0 | -0.012500 | 0 | 0 | 0 |
| +1/4 | -0.021875 | -0.059375 | -0.037500 | -0.021875 |

Every coordinate-2 target is zero and is retained in the machine-readable
output. The two non-null cases have opposite signs without any fitting
constraint. The null is nontrivial: T != 0, C0=I is full rank, T[C0]=0, but
B11=(-1/80,0) is nonzero. The predicted zero concerns the normalized residual
or matched SCAFFOLD–FedAvg difference, not the unadjusted global mean.

With these conservative mu,L and H=4,
gamma_imp=min(1,1/(48L),1/(24H(L+mu)))=1/288. All three candidate steps
1/512,1/1024,1/2048 are below it. **This does not certify the complete gamma0
used by all theorem absorption steps.**

## Exact covariance matching and higher moments

The scalar laws and moments are independently calculated with exact arithmetic:

| Law | Support and probabilities | E z | E z² | E z³ | E z⁴ | E z⁵ | E z⁶ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Symmetric | -1,+1, each 1/2 | 0 | 1 | 0 | 1 | 0 | 1 |
| Asymmetric | sqrt(2) with 1/3; -1/sqrt(2) with 2/3 | 0 | 1 | 1/sqrt(2) | 3/2 | 5sqrt(2)/4 | 11/4 |

Enumerating all four Cartesian support points with product probabilities and
applying diag(sqrt(1+rho),sqrt(1-rho)) verifies vector mean zero and covariance
C_rho exactly. The laws therefore have identical covariance at rho=+1/4 but
different third and fourth moments. The symmetric vector norm is sqrt(2);
the asymmetric vector norm is at most 2 for every proposed rho. The brief's
common bound sqrt(5) is valid, though conservative.

Exact marginal matching does not mean a finite batch has zero empirical mean
or exact empirical covariance. No sample recentering, whitening or rescaling
is warranted. Fresh-block independence is a property of the generator and
indexing scheme; moments or empirical correlation alone cannot establish it.
The production-path test must separately verify fresh draws across clients,
steps and rounds and reuse the same indexed arrays only for the matched
algorithm pair. Cross-law differences retain a possible O(gamma²/N) term as
well as O(gamma³); after division by gamma², the remainder is O(1/N+gamma).

## Numerical verification and a retained cancellation diagnostic

The supplied `null_model_reference.py` was actually executed in a subprocess;
its full stdout is `attachment_reference_stdout.json`. Independently derived
targets agree with that output and `ANALYTICAL_TARGETS_CHECKED.json` to maximum
absolute difference 1.39e-17. On 404 fixed, independently generated points,
the supplied gradient and Hessian agree with symbolic derivatives to maxima
2.85e-14 and 8.89e-16 respectively. The maximum scalar-objective difference
is 3.64e-12 at points with coordinates reaching magnitude 100 (ordinary
floating-point operation-order differences).

An additional 18 near-origin points use 80-digit symbolic derivatives. The
supplied q1 expression avoids subtracting cosines, but along x1=x2 its two
quadratic terms still cancel to leave a quartic result. An initial 3e-15
relative-only comparison at x=(0.01,0.01) failed: the absolute difference was
2.60e-22, or 1.04e-12 relative to q1. This diagnostic is preserved in
`validation_history.json`. It is within roundoff on the quadratic operands;
it is not a model or coefficient discrepancy. All 18 checks pass with a
documented absolute bound 64*machine_epsilon*alpha*(x1²+x2²).

For the new independent path an algebraically identical form also preserves
the diagonal quartic term:

\[
q_1(x)=4\alpha\{\sin((x_1+x_2)/2)\sin((x_1-x_2)/2)
+2\sin^2(x_1/2)\sin^2(x_2/2)\}.
\]

SymPy verifies exact equivalence, and this form passes the original 3e-15
relative criterion at all 18 points. The independent script does not modify
the supplied reference. No coefficient estimate or target inclusion was
consulted when diagnosing arithmetic or selecting this equivalent formula.

## Reproduction and scope

From the repository root, the tested command is:

```powershell
& 'python' targeted_closure_20261014\certificate\independent_model_checks.py
```

Runtime: Python 3.12.10, NumPy 2.4.6, SymPy 1.14.0. No dependency was installed.
`independent_model_checks.json` records exact formulas, exact and floating
targets, exact support/probability enumeration, every near-zero check,
environment details and SHA-256 hashes. It is regenerated by that command.

## Independent review of the new compiled path

Status: **PASS_INDEPENDENT_KERNEL_CHECKS** for the source hash recorded in
`independent_kernel_checks.json`. `independent_kernel_checks.py` imports only
`targeted.kernels`; it does not import the model/reference module, existing
tests, or any target coefficients. It separately evaluates the scalar
objective's derivative and follows the original endpoint/control recursions.
Weights are constructed by repeated multiplication with (1-gamma,1-2gamma),
and the balance is recovered by a separate linear solve.

The compiled path uses the trigonometric q with A=diag(1,2). It calls
`q_compiled` inside the client/local-step loop and regenerates the weights
from this A; no historical `controlled_chunk` is called and no target value
enters a trajectory. The supplied two-squared-sines q1 is retained, with its
diagonal cancellation interpreted using the absolute bounds above.

The new control update is algebraically equivalent to the manuscript's update.
Let G_c=sum_h[grad f(theta_c,h)+epsilon_c,h+1], omitting the controls from G.
The original endpoint relation is theta_c,H=x-gamma(G_c+H xi_c), so

\[
\xi_c^+=\xi_c+\frac{\theta_{c,H}-\bar\theta_H}{\gamma H}
=\bar\xi+\frac{\bar G-G_c}{H}.
\]

The explicit old mean bar(xi) is retained. Thus the rewrite preserves a
nonzero incoming control mean and is not a projection onto zero sum. For a
nonzero mean the ideal zero-sum one-round recursion has an extra term
-gamma(sum_h P^(H-1-h))bar(xi), which the independent checker also verifies.
The numerical residual stored by the kernel includes this term and arithmetic
error; it must accompany finite-window identity checks.

Executed independent checks:

- 95 complete explicit-noise rounds in five cases spanning H=1/4, N=3/7/11,
  three candidate step sizes, alpha=0/.05, and zero/nonzero control means.
  Maximum state difference from the original scalar recursion: 1.12e-16;
  controls: 1.14e-13; balance: 2.43e-17. The larger control comparison reflects
  division of endpoint subtraction error by gamma H in the original formula.
- 120 arbitrary nonzero gradient points: maximum discrepancy 4.45e-16.
- 31 H=1 rounds with coincident algorithm starts: global states are equal
  bit for bit. Twenty-seven deterministic rounds also preserve identical
  states and zero controls within recorded tolerances.
- Explicit alpha=0 cases give exactly zero balance. Nonzero control means
  are preserved, with maximum drift 4.45e-16 across the cases.
- Both noise laws: reconstruct 79 rounds from their explicit indexed noise
  arrays using the independent scalar recursion. Maximum trajectory
  discrepancy is 9.25e-15. Save/reload at round 29 and continue: final state,
  controls and every recorded observable are bitwise identical to the
  uninterrupted run. Small test checkpoint files are retained.
- Both noise laws, arbitrary nonstationary starts: the pre-round,
  post-round and paired post-round finite-window identities all pass when
  endpoints and accumulated recursion residuals are retained. The maximum
  absolute residual across these checks is 1.94e-18.

The deterministic indexed generator uses round/step/client-coordinate indices;
the two algorithms receive the same explicit noise array within each round.
The asymmetric transform excludes the single 64-bit residue that would bias
a three-way modulo map, then applies the prescribed support. Exact law
moments are checked above. Like any keyed pseudorandom simulation, fresh
independence remains a PRNG modeling assumption, not a mathematical
independence certificate established by a finite test or by the moments.

The tested reproduction command for the compiled checker is:

```powershell
$env:PYTHONPATH='./supplementary_study/.deps'
& 'python' targeted_closure_20261014\certificate\independent_kernel_checks.py
```

Runtime: bundled Python 3.12.14, NumPy 2.5.3, Numba 0.68.0. Passing these
identities establishes recursion/timing consistency. It does not establish
stationarity, validate a finite-grid intercept, or prove an asymptotic
coefficient theorem.
