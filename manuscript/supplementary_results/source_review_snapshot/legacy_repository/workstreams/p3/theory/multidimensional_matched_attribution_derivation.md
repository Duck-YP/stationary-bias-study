# Multidimensional matched FedAvg attribution derivation

## 1. Main expansion

For fixed dimension $d$, fixed $H\geq2$, and sufficiently small $\gamma$, the stationary FedAvg mean satisfies

$$
b_{\mathrm{FA}}^{(d)}(\gamma,N,H)
=-\frac{\gamma}{2N}A^{-1}T[S_C]
-\gamma^2\frac{H-1}{4}A^{-1}T[C]
+O_{H,d}\!\left(\frac{\gamma^2}{N}+\gamma^3\right),
\qquad AS_C+S_CA=C.
$$

The client-independent coefficient is

$$
B_{20,\mathrm{FA}}^{(d)}(H)
=B_{20,\mathrm{local}}^{(d)}(H)
=-\frac{H-1}{4}A^{-1}T[C].
$$

The leading coefficient retains the established `B11_d` notation

$$
B_{11,d}=-\frac12A^{-1}T[S_C].
$$

With the corresponding multidimensional SCAFFOLD coefficient,

$$
B_{20,\mathrm{SCAF}}^{(d)}(H)-B_{20,\mathrm{FA}}^{(d)}(H)
=B_{20,\mathrm{ctrl}}^{(d)}(H)
=-\frac{(H-1)(2H-1)}{12H}A^{-1}T[C].
$$

The derivation starts from the exact FedAvg recursion. Its scalar specialization is used only as an algebraic consistency check.

## 2. Assumptions and notation

Fix $d\geq1$, $H\geq2$, and $N\geq2$. Participation is full, clients are homogeneous, and the common minimizer is translated to zero. The objective $f:\mathbb R^d\to\mathbb R$ is $C^5$,

$$
\mu I\preceq \nabla^2f(y)\preceq LI
\quad\text{for every }y,
$$

and $\nabla^3f,\nabla^4f,\nabla^5f$ are uniformly bounded. Set

$$
A=\nabla^2f(0)=A^\top\succ0,
\qquad T=\nabla^3f(0).
$$

The oracle is

$$
\nabla F_{t,c,h}(y)=\nabla f(y)+\epsilon_{t,c,h}.
$$

Every vector block $\epsilon_{t,c,h}$ is centered, almost surely bounded, independent of the round-start state, and fresh across rounds, clients, and local steps, with common covariance

$$
\mathbb E[\epsilon\epsilon^\top]=C\succeq0.
$$

Coordinates inside one block may be correlated. Noise symmetry and $AC=CA$ are not assumed. The exact recursion is

$$
\theta_{t,c,0}=x_t,
\qquad
\theta_{t,c,h+1}=\theta_{t,c,h}
-\gamma\{\nabla f(\theta_{t,c,h})+\epsilon_{t,c,h+1}\},
\qquad
x_{t+1}=\frac1N\sum_{c=1}^N\theta_{t,c,H}.
$$

Only $0<\gamma\leq\gamma_0$ is considered, where $\gamma_0$ depends on the fixed regularity constants and makes the gradient steps contractive. The stationary law is the unique law induced by this contractive random recursion.

The Lyapunov solution $S_C$ is the unique symmetric matrix satisfying $AS_C+S_CA=C$. Scale abbreviations are

$$
s_{\gamma,N}=\frac\gamma N+\gamma^2,
\qquad
r_{\gamma,N}=\frac{\gamma^2}{N}+\gamma^3=\gamma s_{\gamma,N},
\qquad
v_{\gamma,N}=\frac{\gamma^2}{N^2}+\gamma^3.
$$

At stationarity, with a generic round-start state $x$, define

$$
b=\mathbb E x,
\qquad M_x=\mathbb E[xx^\top],
\qquad
m_h=\frac1N\sum_c\mathbb E\theta_{c,h},
$$

$$
M_h=\frac1N\sum_c\mathbb E[\theta_{c,h}\theta_{c,h}^\top],
\qquad U_h=M_h-M_x.
$$

The matrices $M_x$ and $M_h$ are raw second moments, not centered covariances. Tensor contraction is denoted by $T[M]$, with component $(T[M])_i=\sum_{j,k}T_{ijk}M_{jk}$. All matrix and tensor norms are fixed finite-dimensional compatible norms. Constants $C_{H,d}$ may depend on fixed $H,d$ and the objective/noise bounds, but never on $N$ or $\gamma$.

## 3. Dependency order

The non-circular proof order is

```text
stationary foundation / coarse moments
    -> finite-step displacement
    -> coarse global second moment + mean bootstrap
    -> nonlinear increment moments
    -> sharp global fourth moment
    -> signed global third tensor
    -> client-averaged displacement
    -> nonlinear second-moment terms
    -> sharp global second moment
    -> local signed third tensor / Taylor tail
    -> coefficient assembly
```

In particular, the sharp global second-moment formula is unavailable when the sharp fourth moment and signed third tensor are established. Those two results are later inputs to the nonlinear forcing estimate needed for the sharp second moment. Reversing either arrow would be circular.

The stationary fourth/sixth-moment interface is verified in Paul Mangold, Alain Oliviero Durmus, Aymeric Dieuleveut, Sergey Samsonov, and Eric Moulines, "Refined Analysis of Constant Step Size Federated Averaging and Federated Richardson-Romberg Extrapolation," AISTATS 2025, PMLR 258:5023--5031, arXiv:2412.01389v2, Lemma 8. Lemma 8's proof refers back to Lemma 6, but the imported stationary-moment result is Lemma 8, not Lemma 6.

