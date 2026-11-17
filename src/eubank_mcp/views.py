"""What each role is allowed to see.

The models in models.py define the fields that leave the server.
SUMMARY_FIELDS and RISK_FIELDS are derived from them for the audit log.
"""

from datetime import date

from eubank_mcp.config import Role
from eubank_mcp.models import AnalystSummary, AttendantSummary, CustomerRisk, Note
from eubank_mcp.repository import CustomerRecord

SUMMARY_MODELS: dict[Role, type[AttendantSummary]] = {
    Role.ATTENDANT: AttendantSummary,
    Role.ANALYST: AnalystSummary,
}

SUMMARY_FIELDS: dict[Role, tuple[str, ...]] = {role: tuple(m.model_fields) for role, m in SUMMARY_MODELS.items()}

RISK_FIELDS: tuple[str, ...] = tuple(CustomerRisk.model_fields)


def mask_iban(iban: str) -> str:
    return f"{iban[:2]}** **** {iban[-4:]}"


def mask_nif(nif: str) -> str:
    return "*" * (len(nif) - 3) + nif[-3:]


def age_on(birth: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (birth.month, birth.day)
    return today.year - birth.year - (0 if had_birthday else 1)


def summary_view(rec: CustomerRecord, notes: list[dict], role: Role, today: date) -> AttendantSummary:
    available = {
        "customer_id": rec.customer_id,
        "name": rec.full_name,
        "nif_masked": mask_nif(rec.nif),
        "iban_masked": mask_iban(rec.iban),
        "preapproved_limit_eur": rec.preapproved_limit_eur,
        "recent_notes": [Note(**n) for n in notes],
        "age": age_on(rec.birth_date, today),
        "country": rec.country,
    }
    return SUMMARY_MODELS[role](**{key: available[key] for key in SUMMARY_FIELDS[role]})


def risk_view(rec: CustomerRecord) -> CustomerRisk:
    return CustomerRisk(
        customer_id=rec.customer_id,
        credit_score=rec.credit_score,
        risk_profile=rec.risk_profile,
        kyc_status=rec.kyc_status,
        is_pep=rec.is_pep,
    )
