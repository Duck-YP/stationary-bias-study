import numpy as np
from .model import gradient_reference,q_stable,A,operators,reference_round
from .kernels import q_compiled,explicit_round,trigonometric_chunk,scalar_noise

def test_gradient_independence():
    rng=np.random.default_rng(301)
    for scale in (1e-7,.3,3.):
        for x in rng.normal(size=(30,2))*scale:
            np.testing.assert_allclose(q_compiled(*x,.05),gradient_reference(x)-A@x,atol=8e-16,rtol=2e-8)
            np.testing.assert_allclose(q_compiled(*x,.05),q_stable(x),atol=1e-16,rtol=1e-14)

def test_reference_explicit_nonzero():
    rng=np.random.default_rng(302); gamma=1/1024; N=9; H=4
    x=rng.normal(size=(2,2))*.2; c=rng.normal(size=(N,2)); c-=c.mean(0)
    xr=x.copy(); cr=c.copy(); ops=operators(gamma,H)
    for _ in range(35):
        eps=rng.normal(size=(H,N,2))
        xr,cr,before=reference_round(xr,cr,gamma,eps)
        x,c,z,eta,res=explicit_round(x,c,gamma,eps,*ops)
        np.testing.assert_allclose(x,xr,rtol=0,atol=2e-14)
        np.testing.assert_allclose(c,cr,rtol=0,atol=3e-12)
        for a in range(2):
            qm=np.array([np.mean([q_stable(v) for v in before[h,a]],axis=0) for h in range(H)])
            expected=-gamma*np.linalg.solve(np.diag(ops[1]),(ops[0]*qm).sum(0))
            np.testing.assert_allclose(z[a],expected,atol=2e-15,rtol=2e-11)
        assert np.max(abs(c.mean(0)))<2e-14
        assert np.max(abs(res))<2e-16

def test_h1_and_preserve_nonzero_control_mean():
    rng=np.random.default_rng(303); N=8; gamma=.001; H=1; ops=operators(gamma,H)
    x=np.repeat([[.17,-.21]],2,axis=0); c=rng.normal(size=(N,2)); c-=c.mean(0)
    for _ in range(30):
        x,c,*_=explicit_round(x,c,gamma,rng.normal(size=(H,N,2)),*ops)
        np.testing.assert_allclose(x[0],x[1],atol=5e-15,rtol=0)
    c+=np.array([.1,-.05]); old=c.mean(0)
    _,c,*_=explicit_round(x,c,gamma,rng.normal(size=(H,N,2)),*ops)
    np.testing.assert_allclose(c.mean(0),old,atol=1e-15,rtol=0)

def test_quadratic_and_deterministic():
    rng=np.random.default_rng(304); N=8; H=4; gamma=.001; ops=operators(gamma,H)
    x=np.repeat([[.1,-.2]],2,axis=0); c=rng.normal(size=(N,2)); c-=c.mean(0)
    eps=rng.normal(size=(H,N,2))
    new,_,z,eta,_=explicit_round(x,c,gamma,eps,*ops,alpha=0.)
    np.testing.assert_allclose(new,x*ops[2]+eta,atol=5e-16,rtol=0)
    np.testing.assert_array_equal(z,0.)
    c[:]=0
    for _ in range(30):
        x,c,*_=explicit_round(x,c,gamma,np.zeros_like(eps),*ops)
        np.testing.assert_allclose(x[0],x[1],atol=1e-16,rtol=0)
        np.testing.assert_allclose(c,0,atol=1e-15,rtol=0)

def test_active_indexed_path_and_resume(tmp_path):
    N=7; H=4; g=1/512; key=np.uint64(5381); ops=operators(g,H)
    x=np.array([[.13,-.19],[.13,-.19]]); c=np.zeros((N,2))
    for asym in (False,True):
        a=trigonometric_chunk(x.copy(),c.copy(),key,0,37,N,H,g,*ops,.25,asym)
        b=trigonometric_chunk(x.copy(),c.copy(),key,0,11,N,H,g,*ops,.25,asym)
        path=tmp_path/'checkpoint.npz'; np.savez(path,x=b[0],controls=b[1],round_id=11)
        with np.load(path) as cp:
            d=trigonometric_chunk(cp['x'],cp['controls'],key,int(cp['round_id']),26,N,H,g,*ops,.25,asym)
        for i in (0,1): np.testing.assert_array_equal(a[i],d[i])
        for i in range(2,7): np.testing.assert_array_equal(a[i],np.concatenate([b[i],d[i]]))
        xr=x.copy(); cr=c.copy()
        for t in range(37):
            eps=np.array([[[scalar_noise(key,t,h,k*2+j,asym)*np.sqrt(1+(.25 if j==0 else -.25)) for j in range(2)] for k in range(N)] for h in range(H)])
            xr,cr,_=reference_round(xr,cr,g,eps)
            np.testing.assert_allclose(a[2][t],xr,atol=3e-14,rtol=0)

def test_finite_window_pre_post_identity():
    N=13; H=4; g=1/1024; ops=operators(g,H); key=np.uint64(991)
    x=np.array([[.3,-.1],[.25,-.18]]); c=np.zeros((N,2)); T=183
    new,ctrl,raw,bal,eta,res,cm=trigonometric_chunk(x.copy(),c,key,0,T,N,H,g,*ops,-.25,True)
    endpoint=(new-x)/T
    pre=np.concatenate([x[None],raw[:-1]],axis=0)
    pre_res=ops[1]*(pre.mean(0)-bal.mean(0))-eta.mean(0)+endpoint-res.mean(0)
    post_res=ops[1]*(raw.mean(0)-bal.mean(0))-eta.mean(0)+ops[2]*endpoint-res.mean(0)
    assert np.max(abs(pre_res))<2e-17
    assert np.max(abs(post_res))<2e-17
    paired=ops[1]*(raw[:,0].mean(0)-raw[:,1].mean(0)-bal[:,0].mean(0)+bal[:,1].mean(0))
    paired+=ops[2]*(endpoint[0]-endpoint[1])-res[:,0].mean(0)+res[:,1].mean(0)
    assert np.max(abs(paired))<3e-17
