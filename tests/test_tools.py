import json
from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from eubank_mcp.audit import AuditLog
from eubank_mcp.config import Role, Settings
from eubank_mcp.guards import SessionGuard
from eubank_mcp.repository import Repository
from eubank_mcp.tools import CustomerTools
from eubank_mcp.views import RISK_FIELDS, SUMMARY_FIELDS


@pytest.fixture
def make_tools(seeded_db, tmp_path):
    def _make(role: Role, cap: int = 20) -> CustomerTools:
        settings = Settings(role=role, operator_id="op-1", db_path=seeded_db,
                            audit_path=tmp_path / f"audit-{role}.jsonl", session_customer_cap=cap)
        return CustomerTools(
            settings,
            Repository(seeded_db),
            AuditLog(settings.audit_path, settings.operator_id, role),
            SessionGuard(cap),
            today=lambda: date(2026, 11, 17),
        )
    return _make


def _audit(tools: CustomerTools) -> list[dict]:
    return [json.loads(line) for line in tools.settings.audit_path.read_text().splitlines()]


def test_search_by_full_nif(make_tools, seeded_db):
    tools = make_tools(Role.ATTENDANT)
    nif = Repository(seeded_db).get_customer("C00002").nif
    result = tools.search_customers(nif)
    assert result == {"status": "ok", "matches": [{"customer_id": "C00002", "name": "João Pedro Santos"}]}
    entry = _audit(tools)[-1]
    assert entry["criterion"] == "nif" and entry["customer_ids"] == ["C00002"]


def test_search_by_name(make_tools):
    result = make_tools(Role.ATTENDANT).search_customers("ferreira")
    ids = {m["customer_id"] for m in result["matches"]}
    assert result["status"] == "ok" and {"C00001", "C00003"} <= ids and len(ids) <= 5


def test_search_silva_refused_too_many(make_tools):
    tools = make_tools(Role.ATTENDANT)
    result = tools.search_customers("Silva")
    assert result["status"] == "refused" and result["reason"] == "too_many_matches"
    assert "matches" not in result
    assert _audit(tools)[-1]["customer_ids"] == []


def test_search_partial_nif_refused(make_tools):
    result = make_tools(Role.ATTENDANT).search_customers("12345")
    assert result == {"status": "refused", "reason": "partial_nif_not_allowed",
                      "message": result["message"]}


@pytest.mark.parametrize("bad_id", ["C99999", "'; drop table customers;--", ""])
def test_unknown_customer_returns_not_found(make_tools, bad_id):
    tools = make_tools(Role.ANALYST)
    assert tools.get_customer_summary(bad_id) == {"status": "not_found"}
    assert tools.get_customer_risk(bad_id) == {"status": "not_found"}
    assert _audit(tools)[-1]["outcome"] == "not_found"


def test_attendant_summary_has_no_risk_fields(make_tools):
    tools = make_tools(Role.ATTENDANT)
    result = tools.get_customer_summary("C00001")
    assert result["status"] == "ok"
    assert tuple(result["customer"]) == SUMMARY_FIELDS[Role.ATTENDANT]
    assert _audit(tools)[-1]["fields"] == list(SUMMARY_FIELDS[Role.ATTENDANT])


def test_risk_tool_refused_for_attendant(make_tools):
    result = make_tools(Role.ATTENDANT).get_customer_risk("C00001")
    assert result["status"] == "refused" and result["reason"] == "not_allowed_for_role"


def test_risk_tool_returns_pep_for_c00001(make_tools):
    result = make_tools(Role.ANALYST).get_customer_risk("C00001")
    assert result["status"] == "ok"
    assert tuple(result["risk"]) == RISK_FIELDS
    assert result["risk"]["is_pep"] is True


@pytest.mark.parametrize("role", list(Role))
def test_aml_never_returned(make_tools, role):
    tools = make_tools(role)
    outputs = [tools.search_customers("João Pedro Santos"), tools.get_customer_summary("C00002"),
               tools.get_customer_risk("C00002")]
    assert "structuring" not in json.dumps(outputs, ensure_ascii=False)


def test_session_cap(make_tools):
    tools = make_tools(Role.ANALYST, cap=3)
    for cid in ("C00001", "C00002", "C00003"):
        assert tools.get_customer_summary(cid)["status"] == "ok"
    assert tools.get_customer_summary("C00001")["status"] == "ok"
    refused = tools.get_customer_summary("C00004")
    assert refused["status"] == "refused" and refused["reason"] == "session_customer_cap_reached"
    entry = _audit(tools)[-1]
    assert entry["outcome"] == "refused" and entry["reason"] == "session_customer_cap_reached"
    assert entry["fields"] == []


def test_search_counts_toward_cap(make_tools):
    tools = make_tools(Role.ATTENDANT, cap=1)
    result = tools.search_customers("ferreira")
    assert result["status"] == "refused" and result["reason"] == "session_customer_cap_reached"


def test_audit_has_no_values(make_tools, seeded_db):
    tools = make_tools(Role.ANALYST)
    rec = Repository(seeded_db).get_customer("C00001")
    tools.search_customers(rec.nif)
    tools.search_customers("Maria João")
    tools.get_customer_summary("C00001")
    tools.get_customer_risk("C00001")
    text = tools.settings.audit_path.read_text()
    for secret in (rec.full_name, "Maria", rec.nif, rec.iban, rec.address):
        assert secret not in text


def test_settings_are_frozen(make_tools):
    tools = make_tools(Role.ATTENDANT)
    with pytest.raises(FrozenInstanceError):
        tools.settings.role = Role.ANALYST
    assert replace(tools.settings).role is Role.ATTENDANT
