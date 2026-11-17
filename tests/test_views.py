import json
from datetime import date

import pytest

from eubank_mcp.config import Role
from eubank_mcp.repository import Repository
from eubank_mcp.views import (
    RISK_FIELDS,
    SUMMARY_FIELDS,
    age_on,
    mask_iban,
    mask_nif,
    risk_view,
    summary_view,
)

TODAY = date(2026, 11, 17)


@pytest.fixture
def maria(seeded_db):
    repo = Repository(seeded_db)
    return repo.get_customer("C00001"), repo.recent_notes("C00001")


def test_mask_iban():
    assert mask_iban("PT50000201231234567890154") == "PT** **** 0154"


def test_mask_nif():
    assert mask_nif("123456789") == "******789"


def test_age_on_day_before_birthday():
    assert age_on(date(1990, 6, 15), date(2026, 6, 14)) == 35
    assert age_on(date(1990, 6, 15), date(2026, 6, 15)) == 36


def test_attendant_summary_keys(maria):
    rec, notes = maria
    view = summary_view(rec, notes, Role.ATTENDANT, TODAY)
    assert tuple(view) == SUMMARY_FIELDS[Role.ATTENDANT]
    values = json.dumps(view, ensure_ascii=False)
    for secret in (rec.nif, rec.iban, rec.address, rec.birth_date.isoformat()):
        assert secret not in values


def test_analyst_summary_keys(maria):
    rec, notes = maria
    view = summary_view(rec, notes, Role.ANALYST, TODAY)
    assert tuple(view) == SUMMARY_FIELDS[Role.ANALYST]
    assert view["country"] == "PT"
    assert isinstance(view["age"], int)
    values = json.dumps(view, ensure_ascii=False)
    for secret in (rec.nif, rec.iban, rec.address, rec.birth_date.isoformat()):
        assert secret not in values


def test_no_view_contains_aml_or_pep_for_attendant(maria):
    rec, notes = maria
    keys = " ".join(summary_view(rec, notes, Role.ATTENDANT, TODAY)).lower()
    for word in ("pep", "kyc", "aml", "risk", "score"):
        assert word not in keys


def test_risk_view(maria):
    rec, _ = maria
    view = risk_view(rec)
    assert tuple(view) == RISK_FIELDS
    assert view["is_pep"] is True
    assert view["credit_score"] == 712
