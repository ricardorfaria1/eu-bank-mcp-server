import pytest

from eubank_mcp.config import ConfigError, Role, load_settings


def _env(db, **overrides):
    env = {"EUBANK_ROLE": "attendant", "EUBANK_OPERATOR_ID": "op-1", "EUBANK_DB_PATH": str(db)}
    env.update(overrides)
    return env


def test_valid_settings(tmp_path):
    db = tmp_path / "x.db"
    db.touch()
    s = load_settings(_env(db, EUBANK_ROLE="analyst", EUBANK_OPERATOR_ID="op-17"))
    assert s.role is Role.ANALYST
    assert s.operator_id == "op-17"
    assert s.session_customer_cap == 20


def test_invalid_role_rejected(tmp_path):
    db = tmp_path / "x.db"
    db.touch()
    with pytest.raises(ConfigError, match="EUBANK_ROLE"):
        load_settings(_env(db, EUBANK_ROLE="admin"))


@pytest.mark.parametrize("operator", ["", "   ", None])
def test_missing_operator_rejected(tmp_path, operator):
    db = tmp_path / "x.db"
    db.touch()
    env = _env(db)
    if operator is None:
        del env["EUBANK_OPERATOR_ID"]
    else:
        env["EUBANK_OPERATOR_ID"] = operator
    with pytest.raises(ConfigError, match="EUBANK_OPERATOR_ID"):
        load_settings(env)


def test_missing_db_rejected(tmp_path):
    with pytest.raises(ConfigError, match="eubank-seed"):
        load_settings(_env(tmp_path / "nope.db"))
