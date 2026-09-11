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


def hidden_ticket_fields() -> set[str]:
    """get fields which are to be hidden as per the user role category"""
    if is_agent():
        # if agent is requesting the hidden fields will be that for customers
        return fields_only_for("Customers")
    return fields_only_for("Agents") | AGENT_WORKFLOW_FIELDS


@redis_cache()
def fields_only_for(audience: str) -> set[str]:
    """helper which returns the set of fields according to the role passed"""
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
