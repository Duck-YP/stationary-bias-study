import numpy as np
from scipy.linalg import solve_discrete_lyapunov
from scipy import sparse
from .model import A,C,U,ALPHA,grad,hessian,third_contract,objective,logistic
from .kernels import reference,production_round,controlled_chunk,logistic_chunk,random_key,stream_key
from .data import sparse_logistic,partition


def controlled_args(gamma,H):
    P=np.eye(2)-gamma*A
    weights=np.array([np.linalg.matrix_power(P,H-1-h) for h in range(H)])
    operator=np.linalg.solve(np.eye(2)-np.linalg.matrix_power(P,H),np.eye(2))
    return weights,operator,np.linalg.cholesky(C)


def check_close(a,b,tol=1e-10):
    np.testing.assert_allclose(a,b,rtol=tol,atol=tol)


def test_reference_production_rounds():
    rng=np.random.default_rng(17)
    N=8; H=4; gamma=.01
    x=rng.normal(size=2)*.1; xi=rng.normal(size=(N,2)); xi-=xi.mean(0)
    xr=x.copy(); cr=xi.copy()
    for _ in range(20):
        eps=rng.choice([-1.,1.],size=(H,N,2)) @ np.linalg.cholesky(C).T
        a=reference(xr,cr,gamma,eps)
        b=production_round(x,xi,gamma,eps,True,np.zeros((N,2)),A,ALPHA,U)
        for ar,br in zip(a,b): check_close(ar,br)
        xr,cr=a[:2]; x,xi=b[:2]
        assert np.linalg.norm(xi.sum(0))<1e-10*(1+np.linalg.norm(xi))


def test_h1_nonzero_controls():
    rng=np.random.default_rng(18); N=8
    c=rng.normal(size=(N,2)); c-=c.mean(0)
    x=np.array([.3,-.2]); y=x.copy()
    for _ in range(40):
        eps=rng.normal(size=(1,N,2))
        x,c,*_=reference(x,c,.01,eps)
        y,_,*_=reference(y,np.zeros_like(c),.01,eps,False)
        check_close(x,y)


def test_quadratic_global_linear_dynamics_covariance():
    rng=np.random.default_rng(19); N=8; gamma=.02; P=np.eye(2)-gamma*A
    M=solve_discrete_lyapunov(P,gamma**2*C/N)
    check_close(M,P@M@P.T+gamma**2*C/N)
    assert np.linalg.norm(A@C-C@A)>1e-3
    for H in (1,2,4,8):
        x=np.array([.3,-.2]); y=x.copy(); linear=x.copy(); c=np.zeros((N,2))
        Q=np.zeros((2,2))
        for h in range(H):
            ph=np.linalg.matrix_power(P,h)
            Q+=gamma**2/N*ph@C@ph.T
        PH=np.linalg.matrix_power(P,H)
        check_close(solve_discrete_lyapunov(PH,Q),M)
        for _ in range(30):
            eps=rng.normal(size=(H,N,2))@np.linalg.cholesky(C).T
            for h in range(H): linear=P@linear-gamma*eps[h].mean(0)
            x,c,*_=reference(x,c,gamma,eps,True,alpha=0)
            y,_,*_=reference(y,np.zeros_like(c),gamma,eps,False,alpha=0)
            check_close(x,linear); check_close(y,linear)


def test_deterministic_consistency():
    x=np.array([.2,-.1]); y=x.copy(); c=np.zeros((8,2))
    for _ in range(100):
        eps=np.zeros((4,8,2))
        x,c,*_=reference(x,c,.01,eps)
        y,_,*_=reference(y,c,.01,eps,False)
        check_close(x,y); check_close(c,0)


def test_derivatives():
    x=np.array([.3,-.2]); e=1e-5
    gfd=np.array([(objective(x+e*v)-objective(x-e*v))/(2*e) for v in np.eye(2)])
    check_close(grad(x),gfd,2e-9)
    hfd=np.column_stack([(grad(x+e*v)-grad(x-e*v))/(2*e) for v in np.eye(2)])
    check_close(hessian(x),hfd,2e-9)
    T=np.stack([(hessian(x+e*v)-hessian(x-e*v))/(2*e) for v in np.eye(2)],axis=2)
    check_close(third_contract(x,C),np.einsum("ijk,jk->i",T,C),2e-9)


