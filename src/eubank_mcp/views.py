"""What each role is allowed to see.

SUMMARY_FIELDS and RISK_FIELDS are the single source of truth for the
fields that leave the server. The audit log and the README use them too.
"""

from datetime import date

from eubank_mcp.config import Role
from eubank_mcp.repository import CustomerRecord

_COMMON = ("customer_id", "name", "nif_masked", "iban_masked", "preapproved_limit_eur", "recent_notes")

SUMMARY_FIELDS: dict[Role, tuple[str, ...]] = {
    Role.ATTENDANT: _COMMON,
    Role.ANALYST: _COMMON + ("age", "country"),
}

RISK_FIELDS: tuple[str, ...] = ("customer_id", "credit_score", "risk_profile", "kyc_status", "is_pep")


def mask_iban(iban: str) -> str:
    return f"{iban[:2]}** **** {iban[-4:]}"


def mask_nif(nif: str) -> str:
    return "*" * (len(nif) - 3) + nif[-3:]


def age_on(birth: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (birth.month, birth.day)
    return today.year - birth.year - (0 if had_birthday else 1)


def summary_view(rec: CustomerRecord, notes: list[dict], role: Role, today: date) -> dict:
    available = {
        "customer_id": rec.customer_id,
        "name": rec.full_name,
        "nif_masked": mask_nif(rec.nif),
        "iban_masked": mask_iban(rec.iban),
        "preapproved_limit_eur": rec.preapproved_limit_eur,
        "recent_notes": notes,
        "age": age_on(rec.birth_date, today),
        "country": rec.country,
    }
    return {key: available[key] for key in SUMMARY_FIELDS[role]}


def risk_view(rec: CustomerRecord) -> dict:
    available = {
        "customer_id": rec.customer_id,
        "credit_score": rec.credit_score,
        "risk_profile": rec.risk_profile,
        "kyc_status": rec.kyc_status,
        "is_pep": rec.is_pep,
    }
    return {key: available[key] for key in RISK_FIELDS}