Under A1, A2, A3, $\gamma\leq1/(45L)$, and $\gamma\mu H\leq1$, Lemma 8 states for $p\in\{2,3\}$ that the stationary global parameter satisfies

$$
\mathbb E\|\theta-\theta_\star\|^{2p}
=O\!\left(\gamma^p+\gamma^{2p}H^{2p}\right),
$$

with the corresponding fixed-$h$ local FedAvg iterate having the same order. In the present notation, the stationary global parameter is $x$, $\theta_\star=0$, and the local iterates are $\theta_{c,h}$. Therefore, for fixed $H$,

$$
\mathbb E\|x\|^4=O_{H,d}(\gamma^2),
\qquad
\mathbb E\|x\|^6=O_{H,d}(\gamma^3),
$$

with corresponding fixed-$h$ local fourth/sixth-moment bounds.

The assumptions specialize as follows.

- **A1:** $F_\epsilon(y)=f(y)+\langle\epsilon,y\rangle$ has the same Hessian as $f$, so convexity and smoothness are inherited.
- **A2:** Homogeneous clients give zero client heterogeneity.
- **A3:** Bounded additive noise has finite second, fourth, and sixth moments; state independence supplies the required moment envelope.
- **Step size:** $\gamma\leq1/(45L)$ and $\gamma\mu H\leq1$ are absorbed into the final fixed-$H$ small-step threshold $\gamma_{0,H,d}$.

As an internal consistency check on the imported interface, let $K$ be the
almost-sure noise bound.  For sufficiently small $\gamma$, the deterministic
gradient map $G_\gamma(y)=y-\gamma\nabla f(y)$ satisfies

$$
\|G_\gamma(x)-G_\gamma(y)\|
\leq\rho_\gamma\|x-y\|,
\qquad
\rho_\gamma\leq1-c\gamma,
$$

where $c>0$ depends only on the fixed Hessian bounds.  Since
$G_\gamma(0)=0$, every local step obeys

$$
\|\theta_{c,h+1}\|
\leq\rho_\gamma\|\theta_{c,h}\|+\gamma K.
$$

Iteration gives

$$
\|\theta_{c,h}\|
\leq\rho_\gamma^h\|x\|
+\gamma K\sum_{j=0}^{h-1}\rho_\gamma^j
\leq\rho_\gamma^h\|x\|
+\frac Kc(1-\rho_\gamma^h).
$$

Thus the closed ball of radius $R=K/c$ is invariant under every local map
and under their client average.  Starting the contractive random recursion at
zero keeps every iterate in that ball; convergence to the unique stationary
law therefore proves

$$
\boxed{\|x\|\leq R\quad\pi_{\gamma,N}\text{-a.s.}}
$$

with the same bound for every fixed local iterate.  The radius is independent
of $N$ and $\gamma$.  In particular, for every $m\geq0$,
$\mathbb E\|x\|^{m+2}\leq R^2\mathbb E\|x\|^m$, and likewise locally.

Expanding the exact one-round even-power drift, centering every fresh block
before applying Young's inequality, gives for $k=1,2,3$

$$
\mathbb E[\|x^+\|^{2k}\mid x]
\leq(1-c_k\gamma)\|x\|^{2k}
+C_k\gamma^2\|x\|^{2k-2}
+C_k\gamma^{k+1}.
$$

For $k=1$, retaining client averaging instead of discarding it sharpens the additive term to $C(\gamma^2/N+\gamma^3)$. Stationarity and induction in $k$ therefore give

$$
\mathbb E\|x\|^2=O_{H,d}(s_{\gamma,N}),
\qquad
\mathbb E\|x\|^4=O_{H,d}(\gamma^2),
\qquad
\mathbb E\|x\|^6=O_{H,d}(\gamma^3).
$$

For each fixed $h\leq H$, the exact finite-step recursion and bounded fresh noise transfer the fourth/sixth bounds to $\theta_{c,h}$. The stationary mean equation and $\|\nabla f(y)-Ay\|\leq C\|y\|^2$ give $\|b\|=O_{H,d}(s_{\gamma,N})$. These estimates use no sharp covariance expansion and are consistent with the verified Lemma 8 interface.

## 4. Local raw second moment

For a fixed round and client, exact summation of the local recursion gives

$$
\theta_{c,h}=x+D_{c,h}+R_{c,h},
$$

$$
D_{c,h}=-\gamma\sum_{j=1}^h\epsilon_{c,j},
\qquad
R_{c,h}=-\gamma\sum_{\ell=0}^{h-1}\nabla f(\theta_{c,\ell}).
$$

### A1. xD terms

Let $\mathcal F_t$ contain the round-start state and all preceding rounds. Each $\epsilon_{t,c,j}$ is independent of $\mathcal F_t$ and centered, so

$$
\mathbb E[xD_{c,h}^\top]
=\mathbb E\!\left[x\,\mathbb E[D_{c,h}^\top\mid\mathcal F_t]\right]=0.
$$

Transposition gives $\mathbb E[D_{c,h}x^\top]=0$. Only block freshness and centering are used; within-block coordinate independence is unnecessary.

### A2. DD term

Expanding both sums,

$$
\mathbb E[D_{c,h}D_{c,h}^\top]
=\gamma^2\sum_{j,k=1}^h
\mathbb E[\epsilon_{c,j}\epsilon_{c,k}^\top].
$$

For $j\ne k$, freshness and centering make the expectation zero. The $h$ diagonal terms equal $C$, hence

$$
\boxed{\mathbb E[D_{c,h}D_{c,h}^\top]=\gamma^2hC.}
$$

There is no $1/N$ factor: this is one client's local raw moment, not the moment of a client average.

### A3. xR terms

The coarse global second moment and the fixed-step displacement bound give

