"""Per-audience display visibility for HD Ticket fields, layered over permission levels.
The Default template's visible_to only narrows what levels allow; raw framework queries
ignore it."""

import frappe
from frappe.utils.caching import redis_cache

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import is_agent_staff

CUSTOMER = "customer"
AGENT = "agent"

# visible_to option -> who sees the field on helpdesk pages
VISIBLE_TO_AUDIENCES = {
    "Everyone": frozenset({CUSTOMER, AGENT}),
    "Customers": frozenset({CUSTOMER}),
    "Agents": frozenset({AGENT}),
}

# framework columns permission levels cannot cover; agent workflow data, so hidden
# from customers. _seen stays out: the portal list reads it for unread dots
STAFF_STANDARD_FIELDS = frozenset({"_assign", "_comments", "_liked_by", "_user_tags"})


class TicketFieldVisibility:
    """Answers: may the current user see this HD Ticket field on helpdesk pages."""

    def __init__(self):
        self.audience = AGENT if is_agent_staff() else CUSTOMER

    def is_readable(self, fieldname: str) -> bool:
        return fieldname not in self.hidden_fields()

    def hidden_fields(self) -> set[str]:
        hidden = {
            f
            for f, seen_by in get_field_audiences().items()
            if self.audience not in seen_by
        }
        if self.audience == CUSTOMER:
            hidden |= STAFF_STANDARD_FIELDS
        return hidden

    def filter_fieldnames(self, fieldnames: list[str]) -> list[str]:
        return [f for f in fieldnames if self.is_readable(f)]

    def filter_field_dicts(self, fields: list[dict], key: str) -> list[dict]:
        return [f for f in fields if self.is_readable(f.get(key))]

    def filter_template_rows(self, rows: list[dict]) -> list[dict]:
        # judged against the Default template, not the row's own visible_to
        return self.filter_field_dicts(rows, key="fieldname")

    def strip(self, ticket) -> None:
        """Blank hidden fields, the same shape the permission-level strip produces."""
        for fieldname in self.hidden_fields():
            if hasattr(ticket, fieldname):
                ticket.set(fieldname, None)


@redis_cache
def get_field_audiences() -> dict[str, frozenset]:
    """fieldname -> who may see it, from the Default template."""
    rows = frappe.get_all(
        "HD Ticket Template Field",
        filters={
            "parenttype": "HD Ticket Template",
            "parent": DEFAULT_TICKET_TEMPLATE,
            "parentfield": "fields",
        },
        fields=["fieldname", "visible_to", "hide_from_customer"],
    )
    return {row.fieldname: row_audiences(row) for row in rows if row.fieldname}


def row_audiences(row) -> frozenset:
    # a blank or unrecognised visible_to falls back to the old flag
    seen_by = VISIBLE_TO_AUDIENCES.get(row.get("visible_to"))
    if seen_by is not None:
        return seen_by
    return VISIBLE_TO_AUDIENCES[
        "Agents" if row.get("hide_from_customer") else "Everyone"
    ]
