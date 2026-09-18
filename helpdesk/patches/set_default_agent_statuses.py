import frappe

from helpdesk.helpdesk.doctype.hd_agent_status.hd_agent_status import (
    get_default_agent_status,
)
from helpdesk.setup.install import add_default_agent_status


def execute():
    """Add the default HD Agent Status records on sites that predate the feature,
    and set the Active status on existing agents whose availability is unset or invalid.
    """
    add_default_agent_status()

    default_status = get_default_agent_status()

    valid_statuses = frappe.get_all("HD Agent Status", pluck="name")
    agents = frappe.get_all(
        "HD Agent",
        or_filters=[
            ["availability", "is", "not set"],
            ["availability", "=", ""],
            ["availability", "not in", valid_statuses],
        ],
        pluck="name",
    )
    if agents:
        frappe.db.set_value(
            "HD Agent",
            {"name": ["in", agents]},
            "availability",
            default_status,
            update_modified=False,
        )
