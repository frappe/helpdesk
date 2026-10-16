import frappe

from helpdesk.helpdesk.doctype.hd_settings.helpers import set_customer_home_page

# Where develop's install sent customers: the old Vue portal inside the desk app.
OLD_PORTAL_HOME = "/helpdesk"


def execute():
    """Customers now land on the Studio portal's knowledge base. The roles and the portal
    default still on the old portal move to it; values an admin changed stay."""
    frappe.db.set_single_value("HD Settings", "prefer_knowledge_base", 1)
    set_customer_home_page([OLD_PORTAL_HOME])