def test_orthogonal_path():
    Q=np.array([[.6,-.8],[.8,.6]])
    rng=np.random.default_rng(20); x=np.array([.2,-.1]); y=Q@x
    c=np.zeros((8,2)); cr=c.copy()
    for _ in range(30):
        eps=rng.normal(size=(4,8,2))
        x,c,*_=reference(x,c,.01,eps)
        y,cr,*_=reference(y,cr,.01,eps@Q.T,matrix=Q@A@Q.T,direction=Q@U)
        check_close(y,Q@x); check_close(cr,c@Q.T)


def test_noise_keys_and_covariance():
    key=stream_key("E1",0,20001,"test")
    signs=np.array([[1. if random_key(key,t,0,j)&np.uint64(1) else -1. for j in range(4)] for t in range(50000)])
    assert np.max(abs(signs.mean(0)))<.02
    assert np.max(abs(np.cov(signs,rowvar=False,bias=True)-np.eye(4)))<.025
    eps=signs[:,:2]@np.linalg.cholesky(C).T
    check_close(np.cov(eps,rowvar=False,bias=True),C,.025)
    assert random_key(key,5,2,7)==random_key(key,5,2,7)
    assert random_key(key,5,2,7)!=random_key(key,6,2,7)


def test_compiled_controlled_and_balance():
    N=8; H=4; gamma=.01; key=stream_key("E1",0,20002,"test")
    args=controlled_args(gamma,H)
    x,c,raw,bal,*_=controlled_chunk(np.zeros((2,2)),np.zeros((N,2)),key,0,20,N,H,gamma,*args)
    xr=np.zeros(2); cr=np.zeros((N,2)); yr=xr.copy()
    P=np.eye(2)-gamma*A
    for t in range(20):
        z=np.array([[[1. if random_key(key,t,h,c*2+j)&np.uint64(1) else -1. for j in range(2)] for c in range(N)] for h in range(H)])
        eps=z@np.linalg.cholesky(C).T
        xr,cr,_,before=reference(xr,cr,gamma,eps)
        yr,_,_,beforefa=reference(yr,np.zeros_like(cr),gamma,eps,False)
        check_close(raw[t,0],xr); check_close(raw[t,1],yr)
        for a,bef in enumerate((before,beforefa)):
            q=np.array([(grad(b)-b@A.T).mean(0) for b in bef])
            qb=sum(args[0][h]@q[h] for h in range(H))
            check_close(bal[t,a],-gamma*np.linalg.solve(np.eye(2)-np.linalg.matrix_power(P,H),qb))


def test_checkpoint_chunk_agreement():
    key=stream_key("E1",0,20003,"test"); args=controlled_args(.01,4)
    whole=controlled_chunk(np.zeros((2,2)),np.zeros((8,2)),key,0,40,8,4,.01,*args)
    first=controlled_chunk(np.zeros((2,2)),np.zeros((8,2)),key,0,17,8,4,.01,*args)
    second=controlled_chunk(first[0],first[1],key,17,23,8,4,.01,*args)
    for i in (0,1): np.testing.assert_array_equal(whole[i],second[i])
    for i in (2,3,4,5): np.testing.assert_array_equal(whole[i],np.concatenate((first[i],second[i])))


def test_logistic_global_objective_and_derivatives():
    rng=np.random.default_rng(21); Z=rng.normal(size=(256,124))*.1; y=rng.integers(0,2,256); x=rng.normal(size=124)*.1
    f,g,H=logistic(Z,y,x)
    for regime in ("R0","R1","R2"):
        members=partition(y,8,regime,4101)
        local=[logistic(Z[rows],y[rows],x) for rows in members]
        check_close(np.mean([a[0] for a in local]),f)
        check_close(np.mean([a[1] for a in local],0),g)
    e=1e-5; v=rng.normal(size=124); v/=np.linalg.norm(v)
    check_close((logistic(Z,y,x+e*v)[0]-logistic(Z,y,x-e*v)[0])/(2*e),g@v,2e-9)
    check_close((logistic(Z,y,x+e*v)[1]-logistic(Z,y,x-e*v)[1])/(2*e),H@v,2e-9)


