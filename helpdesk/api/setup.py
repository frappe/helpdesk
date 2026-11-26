import frappe
from frappe.integrations.frappe_providers.cloud_settings import is_v2_site

from helpdesk.setup.welcome_ticket import AUTHOR_EMAIl as WELCOME_TICKET_AUTHOR

SETUP_ROLE = "System Manager"


def is_setup_pending() -> bool:
    """The first-run setup is for a System Manager on a Frappe Cloud v2 site, until it ends."""
    return (
        SETUP_ROLE in frappe.get_roles()
        and is_v2_site()
        and not frappe.db.get_single_value("HD Settings", "setup_complete")
    )


@frappe.whitelist(methods=["POST"])
def complete_setup() -> str | None:
    """Ends the first-run setup, on Finish or Skip. A second call is a no-op.
    Returns the welcome ticket, for the desk to open first."""
    frappe.only_for(SETUP_ROLE)
    frappe.db.set_single_value("HD Settings", "setup_complete", 1)
    return frappe.db.get_value(
        "HD Ticket",
        {"raised_by": WELCOME_TICKET_AUTHOR},
        "name",
        order_by="creation asc",
    )
