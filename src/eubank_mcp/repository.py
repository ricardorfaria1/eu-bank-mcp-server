"""Read-only access to the customer database.

The connection is opened with SQLite's read-only URI mode, so a write fails
at the database level whatever the caller does. No method reads aml_alerts.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class CustomerRecord:
    customer_id: str
    full_name: str
    nif: str
    birth_date: date
    address: str
    country: str
    iban: str
    credit_score: int
    preapproved_limit_eur: int
    risk_profile: str
    kyc_status: str
    is_pep: bool


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class Repository:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True,
                                     check_same_thread=False)

    def search_by_name(self, normalised_term: str, limit: int) -> list[tuple[str, str]]:
        rows = self._conn.execute(
            "SELECT customer_id, full_name FROM customers "
            "WHERE name_search LIKE ? ESCAPE '\\' ORDER BY customer_id LIMIT ?",
            (f"%{_escape_like(normalised_term)}%", limit),
        ).fetchall()
        return [(cid, name) for cid, name in rows]

    def find_by_nif(self, nif: str) -> tuple[str, str] | None:
        row = self._conn.execute(
            "SELECT customer_id, full_name FROM customers WHERE nif = ?", (nif,)
        ).fetchone()
        return (row[0], row[1]) if row else None

    def get_customer(self, customer_id: str) -> CustomerRecord | None:
        row = self._conn.execute(
            "SELECT c.customer_id, c.full_name, c.nif, c.birth_date, c.address, c.country, c.iban, "
            "cr.credit_score, cr.preapproved_limit_eur, r.risk_profile, r.kyc_status, r.is_pep "
            "FROM customers c JOIN credit cr USING (customer_id) JOIN risk r USING (customer_id) "
            "WHERE c.customer_id = ?",
            (customer_id,),
        ).fetchone()
        if row is None:
            return None
        return CustomerRecord(
            customer_id=row[0], full_name=row[1], nif=row[2], birth_date=date.fromisoformat(row[3]),
            address=row[4], country=row[5], iban=row[6], credit_score=row[7],
            preapproved_limit_eur=row[8], risk_profile=row[9], kyc_status=row[10], is_pep=bool(row[11]),
        )

    def recent_notes(self, customer_id: str, limit: int = 3) -> list[dict]:
        rows = self._conn.execute(
            "SELECT created_at, body FROM service_notes WHERE customer_id = ? "
            "ORDER BY created_at DESC, note_id DESC LIMIT ?",
            (customer_id, limit),
        ).fetchall()
        return [{"created_at": created_at, "body": body} for created_at, body in rows]
