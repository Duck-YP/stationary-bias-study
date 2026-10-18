# Nontrivial zero-coefficient design (proposed; no simulations yet)

This is a new analytical construction for the proposed follow-up. It is not a recovered result from the existing experiment archive. Symbolic gradient/Hessian identities, origin derivatives, coefficient arithmetic and exact discrete noise moments have been checked. No stationary chains have been run here. Codex must independently check the construction and implement it separately from the old controlled objective.

## 1. Objective

Fix alpha = 1/20 and A = diag(1,2). For x=(x1,x2), define

f(x) = (x1^2 + 2 x2^2)/2 + alpha g(x),

g(x) = -4(sin(x1)-x1)
       + (sin(x1+x2)-(x1+x2))
       + (sin(x1-x2)-(x1-x2)).

This is nonquadratic and not centrally even. The objective does not change with gamma, N, H or noise law.

The perturbation is a sum of three ridge functions with vectors e1, (1,1), (1,-1) and weights -4,1,1. Therefore

||Hess g(x)|| <= 4 ||e1||^2 + ||(1,1)||^2 + ||(1,-1)||^2 = 8

for every x. Consequently

0.6 I <= Hess f(x) <= 2.4 I.

Also grad f(0)=0 and Hess f(0)=A, so the unique minimizer is zero. All derivatives of orders 3,4,5 are globally bounded; a valid order-j bound is alpha[4+2*2^(j/2)]. This is an analytical global bound, not a grid-based certificate.

The nonzero third derivatives at zero are

T111=2 alpha, T122=T212=T221=-2 alpha.

In particular T != 0. For symmetric M,

T[M] = (2 alpha (M11-M22), -4 alpha M12).

For a stable implementation of q(x)=grad f(x)-Ax, use

q1=4 alpha [sin^2(x1/2)-cos(x1) sin^2(x2/2)],
q2=-2 alpha sin(x1) sin(x2).

Independently compare this implementation to derivatives of the objective. Do not obtain q by evaluating a coefficient target or forcing its sample mean to have any value.

## 2. Covariance intervention, including a nontrivial null

Let rho be -1/4, 0 or +1/4, and take

C_rho=diag(1+rho,1-rho).

All three covariances are positive definite and have trace 2. Their Lyapunov solutions are

S_rho=diag((1+rho)/2,(1-rho)/4).

It follows that

T[C_rho]=(4 alpha rho,0),
T[S_rho]=(alpha(1+3rho)/2,0),
B11(rho)=(-alpha(1+3rho)/4,0).

Thus at rho=0, T is nonzero, C=I is full rank, T[C]=0, but B11=(-0.0125,0) is NONZERO. A zero raw global mean is NOT the prediction. The test concerns the coefficient after removing the shared gamma/N contribution, or the matched algorithm difference.

At H=4:

| rho | B11, coord. 1 | B20 SCAFFOLD, coord. 1 | B20 FedAvg, coord. 1 | B20 control, coord. 1 |
| --- | --- | --- | --- | --- |
| -1/4 | -0.003125 | +0.059375 | +0.0375 | +0.021875 |
| 0 | -0.0125 | 0 | 0 | 0 |
| +1/4 | -0.021875 | -0.059375 | -0.0375 | -0.021875 |

The second coordinate of these resolved targets is zero. Retain it in all numerical outputs. The two non-null covariance cases are positive/signed controls: they test whether the procedure can recover nearby nonzero coefficients of opposite sign rather than returning zero for everything.

For these conservative objective constants and H=4,

gamma_imp = min(1,1/(48L),1/[24H(L+mu)]) = 1/288.

The candidate grid gamma in {1/512,1/1024,1/2048} lies below this imported threshold. This does NOT certify the complete gamma0 used by every proof absorption step; that distinction must remain explicit in the report.

## 3. Two bounded noise laws

Generate independent coordinates of z, independently across clients, local steps and rounds. Set epsilon=C_rho^(1/2) z, with the fixed analytical diagonal square root.

Symmetric law: z=+1 or -1, each with probability 1/2.

Asymmetric law: z=sqrt(2) with probability 1/3, and z=-1/sqrt(2) with probability 2/3.

Both have E[z]=0 and E[z^2]=1. Their third moments are 0 and 1/sqrt(2), and fourth moments are 1 and 3/2. Thus the transformed noises have identical covariance for fixed rho but different higher moments. A common almost-sure vector bound for all proposed cases is sqrt(5).

Use the symmetric law for rho=-1/4,0,+1/4. Add the asymmetric law only for rho=+1/4. This makes four conditions, not a large distribution benchmark. Within each condition, SCAFFOLD and FedAvg must receive the same indexed noise realizations. Cross-law coupling is optional but must preserve each law's exact marginal distribution and fresh-block independence.

Do not empirically recenter, renormalize or whiten each generated batch: that would change the oracle and introduce dependencies.

## 4. What is and is not predicted

For the null case:

[b^A-(gamma/N) B11]/gamma^2 = O_H,d(1/N+gamma),

and (b^S-b^F)/gamma^2 = O_H,d(1/N+gamma).

For two noise laws nu1, nu2 at fixed C:

b^(A,nu1)-b^(A,nu2)=O_H,d(gamma^2/N+gamma^3).

Do not drop gamma^2/N at finite N, and do not require equality of finite-step stationary means. Zero inclusion by a wide interval is not evidence of zero coefficient or invariance. These are targeted numerical diagnostics, not proofs of the theorem.