$$
\sup_{c,\ell\leq H}\mathbb E\|\theta_{c,\ell}\|^2
=O_{H,d}(s_{\gamma,N}).
$$

Global $L$-smoothness and $\nabla f(0)=0$ imply

$$
\begin{aligned}
\left\|\frac1N\sum_c\mathbb E[xR_{c,h}^\top]\right\|
&\leq C_H\gamma
(\mathbb E\|x\|^2)^{1/2}
\sup_{c,\ell}(\mathbb E\|\theta_{c,\ell}\|^2)^{1/2}\\
&=O_{H,d}(\gamma s_{\gamma,N})
=O_{H,d}(r_{\gamma,N}).
\end{aligned}
$$

The same estimate holds for the transpose. The constant is uniform in $N,\gamma$.

### A4. DR terms

The separate estimates are

$$
\|D_{c,h}\|_{L^2}=O_H(\gamma),
\qquad
\|R_{c,h}\|_{L^2}=O_{H,d}(\gamma\sqrt{s_{\gamma,N}}).
$$

Thus Cauchy--Schwarz gives $O_{H,d}(\gamma^2\sqrt{s_{\gamma,N}})$, not merely an unspecified higher order. Put $t=1/N$. Since $\gamma\leq t+\gamma$,

$$
\sqrt{\gamma(t+\gamma)}\leq t+\gamma,
$$

and therefore

$$
\gamma^2\sqrt{s_{\gamma,N}}
=\gamma^2\sqrt{\gamma(t+\gamma)}
\leq\gamma^2(t+\gamma)
=\frac{\gamma^2}{N}+\gamma^3.
$$

Both $DR^\top$ and its transpose are uniformly $O_{H,d}(r_{\gamma,N})$.

### A5. RR terms

The preceding $L^2$ bound yields

$$
\|\mathbb E[R_{c,h}R_{c,h}^\top]\|
\leq\mathbb E\|R_{c,h}\|^2
=O_{H,d}(\gamma^2s_{\gamma,N}).
$$

For $\gamma\leq1$, $\gamma^2s_{\gamma,N}=\gamma^3/N+\gamma^4\leq r_{\gamma,N}$. No inverse power of $\gamma$ occurs.

### A6. Result

Combining the exact expansion and averaging over clients gives, uniformly for fixed $0\leq h\leq H$,

$$
\boxed{U_h^{\mathrm{FA}}=\gamma^2hC+O_{H,d}(r_{\gamma,N}).}
$$

## 5. Sharp global second moment

Set

$$
P=I-\gamma A,
\qquad q(y)=\nabla f(y)-Ay,
\qquad
\bar\epsilon_j=\frac1N\sum_c\epsilon_{c,j},
\qquad
\bar q_h=\frac1N\sum_cq(\theta_{c,h}).
$$

Iterating the linear part of the exact recursion gives the identity

$$
x^+=P^Hx+\eta+\Delta,
$$

$$
\eta=-\gamma\sum_{j=1}^HP^{H-j}\bar\epsilon_j,
\qquad
\Delta=-\gamma\sum_{h=0}^{H-1}P^{H-1-h}\bar q_h.
$$

### B1. Fresh-noise covariance

Freshness across clients and local steps gives

$$
\mathbb E[\bar\epsilon_j\bar\epsilon_k^\top]
=\mathbf{1}_{\{j=k\}}\frac CN.
$$

Consequently,

$$
\boxed{
\Sigma_\eta=\mathbb E[\eta\eta^\top]
=\frac{\gamma^2}{N}\sum_{k=0}^{H-1}P^kC(P^k)^\top.}
$$

For fixed $H,d$, blockwise Rosenthal expansion and boundedness give

$$
\mathbb E\|\eta\|^2=O(\gamma^2/N),
\quad
\mathbb E\|\eta\|^4=O_{H,d}(\gamma^4/N^2),
\quad
\mathbb E\|\eta\|^6=O_{H,d}(\gamma^6/N^3).
$$

The signed third tensor need not vanish. Only equal-block triples survive, so

$$
\|\mathbb E[\eta^{\otimes3}]\|
=O_{H,d}(NH(\gamma/N)^3)
=O_{H,d}(\gamma^3/N^2).
$$

This calculation uses centered independent vector blocks, not independent coordinates or symmetric noise.

### B2. High-moment prerequisite

The verified Lemma 8 interface and the assumption-specialization check in Section 3 supply

$$
\mathbb E\|x\|^4=O_{H,d}(\gamma^2),
\qquad
\mathbb E\|x\|^6=O_{H,d}(\gamma^3),
$$

and the corresponding fixed-$h$ local bounds.  The invariant-ball lemma in
Section 3 gives, without another moment assumption,

$$
\mathbb E\|x\|^8\leq R^2\mathbb E\|x\|^6=O(\gamma^3),
$$

and the same estimate locally. These are coarse bounds; the sharp fourth
bound is not asserted here.

The imported stationary global/local moment result is Mangold et al., Lemma 8. Its proof refers to Lemma 6, but the result used here is not relabeled as Lemma 6.

### B3. Delta moments

Taylor's theorem and the uniform third-derivative bound give

$$
\|q(y)\|\leq C\|y\|^2,
\qquad
\|q(y)\|\leq C\|y\|.
$$

For fixed $H$, Jensen's inequality and the local fourth moment give

$$
\mathbb E\|\Delta\|^2
\leq C_H\gamma^2\sup_{c,h}\mathbb E\|\theta_{c,h}\|^4
=O_{H,d}(\gamma^4).
$$

Uniform stationary support and the local sixth moment give

$$
\mathbb E\|\Delta\|^4
\leq C_H\gamma^4\sup_{c,h}\mathbb E\|\theta_{c,h}\|^8
\leq C_{H,d}\gamma^4\sup_{c,h}\mathbb E\|\theta_{c,h}\|^6
=O_{H,d}(\gamma^7).
$$

