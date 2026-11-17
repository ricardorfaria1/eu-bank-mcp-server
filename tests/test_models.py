import pytest
from pydantic import ValidationError

from eubank_mcp.config import Role
from eubank_mcp.models import AnalystSummary, AttendantSummary, CustomerRisk, Refused
from eubank_mcp.views import RISK_FIELDS, SUMMARY_FIELDS


def test_field_lists_come_from_models():
    assert SUMMARY_FIELDS[Role.ATTENDANT] == tuple(AttendantSummary.model_fields)
    assert SUMMARY_FIELDS[Role.ANALYST] == tuple(AnalystSummary.model_fields)
    assert RISK_FIELDS == tuple(CustomerRisk.model_fields)


def test_attendant_model_has_no_risk_or_location_fields():
    names = set(AttendantSummary.model_fields)
    assert not names & {"age", "country", "credit_score", "risk_profile", "kyc_status", "is_pep"}


def test_models_reject_unknown_fields():
    with pytest.raises(ValidationError):
        AttendantSummary(customer_id="C1", name="x", nif_masked="***", iban_masked="PT**", preapproved_limit_eur=1,
                         recent_notes=[], is_pep=True)


def test_refused_requires_known_reason():
    with pytest.raises(ValidationError):
        Refused(reason="made_up", message="x")
