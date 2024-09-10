import pytest
import os
import sparse

@pytest.fixture
def seed(scope="session"):
    return 42


def get_backend_id(param):
    backend = param
    return f"{backend=}"

@pytest.fixture(params=[sparse._BACKEND], autouse=True, ids=get_backend_id)
def backend(request):

    return request.param
    

@pytest.fixture
def min_size(scope="session"):
    return 100

@pytest.fixture
def max_size(scope="session"):
    return 2**26
