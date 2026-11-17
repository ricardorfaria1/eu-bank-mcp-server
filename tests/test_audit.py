import inspect
import json

from eubank_mcp.audit import AuditLog
from eubank_mcp.config import Role

KEYS = {"ts", "operator_id", "role", "tool", "outcome", "customer_ids", "fields", "criterion", "reason"}


def test_records_are_json_lines(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path, operator_id="op-7", role=Role.ANALYST)
    log.record("get_customer_summary", "ok", customer_ids=["C00001"], fields=["name", "age"])
    log.record("search_customers", "refused", criterion="name", reason="too_many_matches")
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    first, second = (json.loads(line) for line in lines)
    assert set(first) == KEYS
    assert first["operator_id"] == "op-7" and first["role"] == "analyst"
    assert first["customer_ids"] == ["C00001"] and first["fields"] == ["name", "age"]
    assert second["outcome"] == "refused" and second["criterion"] == "name"


def test_record_cannot_take_values_or_search_terms():
    params = set(inspect.signature(AuditLog.record).parameters)
    assert params == {"self", "tool", "outcome", "customer_ids", "fields", "criterion", "reason"}
