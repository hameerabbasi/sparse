import time

import sparse

import numpy as np

I_ = 1000
J_ = 25
K_ = 1000
L_ = 100
DENSITY = 0.0001
ITERS = 3
rng = np.random.default_rng(0)


def benchmark(func, info, args):
    print(info)
    start = time.time()
    for _ in range(ITERS):
        func(*args)
    elapsed = time.time() - start
    print(f"Took {elapsed / ITERS} s.\n")


if __name__ == "__main__":
    print("MTTKRP Example:\n")

    B_sps = sparse.random((I_, K_, L_), density=DENSITY, random_state=rng) * 10
    D_sps = rng.random((L_, J_)) * 10
    C_sps = rng.random((K_, J_)) * 10

    # Finch
    with sparse.Backend(backend=sparse.BackendType.Finch):
        B = sparse.asarray(B_sps.todense(), format="csf")
        D = sparse.asarray(np.array(D_sps, order="F"))
        C = sparse.asarray(np.array(C_sps, order="F"))

        @sparse.compiled
        def mttkrp_finch(B, D, C):
            return sparse.sum(B[:, :, :, None] * D[None, None, :, :] * C[None, :, None, :], axis=(1, 2))

        # Compile
        result_finch = mttkrp_finch(B, D, C)
        assert sparse.nonzero(result_finch)[0].size > 5
        # Benchmark
        benchmark(mttkrp_finch, info="Finch", args=[B, D, C])

    # Numba
    with sparse.Backend(backend=sparse.BackendType.Numba):
        B = sparse.asarray(B_sps, format="gcxs")
        D = D_sps
        C = C_sps

        def mttkrp_numba(B, D, C):
            return sparse.sum(B[:, :, :, None] * D[None, None, :, :] * C[None, :, None, :], axis=(1, 2))

        # Compile
        result_numba = mttkrp_numba(B, D, C)
        # Benchmark
        benchmark(mttkrp_numba, info="Numba", args=[B, D, C])

    np.testing.assert_allclose(result_finch.todense(), result_numba.todense())
