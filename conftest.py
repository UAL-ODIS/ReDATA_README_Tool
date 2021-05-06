import pytest


def pytest_addoption(parser):
    parser.addoption("--figshare-api-key", action="store",
                     default="Figshare production API token")
    parser.addoption("--figshare-stage-api-key", action="store",
                     default="Figshare stage API token")


@pytest.fixture(scope='session')
def figshare_api_key(request):
    name_value = request.config.option.figshare_api_key
    if name_value is None:
        pytest.skip()
    return name_value


@pytest.fixture(scope='session')
def figshare_stage_api_key(request):
    name_value = request.config.option.figshare_stage_api_key
    if name_value is None:
        pytest.skip()
    return name_value
