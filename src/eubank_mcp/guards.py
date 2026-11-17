"""Rules that limit what a session can pull out of the database.

- Search by part of a name (at least 3 letters) or by a complete NIF only.
  A partial NIF is refused: with results capped at 5, narrowing digits one
  at a time would reveal a full NIF.
- Each server session may touch at most N distinct customers, so the base
  cannot be listed a few rows at a time.
"""

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from eubank_mcp.text import normalise

NIF_LENGTH = 9
MIN_NAME_LETTERS = 3
MAX_QUERY_LENGTH = 100


@dataclass(frozen=True)
class Refusal:
    reason: str


@dataclass(frozen=True)
class SearchQuery:
    kind: Literal["name", "nif"]
    value: str


def parse_search(raw: str) -> SearchQuery | Refusal:
    if len(raw) > MAX_QUERY_LENGTH:
        return Refusal("query_too_long")
    value = raw.strip()
    # Control characters (NUL truncates SQLite LIKE patterns, which would bypass the letter minimum).
    if any(unicodedata.category(c).startswith("C") for c in value):
        return Refusal("invalid_characters")
    if value.isdigit():
        if len(value) == NIF_LENGTH:
            return SearchQuery("nif", value)
        return Refusal("partial_nif_not_allowed")
    name = normalise(value)
    if sum(c.isalpha() for c in name) < MIN_NAME_LETTERS:
        return Refusal("query_too_short")
    return SearchQuery("name", name)


class SessionGuard:
    def __init__(self, cap: int):
        self._cap = cap
        self._seen: set[str] = set()

    def admit(self, customer_ids: Iterable[str]) -> Refusal | None:
        new = set(customer_ids) - self._seen
        if len(self._seen) + len(new) > self._cap:
            return Refusal("session_customer_cap_reached")
        self._seen |= new
        return None
