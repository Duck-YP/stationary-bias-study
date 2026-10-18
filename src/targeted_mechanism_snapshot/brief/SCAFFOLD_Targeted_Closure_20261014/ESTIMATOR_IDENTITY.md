# Finite-window direct/balance identity for paired runs

This algebraic check uses the current manuscript's exact additive-noise recursions. It does not require stationarity, and it does not assume the B20 formula. It is proposed here as an implementation diagnostic, not as a new empirical result or theorem claim in the manuscript.

Fix P=I-gamma A and B=I-P^H. With zero-sum controls (or no controls), write one round as

x_(t+1)=P^H x_t + eta_t - gamma s_t,

eta_t=-gamma sum_(j=1)^H P^(H-j) epsilon_bar_(t,j),
s_t=sum_(h=0)^(H-1) P^(H-1-h) q_bar_(t,h),
q(y)=grad f(y)-Ay.

The balance observable is z_t=-gamma B^(-1)s_t. Use linear solves, not explicit inversion.

For a window of T rounds t=s,...,s+T-1,

B (mean_pre(x)-mean(z))
  = mean(eta) - (x_(s+T)-x_s)/T.

If the stored direct observations are POST-round states, mean_post(x), the corresponding identity is

B (mean_post(x)-mean(z))
  = mean(eta) - P^H (x_(s+T)-x_s)/T.

These formulas must not be mixed. The previous production kernel stores post-round global states.

## Matched SCAFFOLD-FedAvg case

For identical indexed noises and the same A, eta_t is identical in the two algorithms. Let d_t=x_t^S-x_t^F. It cancels in the paired identity:

B (mean_pre(d)-mean(z^S-z^F)) = -(d_(s+T)-d_s)/T,

or, for POST-round direct observations,

B (mean_post(d)-mean(z^S-z^F)) = -P^H (d_(s+T)-d_s)/T.

Thus direct and balance estimates of the matched mean difference need not agree exactly on a finite window; the endpoint term must be included. New runs should store window endpoints and both observables, allowing this identity to be tested without another simulation.

## Interpretation

- Check the algebra first using a scalar/reference implementation and explicit noise arrays, then in the compiled implementation.
- In floating-point execution, record the accumulated round-recursion residual and control-sum residual; account for these in the numerical tolerance. Do not project controls or silently alter the old outputs to force agreement.
- For historical runs, evaluate this only if the same-window pre/post convention and endpoints are available. Otherwise mark it NOT_RECONSTRUCTIBLE_FROM_AVAILABLE_OUTPUTS.
- Equality of these observables after the endpoint correction checks implementation and alignment. It does not establish stationarity, validate B20, quantify an asymptotic remainder constant, or explain the historical fitted-intercept discrepancy by itself.
- For unpaired or different-noise-law comparisons, the eta terms do not generally cancel. Retain them or perform ordinary paired/covariance-aware statistical comparison.
