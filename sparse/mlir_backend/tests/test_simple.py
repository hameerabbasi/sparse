import typing

import sparse

import pytest

import numpy as np
import scipy.sparse as sps

if sparse._BACKEND != sparse._BackendType.MLIR:
    pytest.skip("skipping MLIR tests", allow_module_level=True)

parametrize_dtypes = pytest.mark.parametrize(
    "dtype",
    [
        np.int8,
        np.uint16,
        np.float32,
        np.float64,
    ],
)


def generate_sampler(dtype: np.dtype, rng: np.random.Generator) -> typing.Callable[[tuple[int, ...]], np.ndarray]:
    dtype = np.dtype(dtype)
    if np.isdtype(dtype, kind="signed integer"):

        def sampler_signed(size: tuple[int, ...]):
            return rng.integers(-10, 10, dtype=dtype, endpoint=True, size=size)

        return sampler_signed

    if np.isdtype(dtype, kind="unsigned integer"):  #

        def sampler_unsigned(size: tuple[int, ...]):
            return rng.integers(0, 10, dtype=dtype, endpoint=True, size=size)

        return sampler_unsigned

    if np.isdtype(dtype, kind="real floating"):  #

        def sampler_real_floating(size: tuple[int, ...]):
            return -10 + 20 * rng.random(dtype=dtype, size=size)

        return sampler_real_floating

    raise NotImplementedError(f"{dtype=} not yet supported.")


def assert_csr_equal(desired: sps.csr_array, actual: sps.csr_array) -> None:
    np.testing.assert_array_equal(desired.todense(), actual.todense())
    # Broken due to https://github.com/scipy/scipy/issues/21442
    # desired.sort_indices()
    # desired.sum_duplicates()
    # desired.prune()

    # actual.sort_indices()
    # actual.sum_duplicates()
    # actual.prune()

    # np.testing.assert_array_equal(desired.todense(), actual.todense())

    # np.testing.assert_array_equal(desired.indptr, actual.indptr)
    # np.testing.assert_array_equal(desired.indices, actual.indices)
    # np.testing.assert_array_equal(desired.data, actual.data)


@parametrize_dtypes
def test_constructors(rng, dtype):
    SHAPE = (10, 5)
    DENSITY = 0.5
    sampler = generate_sampler(dtype, rng)
    a = sps.random_array(SHAPE, density=DENSITY, format="csr", dtype=np.float64, random_state=rng, data_sampler=sampler)
    c = np.arange(50, dtype=np.float64).reshape((10, 5))

    a_tensor = sparse.asarray(a)
    c_tensor = sparse.asarray(c)

    a_retured = a_tensor.to_scipy_sparse()
    assert_csr_equal(a, a_retured)

    c_returned = c_tensor.to_scipy_sparse()
    np.testing.assert_equal(c, c_returned)


@parametrize_dtypes
def test_add(rng, dtype):
    SHAPE = (10, 5)
    DENSITY = 0.5
    sampler = generate_sampler(dtype, rng)

    a = sps.random_array(SHAPE, density=DENSITY, format="csr", dtype=np.float64, random_state=rng, data_sampler=sampler)
    b = sps.random_array(SHAPE, density=DENSITY, format="csr", dtype=np.float64, random_state=rng, data_sampler=sampler)
    c = np.arange(50, dtype=np.float64).reshape((10, 5))

    a_tensor = sparse.asarray(a)
    b_tensor = sparse.asarray(b)
    c_tensor = sparse.asarray(c)

    actual = sparse.add(a_tensor, b_tensor).to_scipy_sparse()
    expected = a + b
    assert_csr_equal(actual, expected)

    actual = sparse.add(a_tensor, c_tensor).to_scipy_sparse()
    expected = sps.csr_matrix(a + c)
    assert_csr_equal(actual, expected)

    actual = sparse.add(c_tensor, a_tensor).to_scipy_sparse()
    expected = a + c
    assert isinstance(actual, np.ndarray)
    np.testing.assert_array_equal(actual, expected)