Both constants are uniform in $N,\gamma$.

### B4. Sharp global fourth moment

Put $u=P^Hx$ and $\phi(z)=\|z\|^4$.  The exact linear-noise expansion is

$$
\begin{aligned}
\phi(u+\eta)
={}&\|u\|^4+4\|u\|^2\langle u,\eta\rangle
+2\|u\|^2\|\eta\|^2+4\langle u,\eta\rangle^2\\
&+4\langle u,\eta\rangle\|\eta\|^2+\|\eta\|^4.
\end{aligned}
$$

The second term vanishes after expectation because $\eta$ is fresh and
centered.  Independence gives the following term-by-term ledger for the remaining
linear-noise terms:

| term | bound after expectation |
| --- | --- |
| $\|u\|^2\|\eta\|^2$ | $C(\gamma^2/N)\mathbb E\|x\|^2$ |
| $\langle u,\eta\rangle^2$ | $C(\gamma^2/N)\mathbb E\|x\|^2$ |
| $\langle u,\eta\rangle\|\eta\|^2$ | $C\|b\|\,\|\mathbb E[\eta\|\eta\|^2]\|=O(\gamma^3s_{\gamma,N}/N^2)$ |
| $\|\eta\|^4$ | $O(\gamma^4/N^2)$ |

The signed cubic-noise bound in the third row follows from the same equal-block
count as B1.  It does not require symmetric noise.

For the nonlinear part, Taylor's formula for the degree-four polynomial
$\phi$ gives exactly four classes, according to the number of $\Delta$
factors.  Substituting
$\Delta=-\gamma\sum_{h=0}^{H-1}P^{H-1-h}\bar q_h$, writing
$\theta_{c,h}=x+D_{c,h}+R_{c,h}$, and centering every $D$ block before taking
absolute values gives, for any fixed $\varepsilon>0$,

| class | term scale |
| --- | --- |
| one $\Delta$ | $\varepsilon\gamma\mathbb E\|x\|^4+C_\varepsilon(\gamma^2\mathbb E\|x\|^2/N+\gamma^4/N^2+\gamma^4)$ |
| two $\Delta$ factors | $C(\gamma^2\mathbb E\|x\|^4+\gamma^4/N^2+\gamma^4)$ |
| three $\Delta$ factors | $C(\gamma^4/N^2+\gamma^4)$ |
| four $\Delta$ factors | $O(\gamma^7)$ |

Here is the scale justification for each row.  In the one-$\Delta$ row, the
only term with three round-start factors is
$\gamma\mathbb E\|x\|^5$.  On $\{\|x\|\leq a\}$ it is at most
$\gamma a\mathbb E\|x\|^4$; on the complement it is at most
$\gamma a^{-1}\mathbb E\|x\|^6=O(\gamma^4)$.  Choose $a$ so that the first
piece is absorbed into the linear contraction.  Terms with one or more fresh
noise factors either vanish by centering or use B1 together with the coarse
second moment.  In the two-$\Delta$ row use B3 and
$\mathbb E\|x\|^4=O(\gamma^2)$ before sharpening; the last two rows follow
from $\mathbb E\|\Delta\|^2=O(\gamma^4)$,
$\mathbb E\|\Delta\|^4=O(\gamma^7)$, and uniform support.  These bounds cover
the mixed $\eta$-$\Delta$ terms as well as the pure $\Delta$ terms.

The linear contraction satisfies
$\mathbb E\|P^Hx\|^4\leq(1-c_4\gamma)\mathbb E\|x\|^4$.
After the preceding small-radius absorption, stationarity therefore yields

$$
c\gamma\mathbb E\|x\|^4
\leq C\left\{
\frac{\gamma^2}{N}\mathbb E\|x\|^2
+\frac{\gamma^4}{N^2}+\gamma^4
\right\}.
$$

Substitution of only the coarse sharp-scale bound $\mathbb E\|x\|^2=O(s_{\gamma,N})$ gives

$$
\boxed{
\mathbb E\|x\|^4
=O_{H,d}\!\left(\frac{\gamma^2}{N^2}+\gamma^3\right)
=O_{H,d}(v_{\gamma,N}).}
$$

The sharp second-moment expansion in B12 is not used.

### B5. Signed global third tensor

Define

$$
\mathcal T_3=\mathbb E[x^{\otimes3}].
$$

Stationarity and the exact representation give

$$
\{I-(P^H)^{\otimes3}\}\mathcal T_3=\mathcal R_3.
$$

The inverse operator is $O_H(1/\gamma)$: in an eigenbasis of $A$, every denominator is $1-\prod_{r=1}^3(1-\gamma a_{i_r})^H\geq c_H\gamma$. Write $L=P^Hx$.  The exact symmetric tensor expansion of
$(L+\eta+\Delta)^{\otimes3}$ gives the following forcing ledger:

| forcing term | bound | reason |
| --- | --- | --- |
| $\operatorname{Sym}(L^{\otimes2}\otimes\eta)$ | $0$ | fresh centering |
| $\operatorname{Sym}(L\otimes\eta^{\otimes2})$ | $O(\|b\|\gamma^2/N)$ | independence and $\mathbb E\eta^{\otimes2}=\Sigma_\eta$ |
| $\eta^{\otimes3}$ | $O(\gamma^3/N^2)$ | equal-block count from B1 |
| $\operatorname{Sym}(L^{\otimes2}\otimes\Delta)$ | $O(\gamma v_{\gamma,N})$ | $q(x)=\tfrac12T[x,x]+O(\|x\|^3)$ and B4 |
| $\operatorname{Sym}(L\otimes\eta\otimes\Delta)$ | $O(\gamma^4)$ | block centering and one-block replacement |
| $\operatorname{Sym}(\eta^{\otimes2}\otimes\Delta)$ | $O(\gamma^4/N)$ | B1 and B3 |
| $\operatorname{Sym}(L\otimes\Delta^{\otimes2})$ | $O(\gamma^4)$ | coarse second moment, B3, and uniform support |
| $\operatorname{Sym}(\eta\otimes\Delta^{\otimes2})$ | $O(\gamma^4)$ | B1, B3, and $\gamma\leq1$ |
| $\Delta^{\otimes3}$ | $O(\gamma^4)$ | B3 and uniform support |

