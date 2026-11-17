import pytest

from eubank_mcp.seed import build_database


@pytest.fixture(scope="session")
def behaviour_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("behaviour") / "eubank.db"
    build_database(path)
    return path


@pytest.fixture
def anyio_backend():
    return "asyncio"
