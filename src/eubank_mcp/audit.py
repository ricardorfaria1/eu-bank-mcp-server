"""Append-only audit log, one JSON object per line.

It records who looked at which customers and which field names left the
server. It never records field values or search terms, which are personal
data. record() has no parameter that could carry them.
"""

import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from eubank_mcp.config import Role

Outcome = Literal["ok", "refused", "not_found", "error"]


class AuditLog:
    def __init__(self, path: Path, operator_id: str, role: Role):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._operator_id = operator_id
        self._role = role

    def record(
        self,
        tool: str,
        outcome: Outcome,
        customer_ids: Sequence[str] = (),
        fields: Sequence[str] = (),
        criterion: Literal["name", "nif"] | None = None,
        reason: str | None = None,
    ) -> None:
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "operator_id": self._operator_id,
            "role": self._role.value,
            "tool": tool,
            "outcome": outcome,
            "customer_ids": list(customer_ids),
            "fields": list(fields),
            "criterion": criterion,
            "reason": reason,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