For the one-block replacement row, replace the vector block appearing in
$\eta$ by zero.  The independent replacement term vanishes; the changed
$\Delta$ carries an additional $O(\gamma^2/N)$ factor and summing the $NH$
blocks gives the displayed bound.  The $L^{\otimes2}\Delta$ row is the only
one that needs the signed fourth-order drift: its leading part is
$\gamma\mathbb E[x^{\otimes4}]=O(\gamma v)$, while every displacement
remainder has the same or smaller scale by B3.  Thus no absolute
$\mathbb E\|x\|^3$ estimate is used.  Since
$\|b\|=O(s_{\gamma,N})$, the term-by-term ledger gives

$$
\|\mathcal R_3\|
\leq C_{H,d}\left(\frac{\gamma^3}{N^2}+\gamma^4\right)
=O_{H,d}(\gamma v_{\gamma,N}).
$$

Hence

$$
\boxed{\|\mathcal T_3\|=O_{H,d}(v_{\gamma,N})
\leq O_{H,d}(r_{\gamma,N}).}
$$

This is a signed tensor statement and does not assert an absolute third-moment bound at scale $r_{\gamma,N}$.

### B6. Client-averaged displacement

Define

$$
\bar\delta_h=\frac1N\sum_c(\theta_{c,h}-x).
$$

Exact summation gives a drift part of size $\gamma\sum_{\ell<h}N^{-1}\sum_c\nabla f(\theta_{c,\ell})$ and an averaged fresh-noise part $-\gamma\sum_{j\leq h}\bar\epsilon_j$. Centering and independence make the latter's second moment exactly $\gamma^2h\,\operatorname{tr}(C)/N$. Thus

$$
\boxed{
\mathbb E\|\bar\delta_h\|^2
=O_{H,d}\!\left(\frac{\gamma^2}{N}+\gamma^2s_{\gamma,N}\right).}
$$

The explicit $1/N$ is from averaging fresh client blocks; it is not available for one client's displacement.

### B7. E[x Delta^T]

For $\delta_{c,h}=\theta_{c,h}-x$, Taylor expansion at $x$ gives

$$
q(x+\delta_{c,h})
=q(x)+Dq(x)\delta_{c,h}+\mathcal R_{c,h},
\qquad
\|\mathcal R_{c,h}\|\leq C\|\delta_{c,h}\|^2,
$$

and expansion at zero gives

$$
q(x)=\frac12T[x,x]+\mathcal R_q(x),
\qquad
\|\mathcal R_q(x)\|\leq C\|x\|^3.
$$

The four required contributions to $\mathbb E[x\bar q_h^\top]$ are:

1. The signed $T[x,x]$ term is a contraction of $\mathcal T_3$, hence $O(v)\subset O(r)$.
2. The cubic remainder is bounded by $C\mathbb E\|x\|^4=O(v)\subset O(r)$.
3. Since $\|Dq(x)\|\leq C\|x\|$, B4 and B6 give
   $$
   \mathbb E[\|x\|^2\|\bar\delta_h\|]
   \leq \sqrt{v_{\gamma,N}}
   \sqrt{\gamma^2/N+\gamma^2s_{\gamma,N}}
   =O(r_{\gamma,N}).
   $$
   The last comparison follows after setting $t=1/N$ and using $\sqrt{\gamma t}\leq(\gamma+t)/2$.
4. The quadratic displacement remainder satisfies
   $$
   \frac1N\sum_c\mathbb E[\|x\|\|\delta_{c,h}\|^2]
   =O_{H,d}(\gamma^2\sqrt{s_{\gamma,N}})
   =O_{H,d}(r_{\gamma,N}),
   $$
   by the scale calculation in A4.

Multiplication by the outer $\gamma$ in $\Delta$, followed by a fixed $H$-sum, proves

$$
\boxed{\|\mathbb E[x\Delta^\top]\|
=O_{H,d}(\gamma r_{\gamma,N}).}
$$

Plain Cauchy--Schwarz on $x$ and $\Delta$ would not deliver this scale and is not used as the primary argument.

### B8. E[eta Delta^T]

Index the full collection of fresh vector blocks by $i=(c,j)$. Then

$$
\eta=\sum_iB_i\epsilon_i,
\qquad
B_i=-\frac\gamma N P^{H-j},
\qquad
\|B_i\|=O_H(\gamma/N).
$$

Let $Z^{(i,0)}$ replace the whole vector block $\epsilon_i$ by zero. Stability of each subsequent local step gives

$$
\sup_{h\leq H}
\|\theta_{c,h}(Z)-\theta_{c,h}(Z^{(i,0)})\|
\leq C_H\gamma\|\epsilon_i\|.
$$

Only one client changes. The client average contributes $1/N$, $q$ is globally Lipschitz, and the outer factor in $\Delta$ is $\gamma$; therefore

$$
\|\Delta(Z)-\Delta(Z^{(i,0)})\|
\leq C_H\frac{\gamma^2}{N}\|\epsilon_i\|.
$$

The replaced-block variable $\Delta(Z^{(i,0)})$ is independent of $\epsilon_i$. Centering removes

