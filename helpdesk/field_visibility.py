"""Role-based field visibility for HD Ticket, on top of permission levels.

Permission levels are the security floor: the framework strips what a user
may not read on every path. The Default ticket template's rows narrow that
further for helpdesk's own pages — each row's `visible_to` names the minimum
role that may see the field, on the fixed ladder customer < Agent < Agent
Manager < System Manager. Templates never widen access and never write
permission levels; a field the template does not list is untouched.

Enforced only at helpdesk level: the HDTicket controller's
`apply_fieldlevel_read_permissions` override and helpdesk's own endpoints.
Raw framework queries answer to permission levels alone.
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

# framework-managed columns permission levels cannot cover: they are not
# DocFields, and get_permitted_fields hands them to every reader. Agent
# workflow data, so customers never see them. _seen stays out of this set —
# the portal list parses it for unread dots.
STAFF_STANDARD_FIELDS = frozenset({"_assign", "_comments", "_liked_by", "_user_tags"})


class TicketFieldVisibility:
    """Answers: may `user` see this HD Ticket field on helpdesk pages."""

    def __init__(self, user: str | None = None):
        self.user = user or frappe.session.user
        self.rank = user_rank(self.user)

    def is_readable(self, fieldname: str) -> bool:
        return fieldname not in self.hidden_fields()

    def hidden_fields(self) -> set[str]:
        """Template rows tiered above the user's rank, plus the framework's
        agent-workflow columns for customers; everything else is left to
        permission levels."""
        hidden = {f for f, tier in get_field_tiers().items() if tier > self.rank}
        if not self.rank:
            hidden |= STAFF_STANDARD_FIELDS
        return hidden

    def filter_fieldnames(self, fieldnames: list[str]) -> list[str]:
        return [f for f in fieldnames if self.is_readable(f)]

    def filter_field_dicts(self, fields: list[dict], key: str) -> list[dict]:
        return [f for f in fields if self.is_readable(f.get(key))]

    def filter_template_rows(self, rows: list[dict]) -> list[dict]:
        # judged against the Default tier map, not the row's own visible_to:
        # the Default template is the one source of visibility rules
        return self.filter_field_dicts(rows, key="fieldname")

    def strip(self, ticket) -> None:
        """Blank the fields the user may not see; serializers then return
        them empty, the same shape the permission-level strip produces."""
        for fieldname in self.hidden_fields():
            if hasattr(ticket, fieldname):
                ticket.set(fieldname, None)


def user_rank(user: str) -> int:
    # judged from the user's own roles, not is_agent(): that helper answers
    # for the session user when an Administrator asks about someone else
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
    """fieldname -> minimum rank that may see it, from the Default template.
    Matched by fieldname because template saves replace child rows wholesale."""
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
    # a blank or unrecognised visible_to falls back to the old flag, so rows
    # saved before the tier column (or before a label rename) keep working
    tier = VISIBILITY_RANKS.get(row.get("visible_to"))
    if tier is not None:
        return tier
    if row.get("hide_from_customer"):
        return VISIBILITY_RANKS["Agents and above"]
    return VISIBILITY_RANKS["Everyone"]
