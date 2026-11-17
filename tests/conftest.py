import pytest

from eubank_mcp.seed import build_database


@pytest.fixture(scope="session")
def seeded_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "eubank.db"
    build_database(path)
    return path