$$
\mathbb E[\epsilon_i\Delta(Z^{(i,0)})^\top]=0.
$$

Each remaining summand is bounded by $C_H(\gamma/N)(\gamma^2/N)\mathbb E\|\epsilon_i\|^2$. There are exactly $NH$ blocks, so

$$
\boxed{
\|\mathbb E[\eta\Delta^\top]\|
\leq NH\,C_{H,d}\frac{\gamma^3}{N^2}
=O_{H,d}(\gamma^3/N).}
$$

The replacement is blockwise. Coordinates within a block may remain correlated.

### B9. Delta Delta^T

B3 directly gives

$$
\boxed{\|\mathbb E[\Delta\Delta^\top]\|
\leq\mathbb E\|\Delta\|^2=O_{H,d}(\gamma^4).}
$$

### B10. Linearized Lyapunov equation

For $x_{\mathrm{lin}}^+=P^Hx_{\mathrm{lin}}+\eta$, stationarity gives

$$
M_{\mathrm{lin}}=P^HM_{\mathrm{lin}}(P^H)^\top
+\frac{\gamma^2}{N}\sum_{k=0}^{H-1}P^kC(P^k)^\top.
$$

Any solution of the one-step equation

$$
M= PMP^\top+\frac{\gamma^2}{N}C
$$

satisfies the $H$-step equation by telescoping. Conversely, $P^H$ is a strict contraction, so the $H$-step stationary solution is unique. The equations are therefore equivalent.

Diagonalize only $A=Q\operatorname{diag}(a_i)Q^\top$ and express $C,M$ in that basis. No diagonalization of $C$ is needed. Entrywise,

$$
(M_{\mathrm{lin}})_{ij}
=\frac{\gamma}{N}
\frac{C_{ij}}{a_i+a_j-\gamma a_ia_j},
\qquad
(S_C)_{ij}=\frac{C_{ij}}{a_i+a_j}.
$$

The denominators stay uniformly positive for $\gamma\leq\gamma_0$, and their difference gives

$$
\boxed{M_{\mathrm{lin}}=\frac\gamma N S_C+O_d(\gamma^2/N).}
$$

No $AC=CA$ assumption appears.

### B11. Nonlinear Lyapunov inversion

Define

$$
\mathcal S_\gamma(X)=X-P^HX(P^H)^\top.
$$

In the eigenbasis of $A$, its multipliers are

$$
1-(1-\gamma a_i)^H(1-\gamma a_j)^H\geq c_H\gamma,
$$

so

$$
\boxed{\|\mathcal S_\gamma^{-1}\|=O_H(1/\gamma).}
$$

B7, B8, and B9 make the entire nonlinear covariance forcing

$$
O(\gamma r_{\gamma,N})+O(\gamma^3/N)+O(\gamma^4)
=O(\gamma r_{\gamma,N}).
$$

The inverse therefore produces $O(r_{\gamma,N})$. A forcing estimate of only $O(r_{\gamma,N})$ would lose $1/\gamma$ and would not close the claim.

### B12. Result

Combining B10 and B11, and absorbing $O(\gamma^2/N)$ into $O(r_{\gamma,N})$, gives

$$
\boxed{M_x^{\mathrm{FA}}=\frac\gamma N S_C
+O_{H,d}(r_{\gamma,N}).}
$$

The dependency is non-circular: coarse moments precede B4, B4 precedes B5, and both precede B7 and this conclusion.

## 6. Local signed third tensor and Taylor tail

Let $\delta_{c,h}=\theta_{c,h}-x$. Exact trilinear expansion, followed by client averaging, gives the symmetrized identity

$$
\frac1N\sum_c\mathbb E[\theta_{c,h}^{\otimes3}]
=\mathbb E[x^{\otimes3}]
+3\,\operatorname{Sym}\mathbb E[x^{\otimes2}\otimes\bar\delta_h]
+\frac3N\sum_c\operatorname{Sym}\mathbb E[x\otimes\delta_{c,h}^{\otimes2}]
+\frac1N\sum_c\mathbb E[\delta_{c,h}^{\otimes3}].
$$

The four terms have the following independent bounds.

1. B5 gives $\mathbb E[x^{\otimes3}]=O(v)\subset O(r)$.
2. Write $\bar\delta_h=\bar D_h+\bar R_h$.  Centering after fixing the
   round-start state gives
   $\mathbb E[x^{\otimes2}\otimes\bar D_h]=0$.  Inserting
   $\nabla f(x+\delta)=Ax+A\delta+q(x+\delta)$ into $\bar R_h$, the $Ax$
   term contracts the signed global third tensor and is $O(\gamma v)$; the
   $A\delta$ terms use B6 and the $q$ terms use B4 plus the coarse sixth
   moment.  Every contribution is $O(r)$.
3. Expanding $\delta_{c,h}=D_{c,h}+R_{c,h}$ gives the exact classes

   | class in $\mathbb E[x\otimes\delta_{c,h}^{\otimes2}]$ | bound |
   | --- | --- |
   | $x\otimes D^{\otimes2}$ | $\gamma^2h\,b\otimes C=O(\gamma^2s)$ |
   | $x\otimes\operatorname{Sym}(D\otimes R)$ | $O(\gamma^2\sqrt{s})$ |
   | $x\otimes R^{\otimes2}$ | $O(\gamma^2s)$ |

   The first identity uses independence of $x$ from the fresh blocks.  The
   last two bounds use A4--A5 and the sharp fourth moment.
   Since $\gamma^2s\leq r$ and
   $\gamma^2\sqrt{s}\leq r$, the third contribution is $O(r)$.
