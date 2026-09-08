"""Per-role display visibility for HD Ticket fields, layered over permission levels.
The Default template's tiers only narrow what levels allow; raw framework queries ignore them.
"""

import frappe
from frappe.utils.caching import redis_cache

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE

VISIBILITY_RANKS = {
    "Everyone": 0,
    "Agents and above": 1,
    "Agent Managers and above": 2,
    "System Managers only": 3,
}

# framework columns permission levels cannot cover; agent workflow data, so hidden
# from customers. _seen stays out: the portal list reads it for unread dots
STAFF_STANDARD_FIELDS = frozenset({"_assign", "_comments", "_liked_by", "_user_tags"})


class TicketFieldVisibility:
    """Answers: may `user` see this HD Ticket field on helpdesk pages."""

    def __init__(self, user: str | None = None):
        self.user = user or frappe.session.user
        self.rank = user_rank(self.user)

    def is_readable(self, fieldname: str) -> bool:
        return fieldname not in self.hidden_fields()

    def hidden_fields(self) -> set[str]:
        hidden = {f for f, tier in get_field_tiers().items() if tier > self.rank}
        if not self.rank:
            hidden |= STAFF_STANDARD_FIELDS
        return hidden

    def filter_fieldnames(self, fieldnames: list[str]) -> list[str]:
        return [f for f in fieldnames if self.is_readable(f)]

    def filter_field_dicts(self, fields: list[dict], key: str) -> list[dict]:
        return [f for f in fields if self.is_readable(f.get(key))]

    def filter_template_rows(self, rows: list[dict]) -> list[dict]:
        # judged against the Default tier map, not the row's own visible_to
        return self.filter_field_dicts(rows, key="fieldname")

    def strip(self, ticket) -> None:
        """Blank hidden fields, the same shape the permission-level strip produces."""
        for fieldname in self.hidden_fields():
            if hasattr(ticket, fieldname):
                ticket.set(fieldname, None)


def user_rank(user: str) -> int:
    # not is_agent(): it answers for the session user, not the one asked about
    roles = frappe.get_roles(user)
    if "System Manager" in roles:
        return VISIBILITY_RANKS["System Managers only"]
    if "Agent Manager" in roles:
        return VISIBILITY_RANKS["Agent Managers and above"]
    if "Agent" in roles or frappe.db.exists("HD Agent", {"name": user}):
        return VISIBILITY_RANKS["Agents and above"]
    return VISIBILITY_RANKS["Everyone"]


@redis_cache
def get_field_tiers() -> dict[str, int]:
    """fieldname -> minimum rank that may see it, from the Default template."""
    rows = frappe.get_all(
        "HD Ticket Template Field",
        filters={
            "parenttype": "HD Ticket Template",
            "parent": DEFAULT_TICKET_TEMPLATE,
            "parentfield": "fields",
        },
        fields=["fieldname", "visible_to", "hide_from_customer"],
    )
    return {row.fieldname: row_tier(row) for row in rows if row.fieldname}


def row_tier(row) -> int:
    # a blank or unrecognised tier falls back to the old flag
    tier = VISIBILITY_RANKS.get(row.get("visible_to"))
    if tier is not None:
        return tier
    if row.get("hide_from_customer"):
        return VISIBILITY_RANKS["Agents and above"]
    return VISIBILITY_RANKS["Everyone"]
