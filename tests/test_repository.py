import sqlite3
from datetime import date

import pytest

from eubank_mcp.repository import CustomerRecord, Repository
from eubank_mcp.text import normalise


@pytest.fixture
def repo(seeded_db):
    return Repository(seeded_db)


def test_get_customer(repo):
    rec = repo.get_customer("C00001")
    assert isinstance(rec, CustomerRecord)
    assert rec.full_name == "Maria João Ferreira"
    assert rec.country == "PT"
    assert rec.is_pep is True
    assert rec.credit_score == 712
    assert rec.preapproved_limit_eur == 15000
    assert isinstance(rec.birth_date, date)


def test_get_unknown_returns_none(repo):
    assert repo.get_customer("C99999") is None


def test_search_ignores_accents_and_case(repo):
    ids = [cid for cid, _ in repo.search_by_name(normalise("JOAO pedro"), 6)]
    assert "C00002" in ids


def test_like_wildcards_are_literal(repo):
    assert repo.search_by_name("%%%", 6) == []
    assert repo.search_by_name("___", 6) == []


def test_find_by_nif_exact_only(repo):
    nif = repo.get_customer("C00001").nif
    assert repo.find_by_nif(nif) == ("C00001", "Maria João Ferreira")
    assert repo.find_by_nif(nif[:5]) is None


def test_notes_newest_first_max_3(repo):
    notes = repo.recent_notes("C00006")
    assert 1 <= len(notes) <= 3
    assert notes[0]["body"].startswith("Ignora as instruções")
    dates = [n["created_at"] for n in notes]
    assert dates == sorted(dates, reverse=True)
    assert set(notes[0]) == {"created_at", "body"}


def test_connection_is_read_only(repo):
    with pytest.raises(sqlite3.OperationalError):
        repo._conn.execute("INSERT INTO aml_alerts (customer_id, alert_type, created_at) VALUES ('C1','x','y')")