4. The signed local cubic has the full tensor expansion

   $$
   \mathbb E\delta^{\otimes3}
   =\mathbb ED^{\otimes3}
   +3\operatorname{Sym}\mathbb E[D^{\otimes2}\otimes R]
   +3\operatorname{Sym}\mathbb E[D\otimes R^{\otimes2}]
   +\mathbb ER^{\otimes3}.
   $$

   Equal-block counting gives $\mathbb ED^{\otimes3}=O_H(\gamma^3)$,
   including nonzero noise third moments.  Hölder together with the local
   fourth/sixth bounds gives respectively
   $O(\gamma^3\sqrt{s})$, $O(\gamma^3s)$, and
   $O(\gamma^3s^{3/2})$ for the remaining three classes.  All are $O(r)$
   for $N\geq2$ and $\gamma\leq1$.  Noise symmetry is not used.

Consequently,

$$
\boxed{
\left\|\frac1N\sum_c\mathbb E[\theta_{c,h}^{\otimes3}]\right\|
=O_{H,d}(r_{\gamma,N}).}
$$

**This is a signed tensor bound.**

**No claim is made that**
$$
\frac1N\sum_c\mathbb E\|\theta_{c,h}\|^3
$$
**is $O(r_{\gamma,N})$.**

The sharp global fourth moment and fixed-step displacement give

$$
\frac1N\sum_c\mathbb E\|\theta_{c,h}\|^4
\leq C_H\left(\mathbb E\|x\|^4
+\frac1N\sum_c\mathbb E\|\delta_{c,h}\|^4\right)
=O_{H,d}(v_{\gamma,N}),
$$

because $\mathbb E\|\delta_{c,h}\|^4=O_H(\gamma^4)$ and $\gamma^4\leq v_{\gamma,N}$ for $\gamma\leq1$.

At the origin, Taylor expansion is

$$
\nabla f(u)=Au+\frac12T[u,u]
+\frac16D^4f(0)[u,u,u]+\rho_5(u),
\qquad
\|\rho_5(u)\|\leq C\|u\|^4.
$$

Homogeneity is essential: the same $D^4f(0)$ contracts every client's signed cubic tensor. Therefore its client-averaged contribution is $O(r)$. The fifth-order Taylor remainder is controlled by the absolute fourth moment and is $O(v)\subset O(r)$. Hence the full client-averaged Taylor tail is $O_{H,d}(r_{\gamma,N})$.

This excludes an additional client-independent $N^0\gamma^2$ contribution from fourth- and fifth-derivative Taylor terms. It does not identify the full finite-$N$ $\gamma^2/N$ coefficient.

## 7. Coefficient assembly

The exact stationary mean balance, summed over local steps and combined with the audited Taylor tail, is

$$
0=A\sum_{h=0}^{H-1}m_h
+\frac12T\!\left[\sum_{h=0}^{H-1}M_h\right]
+O_{H,d}(r_{\gamma,N}).
$$

The exact mean displacement formula and the coarse local second moments give $m_h-b=O_{H,d}(\gamma s_{\gamma,N})=O_{H,d}(r_{\gamma,N})$. Since $H$ is fixed,

$$
\sum_{h=0}^{H-1}m_h=Hb+O_{H,d}(r_{\gamma,N}).
$$

Using $M_h=M_x+U_h$, dividing by fixed $H$, and multiplying by fixed $A^{-1}$ gives

$$
b=-\frac12A^{-1}T[M_x]
-\frac1{2H}A^{-1}T\!\left[\sum_{h=0}^{H-1}U_h\right]
+O_{H,d}(r_{\gamma,N}).
$$

The local arithmetic is recomputed independently:

$$
\sum_{h=0}^{H-1}h=\frac{H(H-1)}2,
\qquad
-\frac1{2H}\frac{H(H-1)}2=-\frac{H-1}{4}.
$$

Substitution of the local and global second-moment expansions gives

$$
b=-\frac\gamma{2N}A^{-1}T[S_C]
-\gamma^2\frac{H-1}{4}A^{-1}T[C]
+O_{H,d}(r_{\gamma,N}),
$$

and

$$
\boxed{B_{20,\mathrm{FA}}^{(d)}(H)
=-\frac{H-1}{4}A^{-1}T[C].}
$$

For the matched comparison, the imported P2 interface is implemented in
`src/stationary_bias/workstreams/p2_multidimensional_validation/theory.py`
by `vector_theory_targets`: its `B20`, `B20_local`, and `B20_ctrl` definitions
are the three formulas below.  The frozen d=2 statement and numerical targets
are recorded independently in
`workstreams/p2_multidimensional_validation/artifacts/archive/protocols/formal_protocol.md`.
P3 imports only this coefficient interface; the FedAvg coefficient and the
subtraction below are derived here.

$$
B_{20,\mathrm{SCAF}}^{(d)}
=-\frac{(H-1)(5H-1)}{12H}A^{-1}T[C],
$$

$$
B_{20,\mathrm{local}}^{(d)}
=-\frac{H-1}{4}A^{-1}T[C],
\qquad
B_{20,\mathrm{ctrl}}^{(d)}
=-\frac{(H-1)(2H-1)}{12H}A^{-1}T[C].
$$

Direct subtraction, with the FedAvg denominator rewritten as $12H$, gives

$$
\begin{aligned}
B_{20,\mathrm{SCAF}}^{(d)}-B_{20,\mathrm{FA}}^{(d)}
&=\frac{H-1}{12H}\{-\,(5H-1)+3H\}A^{-1}T[C]\\
&=-\frac{(H-1)(2H-1)}{12H}A^{-1}T[C]\\
&=B_{20,\mathrm{ctrl}}^{(d)}.
\end{aligned}
$$

All signs and $H$-factors agree.

## 8. Remainder ledger