def test_logistic_reference_production_h1_resume():
    rng=np.random.default_rng(22); Z=sparse.csr_matrix(rng.normal(size=(128,124))*.05); y=rng.integers(0,2,128).astype(float)
    members=partition(y,8,"R1",4101); key=stream_key("E3",4101,20001,"test")
    csr=(Z.indptr.astype(np.int64),Z.indices.astype(np.int64),Z.data,y)
    whole=logistic_chunk(np.zeros((2,124)),np.zeros((8,124)),key,0,10,4,.1,4,members,*csr)
    first=logistic_chunk(np.zeros((2,124)),np.zeros((8,124)),key,0,3,4,.1,4,members,*csr)
    second=logistic_chunk(first[0],first[1],key,3,7,4,.1,4,members,*csr)
    np.testing.assert_array_equal(whole[2],np.concatenate((first[2],second[2])))
    h1=logistic_chunk(np.zeros((2,124)),rng.normal(size=(8,124)),key,0,1,1,.1,4,members,*csr)
    c=rng.normal(size=(8,124)); c-=c.mean(0)
    h1=logistic_chunk(np.zeros((2,124)),c,key,0,10,1,.1,4,members,*csr)
    check_close(h1[2][:,0],h1[2][:,1])
    theta=np.zeros((2,8,124)); controls=np.zeros((8,124)); xx=np.zeros((2,124))
    # Independent dense reference, with the compiled kernel's keyed index input.
    dense=Z.toarray()
    for t in range(10):
        theta[:]=xx[:,None,:]
        for h in range(4):
            for c in range(8):
                rows=[members[c,int(random_key(key,t,h,c*4+s)%np.uint64(members.shape[1]))] for s in range(4)]
                for a in range(2):
                    gg=logistic(dense[rows],y[rows],theta[a,c])[1]
                    if a==0: gg+=controls[c]
                    theta[a,c]-=.1*gg
        xx=theta.mean(1)
        controls+=(theta[0]-xx[0])/(.1*4)
        check_close(xx,whole[2][t])


def test_cross_run_ustat_zero_bias_calibration():
    rng=np.random.default_rng(23)
    repetitions=rng.normal(size=(5000,12,2))
    u=(np.sum(repetitions.sum(1)**2,axis=1)-np.sum(repetitions**2,axis=(1,2)))/(12*11)
    assert abs(u.mean())<4*u.std()/np.sqrt(len(u))
    assert np.any(u<0)


def test_r0_h1_allocation_identity():
    rng=np.random.default_rng(24); Z=sparse.csr_matrix(rng.normal(size=(128,124))*.05); y=rng.integers(0,2,128).astype(float)
    key=stream_key("E3",0,20001,"R0_h1_shared_mapping")
    paths=[]
    for N in (8,32,128):
        mem=partition(y,N,"R0",0)
        r=logistic_chunk(np.zeros((2,124)),np.zeros((N,124)),key,0,15,1,.1,256//N,mem,Z.indptr.astype(np.int64),Z.indices.astype(np.int64),Z.data,y)
        paths.append(r[2])
    check_close(paths[0],paths[1]); check_close(paths[1],paths[2])


def test_actual_checkpoint_file_resume(tmp_path,monkeypatch):
    from . import engine
    import time
    cell=dict(id="E0_checkpoint",family="E1",N=8,H=4,gamma=.01,m=1,regime="",partition_seed=0)
    schedule=dict(burn=50,batch_length=100,batches=64,primary_batches=64)
    whole=tmp_path/"whole"; resumed=tmp_path/"resumed"
    assert engine.run_one(cell,20001,"test",schedule,whole)
    original=time.monotonic
    calls=[0]
    def controlled_clock():
        calls[0]+=1
        return 0. if calls[0]==1 else 10.
    monkeypatch.setattr(engine.time,"monotonic",controlled_clock)
    assert not engine.run_one(cell,20001,"test",schedule,resumed,deadline=1.)
    with np.load(resumed/"raw/test/E0_checkpoint/seed_20001/checkpoint.npz") as cp:
        assert int(cp["t"])==50
    monkeypatch.setattr(engine.time,"monotonic",original)
    assert engine.run_one(cell,20001,"test",schedule,resumed,resume=True)
    a=np.load(whole/"raw/test/E0_checkpoint/seed_20001/result.npz")
    b=np.load(resumed/"raw/test/E0_checkpoint/seed_20001/result.npz")
    for name in ("x","controls","mean","raw_mean","second_moment","batch_means","batch_raw_means","batch_control_sum","snapshot"):
        np.testing.assert_array_equal(a[name],b[name])
