import pytest

from eubank_mcp.guards import Refusal, SearchQuery, SessionGuard, parse_search


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123456789", SearchQuery("nif", "123456789")),
        ("12345", Refusal("partial_nif_not_allowed")),
        ("Jo", Refusal("query_too_short")),
        ("  João ", SearchQuery("name", "joao")),
        ("", Refusal("query_too_short")),
    ],
)
def test_parse_search(raw, expected):
    assert parse_search(raw) == expected


def test_wildcard_only_query_refused():
    assert parse_search("%%%") == Refusal("query_too_short")
    assert parse_search("_%_ a") == Refusal("query_too_short")


def test_session_guard_counts_distinct_customers():
    guard = SessionGuard(cap=3)
    assert guard.admit(["C1", "C2"]) is None
    assert guard.admit(["C1"]) is None
    assert guard.admit(["C3", "C4"]) == Refusal("session_customer_cap_reached")
    assert guard.admit(["C3"]) is None
    assert guard.admit(["C4"]) == Refusal("session_customer_cap_reached")


@pytest.mark.parametrize("raw", ["z\x00abc", "ra\x00xyz", "ana\tsilva", "ana\x1bx"])
def test_control_characters_refused(raw):
    assert parse_search(raw) == Refusal("invalid_characters")


def test_long_query_refused():
    assert parse_search("a" * 101) == Refusal("query_too_long")
    assert parse_search("a" * 100) == SearchQuery("name", "a" * 100)