| Item | Input scale | Operation | Output scale | $1/\gamma$ factor? | Uniform in $N$? | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Mean correction $\sum_h(m_h-b)$ | each $\gamma s=r$ | fixed $H$-sum | $O(r)$ | No | Yes | derived |
| Global second moment | linear $(\gamma/N)S_C$; nonlinear forcing $\gamma r$ | $\mathcal S_\gamma^{-1}$ | $(\gamma/N)S_C+O(r)$ | Yes, exactly once | Yes | derived |
| Each local $U_h$ remainder | $O(r)$ | none | $O(r)$ | No | Yes | bounded |
| Fixed-$H$ sum of $U_h$ remainders | $H$ terms of $O(r)$ | finite sum | $O_{H,d}(r)$ | No | Yes | bounded |
| $D^4f(0)$ Taylor contribution | signed cubic tensor $O(r)$ | fixed tensor contraction | $O(r)$ | No | Yes | bounded |
| Fifth-order Taylor remainder | absolute fourth moment $O(v)$ | bounded remainder | $O(v)\subset O(r)$ | No | Yes | bounded |
| Multiplication by $T$ | matrix/tensor remainder $O(r)$ | fixed linear contraction | $O_{d}(r)$ | No | Yes | bounded |
| Multiplication by $A^{-1}$ | vector remainder $O(r)$ | fixed linear map | $O_{d}(r)$ | No | Yes | bounded |
| Division by $H$ | $O_{H,d}(r)$ | fixed scalar | $O_{H,d}(r)$ | No | Yes | bounded |

The only $1/\gamma$ loss occurs in nonlinear Lyapunov inversion, where the audited forcing is $O(\gamma r)$. Multiplication by $A^{-1}$, contraction by $T$, and fixed-$H$ sums only modify $C_{H,d}$. They create no $1/\gamma$ loss. The final remainder is

$$
\boxed{O_{H,d}(\gamma^2/N+\gamma^3).}
$$

## 9. Regression and negative checks

### d=1 specialization

Let $A=a$, $T=\tau$, and $C=\sigma^2$. Then $S_C=\sigma^2/(2a)$, so

$$
b_{\mathrm{FA}}
=-\frac{\tau\sigma^2}{4a^2}\frac\gamma N
-\frac{\tau\sigma^2}{4a}(H-1)\gamma^2
+O_H(\gamma^2/N+\gamma^3).
$$

This matches the target implemented in `src/stationary_bias/workstreams/p1_matched_fedavg/theory.py` exactly.

### H=1 algebraic check

The factor $H-1$ makes the second-order local coefficient zero. This is an algebraic sanity check; the formal scope remains $H\geq2$.

### Quadratic check

If $T=0$, both displayed bias coefficients vanish.

### Deterministic check

If $C=0$, uniqueness of the Lyapunov solution gives $S_C=0$, and both displayed stochastic-bias layers vanish.

### T[C]=0 caveat

The coefficient $B_{20}$ may vanish even when $C\ne0$. No claim is made that the $\gamma^2$ layer must be the first nonzero client-independent layer.

### Correlated/noncommuting check

The covariance calculation uses whole vector blocks and permits correlated coordinates. B10 diagonalizes $A$ only; neither diagonal $C$ nor $AC=CA$ is required.

## 10. Derivation summary

| Quantity | Result | Derivation | Notes |
| --- | --- | --- | --- |
| Local noise coefficient | $\gamma^2hC$ | A2 double-sum cancellation | No $1/N$ |
| xR | $O(r)$ | A3 coarse second moments | Freshness not needed |
| DR | $O(r)$ | A4 explicit $t=1/N$ inequality | Absolute cross-moment bound |
| RR | $O(r)$ | A5 $\gamma^2s\leq r$ | Uniform constant |
| High-moment interface | coarse fourth/sixth local and global | Mangold et al., Lemma 8; Section 3 | Lemma 8, not Lemma 6 |
| Sharp fourth moment | $O(v)$ | B4 fourth-order stationary drift | No sharp covariance input |
| Signed global third tensor | $O(v)$ | B5 tensor equation | Not an absolute third moment |
| $\mathbb E[x\Delta^\top]$ | $O(\gamma r)$ | B7 four signed pieces | Plain Cauchy--Schwarz is insufficient |
| $\mathbb E[\eta\Delta^\top]$ | $O(\gamma^3/N)$ | B8 block replacement and $NH$ count | Correlated coordinates allowed |
| Nonlinear Lyapunov inversion | forcing $O(\gamma r)$ | B11 inverse $O(1/\gamma)$ | Produces $O(r)$ |
| Local signed third tensor | $O(r)$ | Section 6 exact tensor expansion | Signed statement only |
| Taylor $D^4$ term | $O(r)$ | Section 6 signed contraction | Homogeneity required |
| Fifth-order remainder | $O(r)$ | Section 6 absolute fourth moment | In fact $O(v)$ |
| Mean assembly | displayed two-term expansion | Section 7 stationary balance | Raw moments used |
| $H$-sum coefficient | $-(H-1)/4$ | Section 7 explicit arithmetic | Sign checked |
| Final remainder | $O(\gamma^2/N+\gamma^3)$ | Section 8 ledger | Fixed maps add no loss |
| Scalar specialization | one-dimensional coefficient | Section 9 | Algebraic check |
| Matched SCAFFOLD--FedAvg attribution | control coefficient | Section 7 direct subtraction | Full finite-$N$ term is outside scope |

## 11. Interpretation boundary

The expansion applies under the assumptions in Section 2. Numerical validation
is a falsification check and does not constitute a proof. The result does not
claim the full finite-$N$ $\gamma^2$ coefficient, heterogeneity, growing
$H$, state-dependent noise, novelty, or a global algorithm ranking.
