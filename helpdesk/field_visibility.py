"""Which HD Ticket fields helpdesk's own pages show to customers and to agents.

Permission levels are the real boundary. The Default template's Visible to only
narrows them, and only here: raw framework queries ignore it.
"""

import frappe
from frappe.utils.caching import redis_cache

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import is_agent

# framework columns permission levels cannot cover; agent workflow data, so never
# shown to customers. _seen stays out: the portal list reads it for unread dots
AGENT_WORKFLOW_FIELDS = {"_assign", "_comments", "_liked_by", "_user_tags"}


def get_hidden_ticket_fields() -> set[str]:
    """Fields the session user must not see.

    Permlevel-unreadable fields, plus what the Default template hides from
    the user's audience.
    """
    meta = frappe.get_meta("HD Ticket")
    readable = meta.get_permlevel_access("read")
    unreadable = {
        df.fieldname
        for df in meta.get_high_permlevel_fields()
        if df.permlevel not in readable
    }
    audience = "Agents" if is_agent() else "Customers"
    return unreadable | get_template_hidden_fields(audience)


@redis_cache()
def get_template_hidden_fields(audience: str) -> set[str]:
    """What the Default template hides from `audience`: Agents or Customers.

    Rows reserved for the other audience, plus the agent workflow columns for
    customers. Rows left at Everyone are hidden from no one.
    """
    other = "Customers" if audience == "Agents" else "Agents"
    hidden = set(
        frappe.get_all(
            "HD Ticket Template Field",
            pluck="fieldname",
            filters={
                "parent": DEFAULT_TICKET_TEMPLATE,
                "parenttype": "HD Ticket Template",
                "visible_to": other,
            },
        )
    )
    if audience == "Customers":
        hidden |= AGENT_WORKFLOW_FIELDS
    return hidden


def get_customer_visible_template_fields() -> list[str]:
    """Default template fieldnames not reserved for agents."""
    rows = frappe.get_all(
        "HD Ticket Template Field",
        filters={
            "parent": DEFAULT_TICKET_TEMPLATE,
            "parenttype": "HD Ticket Template",
        },
        fields=["fieldname", "visible_to"],
    )
    return [row.fieldname for row in rows if row.visible_to != "Agents"]
