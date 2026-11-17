"""Tool logic, independent of MCP so it can be unit-tested directly.

Every call is audited exactly once, and every customer id is admitted by
the session guard before any data about it is returned.
"""

import functools
from collections.abc import Callable
from datetime import date

from eubank_mcp.audit import AuditLog, Outcome
from eubank_mcp.config import Role, Settings
from eubank_mcp.guards import Refusal, SessionGuard, parse_search
from eubank_mcp.models import (
    AnalystSummaryResult,
    AttendantSummaryResult,
    Match,
    NotFound,
    Refused,
    RiskResult,
    SearchResult,
    SummaryResult,
)
from eubank_mcp.repository import Repository
from eubank_mcp.views import RISK_FIELDS, SUMMARY_FIELDS, risk_view, summary_view

MAX_MATCHES = 5

REFUSAL_MESSAGES = {
    "partial_nif_not_allowed": "Search by the complete 9-digit NIF or by at least 3 letters of the name.",
    "query_too_short": "Search by at least 3 letters of the customer's name or by the complete NIF.",
    "too_many_matches": "Refine the search: more than 5 customers match.",
    "session_customer_cap_reached": (
        "This session has reached its limit of distinct customers. Bulk listing is not available."
    ),
    "not_allowed_for_role": "This information is not available for your role.",
    "query_too_long": "The search term is too long.",
    "invalid_characters": "The search term contains invalid characters.",
}


def _audit_errors(tool: str):
    """Record an "error" audit line for any unexpected failure, then re-raise it."""
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)
            except Exception:
                self._audit.record(tool, "error")
                raise
        return wrapper
    return decorator


def _normalise_id(customer_id: str) -> str:
    return customer_id.strip().upper()


def _refused(reason: str) -> Refused:
    return Refused(reason=reason, message=REFUSAL_MESSAGES[reason])


class CustomerTools:
    def __init__(
        self,
        settings: Settings,
        repo: Repository,
        audit: AuditLog,
        guard: SessionGuard,
        today: Callable[[], date] = date.today,
    ):
        self.settings = settings
        self._repo = repo
        self._audit = audit
        self._guard = guard
        self._today = today

    def _refuse(self, tool: str, reason: str, customer_ids=(), criterion=None) -> Refused:
        self._audit.record(tool, "refused", customer_ids=customer_ids, criterion=criterion, reason=reason)
        return _refused(reason)

    def _done(self, tool: str, outcome: Outcome, result, customer_ids=(), fields=(), criterion=None):
        self._audit.record(tool, outcome, customer_ids=customer_ids, fields=fields, criterion=criterion)
        return result

    @_audit_errors("search_customers")
    def search_customers(self, query: str) -> SearchResult | Refused:
        tool = "search_customers"
        parsed = parse_search(query)
        if isinstance(parsed, Refusal):
            return self._refuse(tool, parsed.reason)

        if parsed.kind == "nif":
            hit = self._repo.find_by_nif(parsed.value)
            matches = [hit] if hit else []
        else:
            matches = self._repo.search_by_name(parsed.value, MAX_MATCHES + 1)
            if len(matches) > MAX_MATCHES:
                return self._refuse(tool, "too_many_matches", criterion=parsed.kind)

        ids = [cid for cid, _ in matches]
        refusal = self._guard.admit(ids)
        if refusal:
            # Nothing was returned, so no customer ids are logged as seen.
            return self._refuse(tool, refusal.reason, criterion=parsed.kind)
        result = SearchResult(matches=[Match(customer_id=cid, name=name) for cid, name in matches])
        return self._done(tool, "ok", result, customer_ids=ids, fields=("customer_id", "name"),
                          criterion=parsed.kind)

    @_audit_errors("get_customer_summary")
    def get_customer_summary(self, customer_id: str) -> SummaryResult | NotFound | Refused:
        tool = "get_customer_summary"
        rec = self._repo.get_customer(_normalise_id(customer_id))
        if rec is None:
            return self._done(tool, "not_found", NotFound())
        refusal = self._guard.admit([rec.customer_id])
        if refusal:
            return self._refuse(tool, refusal.reason, customer_ids=[rec.customer_id])
        role = self.settings.role
        view = summary_view(rec, self._repo.recent_notes(rec.customer_id), role, self._today())
        result_type = AnalystSummaryResult if role is Role.ANALYST else AttendantSummaryResult
        return self._done(tool, "ok", result_type(customer=view),
                          customer_ids=[rec.customer_id], fields=SUMMARY_FIELDS[role])

    @_audit_errors("get_customer_risk")
    def get_customer_risk(self, customer_id: str) -> RiskResult | NotFound | Refused:
        tool = "get_customer_risk"
        # The server does not register this tool for attendants; this check is a second line.
        if self.settings.role is not Role.ANALYST:
            return self._refuse(tool, "not_allowed_for_role")
        rec = self._repo.get_customer(_normalise_id(customer_id))
        if rec is None:
            return self._done(tool, "not_found", NotFound())
        refusal = self._guard.admit([rec.customer_id])
        if refusal:
            return self._refuse(tool, refusal.reason, customer_ids=[rec.customer_id])
        return self._done(tool, "ok", RiskResult(risk=risk_view(rec)),
                          customer_ids=[rec.customer_id], fields=RISK_FIELDS)
