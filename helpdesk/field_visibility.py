"""Which HD Ticket fields helpdesk's own pages show to customers and to agents.

Permission levels are the real boundary. The Default template's Visible to only
narrows them, and only here: raw framework queries ignore it.
"""

import frappe
from frappe.model import get_permitted_fields
from frappe.utils.caching import redis_cache

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import is_agent

# framework columns permission levels cannot cover; agent workflow data, so never
# shown to customers. _seen stays out: the portal list reads it for unread dots
AGENT_WORKFLOW_FIELDS = {"_assign", "_comments", "_liked_by", "_user_tags"}


def get_hidden_ticket_fields() -> set[str]:
    """Fields the session user must not see.

    Permlevel-unreadable fields, plus the Default template rows reserved for
    the other audience: agents lose the Customers rows, customers lose the
    Agents rows and the agent workflow columns.
    """
    if is_agent():
        tier = get_fields_visible_to("Customers")
    else:
        tier = get_fields_visible_to("Agents") | AGENT_WORKFLOW_FIELDS
    return get_unreadable_fields("HD Ticket") | tier


def get_unreadable_fields(doctype: str) -> set[str]:
    """Fields the user is unable to read because of perm levels."""
    permitted = set(get_permitted_fields(doctype))
    # fields that hold a value, so section and column breaks stay out of the set
    return {
        field.fieldname
        for field in frappe.get_meta(doctype).get_fieldnames_with_value(
            with_field_meta=True
        )
        if field.fieldname not in permitted
    }


@redis_cache()
def get_fields_visible_to(audience: str) -> set[str]:
    """helper which returns the set of fields according to the role passed

    audience is a Visible to value on the template row: Customers or Agents.
    Fields left at Everyone belong to neither set.
    """
    return set(
        frappe.get_all(
            "HD Ticket Template Field",
            pluck="fieldname",
            filters={
                "parent": DEFAULT_TICKET_TEMPLATE,
                "parenttype": "HD Ticket Template",
                "visible_to": audience,
            },
        )
    )
