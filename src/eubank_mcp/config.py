"""Server settings, read once from environment variables at startup.

The role and operator id come only from here. No tool can change them.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Role(StrEnum):
    ATTENDANT = "attendant"
    ANALYST = "analyst"


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid server setup."""


@dataclass(frozen=True)
class Settings:
    role: Role
    operator_id: str
    db_path: Path
    audit_path: Path
    session_customer_cap: int = 20


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    raw_role = env.get("EUBANK_ROLE", "")
    try:
        role = Role(raw_role)
    except ValueError:
        allowed = ", ".join(r.value for r in Role)
        raise ConfigError(f"EUBANK_ROLE must be one of: {allowed} (got {raw_role!r})") from None

    operator_id = env.get("EUBANK_OPERATOR_ID", "").strip()
    if not operator_id:
        raise ConfigError("EUBANK_OPERATOR_ID must be set to the id of the staff member using the server")

    db_path = Path(env.get("EUBANK_DB_PATH", "data/eubank.db"))
    if not db_path.is_file():
        raise ConfigError(f"Database not found at {db_path}. Run `uv run eubank-seed` first.")

    audit_path = Path(env.get("EUBANK_AUDIT_PATH", "data/audit.jsonl"))
    return Settings(role=role, operator_id=operator_id, db_path=db_path, audit_path=audit_path)
